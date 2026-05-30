"""
Pydantic schemas for API request/response validation.
These define exactly what the frontend receives — clean, typed JSON.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Product Schemas ───────────────────────────────────────────────────────────
class ProductBase(BaseModel):
    name: str
    sku: str
    our_price: float
    cost_price: float
    category: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Competitor Schemas ────────────────────────────────────────────────────────
class CompetitorResponse(BaseModel):
    id: int
    name: str
    website_url: str

    class Config:
        from_attributes = True


# ── Competitor Listing Schemas ────────────────────────────────────────────────
class CompetitorListingResponse(BaseModel):
    id: int
    product_id: int
    competitor_id: int
    competitor_url: str
    competitor_price: Optional[float] = None
    product_name_on_site: Optional[str] = None
    in_stock: bool
    rating: Optional[float] = None
    review_count: Optional[int] = None
    sentiment_score: Optional[float] = None
    scraped_at: datetime

    class Config:
        from_attributes = True


# ── Price Recommendation Schemas ──────────────────────────────────────────────
class RecommendationResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    current_price: float
    recommended_price: float
    min_competitor_price: Optional[float] = None
    max_competitor_price: Optional[float] = None
    avg_competitor_price: Optional[float] = None
    expected_margin: Optional[float] = None
    confidence_score: Optional[float] = None
    reasoning: Optional[str] = None
    status: str
    approved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationApprove(BaseModel):
    status: str  # "approved" or "rejected"


# ── Scrape Request Schema ─────────────────────────────────────────────────────
class ScrapeRequest(BaseModel):
    url: str
    competitor_id: int


# ── Dashboard Stats Schema ────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_products: int
    pending_recommendations: int
    approved_today: int
    avg_margin: float
    total_competitors: int
    last_scrape: Optional[datetime] = None


# ── Price History Schema (for charts) ────────────────────────────────────────
class PriceHistoryPoint(BaseModel):
    date: str
    our_price: float
    competitor_avg: Optional[float] = None
    recommended_price: Optional[float] = None


class PriceHistoryResponse(BaseModel):
    product_id: int
    product_name: str
    history: List[PriceHistoryPoint]