"""
Search Agent
------------
1. Takes a product search query (e.g. "white adidas shoes")
2. Searches Google Shopping via SerpAPI
3. Extracts prices, ratings, platforms
4. Uses Groq to analyze and recommend:
   - Best seller price (for sellers)
   - Best buy deal (for buyers)
"""
import json
from typing import Optional
from groq import Groq
import httpx

from config import settings

groq_client = Groq(api_key=settings.GROQ_API_KEY)


def search_google_shopping(query: str, country: str = "in") -> list:
    """
    Search Google Shopping via SerpAPI.
    Returns list of product listings with prices and ratings.
    """
    print(f"🔍 Searching Google Shopping for: {query}")

    url = "https://serpapi.com/search"
    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": settings.SERPAPI_KEY,
        "gl": country,
        "hl": "en",
        "num": 20,
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, params=params)
            data = response.json()

        results = data.get("shopping_results", [])
        if not results:
            print("⚠️ No shopping results found")
            return []

        listings = []
        for item in results:
            price_str = item.get("price", "")
            price = _parse_price(price_str)

            listing = {
                "title": item.get("title", "Unknown"),
                "price": price,
                "price_str": price_str,
                "source": item.get("source", "Unknown"),
                "rating": item.get("rating"),
                "reviews": item.get("reviews"),
                "link": item.get("link", ""),
                "thumbnail": item.get("thumbnail", ""),
                "delivery": item.get("delivery", ""),
            }
            if price:
                listings.append(listing)

        print(f"✅ Found {len(listings)} listings with prices")
        return listings

    except Exception as e:
        print(f"❌ SerpAPI error: {e}")
        return []


def _parse_price(price_str: str) -> Optional[float]:
    """Extract numeric price from string like '₹2,999' or '$29.99'"""
    if not price_str:
        return None
    try:
        cleaned = ""
        for char in price_str:
            if char.isdigit() or char == ".":
                cleaned += char
            elif char == "," :
                continue
        return float(cleaned) if cleaned else None
    except Exception:
        return None


def calculate_market_stats(listings: list) -> dict:
    """Calculate min, max, average prices and find best deals."""
    prices = [l["price"] for l in listings if l["price"]]
    if not prices:
        return {}

    # price stats
    min_price = min(prices)
    max_price = max(prices)
    avg_price = round(sum(prices) / len(prices), 2)

    # find listing with lowest price
    cheapest = min(listings, key=lambda x: x["price"] or float("inf"))

    # find listing with best combined score (price + rating)
    def combined_score(listing):
        price = listing.get("price") or avg_price
        rating = listing.get("rating") or 3.0
        reviews = listing.get("reviews") or 0

        # normalize price (lower is better) — invert so higher score = better
        price_score = 1 - ((price - min_price) / (max_price - min_price + 1))

        # normalize rating (higher is better)
        rating_score = rating / 5.0

        # weight: 50% price, 40% rating, 10% review count
        review_score = min(reviews / 1000, 1.0) if reviews else 0
        return (price_score * 0.5) + (rating_score * 0.4) + (review_score * 0.1)

    best_deal = max(listings, key=combined_score)

    return {
        "min_price": min_price,
        "max_price": max_price,
        "avg_price": avg_price,
        "total_listings": len(listings),
        "cheapest": cheapest,
        "best_deal": best_deal,
    }


def get_ai_insights(query: str, stats: dict, listings: list) -> dict:
    """
    Ask Groq to analyze the market data and provide:
    - Recommended seller price
    - Best buyer advice
    - Market insights
    """
    # prepare top 10 listings for context
    top_listings = sorted(
        [l for l in listings if l["price"]],
        key=lambda x: x["price"]
    )[:10]

    listings_text = "\n".join([
        f"- {l['title'][:50]} | {l['source']} | ₹{l['price']} | Rating: {l.get('rating', 'N/A')} | Reviews: {l.get('reviews', 'N/A')}"
        for l in top_listings
    ])

    prompt = f"""
You are an e-commerce pricing expert analyzing market data for: "{query}"

Market Data:
- Total listings found: {stats['total_listings']}
- Lowest price: ₹{stats['min_price']}
- Highest price: ₹{stats['max_price']}
- Average price: ₹{stats['avg_price']}

Top listings by price:
{listings_text}

Provide analysis in this exact JSON format (no markdown, no code fences):
{{
    "seller_recommended_price": 2999,
    "seller_reasoning": "2-3 sentences on why this price maximizes profit for a seller entering this market",
    "buyer_best_pick": "Platform/seller name",
    "buyer_reasoning": "2-3 sentences on why this is the best buy considering price and quality",
    "market_insight": "1-2 sentences about the overall market — is it competitive, premium, commoditized?",
    "price_trend": "stable/competitive/premium",
    "competition_level": "low/medium/high"
}}
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an e-commerce pricing expert. Always respond with valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
        )

        raw = response.choices[0].message.content.strip()

        # clean JSON
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            raw = raw[start:end]

        return json.loads(raw)

    except Exception as e:
        print(f"❌ AI insights error: {e}")
        return {
            "seller_recommended_price": stats["avg_price"],
            "seller_reasoning": "Price at market average to remain competitive.",
            "buyer_best_pick": stats["cheapest"]["source"],
            "buyer_reasoning": "Lowest price available in the market.",
            "market_insight": "Market analysis unavailable.",
            "price_trend": "stable",
            "competition_level": "medium"
        }


def run_search(query: str) -> dict:
    """
    Main function — runs the full search pipeline.
    Returns complete market analysis for a product query.
    """
    print(f"\n{'='*50}")
    print(f"🚀 Running search for: {query}")
    print(f"{'='*50}")

    # Step 1: search Google Shopping
    listings = search_google_shopping(query)
    if not listings:
        return {"error": "No results found. Try a different search term."}

    # Step 2: calculate market stats
    stats = calculate_market_stats(listings)
    if not stats:
        return {"error": "Could not calculate market statistics."}

    # Step 3: get AI insights
    insights = get_ai_insights(query, stats, listings)

    print(f"✅ Search complete")
    print(f"   Min: ₹{stats['min_price']} | Max: ₹{stats['max_price']} | Avg: ₹{stats['avg_price']}")

    return {
        "query": query,
        "stats": stats,
        "insights": insights,
        "listings": listings[:20],
    }