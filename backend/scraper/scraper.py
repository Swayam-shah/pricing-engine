"""
Scraping Engine
--------------
1. Takes a competitor URL
2. Sends it to Firecrawl → gets clean markdown (no HTML mess)
3. Sends that markdown to Groq (fast + free) → extracts price, name, stock, rating
4. Validates with Pydantic
5. Saves to PostgreSQL
"""
import json
from datetime import datetime
from typing import Optional

from firecrawl import FirecrawlApp
from groq import Groq
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import settings
from db.models import CompetitorListing, Product, Competitor


# ── Pydantic schema for extracted product data ────────────────────────────────
class ExtractedProduct(BaseModel):
    product_name: str = Field(description="Name of the product on the page")
    price: Optional[float] = Field(None, description="Price in numeric form, no currency symbols")
    in_stock: bool = Field(True, description="Whether the product is in stock")
    rating: Optional[float] = Field(None, description="Product rating out of 5")
    review_count: Optional[int] = Field(None, description="Number of reviews")


# ── Initialize clients ────────────────────────────────────────────────────────
firecrawl = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
groq_client = Groq(api_key=settings.GROQ_API_KEY)


def scrape_url(url: str) -> Optional[str]:
    """
    Step 1: Use Firecrawl to convert a competitor product page
    into clean markdown text that an LLM can easily read.
    """
    try:
        print(f"🔍 Scraping: {url}")
        result = firecrawl.scrape_url(url)

        # handle both dict and object responses
        if isinstance(result, dict):
            markdown = result.get("markdown", "")
        else:
            markdown = getattr(result, "markdown", "") or str(result)

        if not markdown:
            print(f"⚠️  No content extracted from {url}")
            return None

        print(f"✅ Scraped {len(markdown)} characters")
        return markdown

    except Exception as e:
        print(f"❌ Firecrawl error for {url}: {e}")
        return None


def extract_product_data(markdown: str, url: str) -> Optional[ExtractedProduct]:
    """
    Step 2: Send the scraped markdown to Groq (Llama 3.3 70B).
    Groq is fast and free — perfect for this extraction task.
    The LLM reads the page text and pulls out the structured data we need.
    """
    prompt = f"""
You are a product data extraction assistant.
From the following webpage content, extract the product information.
Respond ONLY with a valid JSON object matching this exact structure:
{{
    "product_name": "exact product name",
    "price": 99.99,
    "in_stock": true,
    "rating": 4.5,
    "review_count": 1234
}}

Rules:
- price must be a number only (no $ or currency symbols)
- if price is not found, use null
- if rating is not found, use null
- if review_count is not found, use null
- in_stock should be true unless you see "out of stock" or "unavailable"
- respond with RAW JSON only, no markdown, no code fences

Webpage content:
{markdown[:4000]}
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300,
        )

        raw = response.choices[0].message.content.strip()

        # strip markdown code fences if present
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)
        extracted = ExtractedProduct(**data)
        print(f"✅ Extracted: {extracted.product_name} @ ${extracted.price}")
        return extracted

    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return None


def save_listing(
    db: Session,
    product_id: int,
    competitor_id: int,
    url: str,
    extracted: ExtractedProduct,
    raw_text: str
) -> CompetitorListing:
    """
    Step 3: Save the extracted data to PostgreSQL as a new CompetitorListing row.
    Each scrape creates a new row — this builds your price history over time.
    """
    listing = CompetitorListing(
        product_id=product_id,
        competitor_id=competitor_id,
        competitor_url=url,
        competitor_price=extracted.price,
        product_name_on_site=extracted.product_name,
        in_stock=extracted.in_stock,
        rating=extracted.rating,
        review_count=extracted.review_count,
        raw_scraped_text=raw_text[:5000],
        scraped_at=datetime.utcnow()
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    print(f"💾 Saved listing ID {listing.id} to database")
    return listing


def scrape_competitor_product(
    db: Session,
    product_id: int,
    competitor_id: int,
    url: str
) -> Optional[CompetitorListing]:
    """
    Main function: orchestrates the full scrape → extract → save pipeline.
    Call this for each competitor URL you want to monitor.
    """
    # Step 1: scrape
    markdown = scrape_url(url)
    if not markdown:
        return None

    # Step 2: extract
    extracted = extract_product_data(markdown, url)
    if not extracted:
        return None

    # Step 3: save
    listing = save_listing(db, product_id, competitor_id, url, extracted, markdown)
    return listing


def run_all_scrapes(db: Session):
    """
    Runs scraping for all configured competitor URLs.
    Called by the scheduler every N hours.
    Add your competitor URLs here.
    """
    # ── Configure your scraping targets here ─────────────────────────────
    # Format: (product_sku, competitor_name, url_to_scrape)
    scrape_targets = [
        # Example — replace with real URLs you want to track
        # ("WNC-001", "Amazon", "https://www.amazon.com/dp/B08HMWZBZX"),
        # ("WNC-001", "Flipkart", "https://www.flipkart.com/..."),
    ]

    if not scrape_targets:
        print("⚠️  No scrape targets configured in scraper.py → run_all_scrapes()")
        print("    Add URLs to the scrape_targets list to start tracking competitors.")
        return

    results = []
    for sku, competitor_name, url in scrape_targets:
        product = db.query(Product).filter(Product.sku == sku).first()
        competitor = db.query(Competitor).filter(Competitor.name == competitor_name).first()

        if not product:
            print(f"❌ Product with SKU {sku} not found in DB")
            continue
        if not competitor:
            print(f"❌ Competitor {competitor_name} not found in DB")
            continue

        listing = scrape_competitor_product(db, product.id, competitor.id, url)
        if listing:
            results.append(listing)

    print(f"\n✅ Scraping complete. {len(results)} listings saved.")
    return results