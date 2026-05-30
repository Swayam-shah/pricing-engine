"""
All FastAPI route handlers.
Every endpoint the Next.js frontend will call.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from db.database import get_db
from db.models import (
    Product, Competitor, CompetitorListing,
    PriceRecommendation, SalesHistory
)
from api.schemas import (
    ProductResponse, CompetitorResponse, CompetitorListingResponse,
    RecommendationResponse, RecommendationApprove, ScrapeRequest,
    DashboardStats, PriceHistoryResponse, PriceHistoryPoint
)
from agents.graph import run_pricing_agent
from scraper.scraper import scrape_competitor_product

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    """Get all products."""
    return db.query(Product).all()


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/products/{product_id}/price-history", response_model=PriceHistoryResponse)
def get_price_history(product_id: int, days: int = 30, db: Session = Depends(get_db)):
    """
    Get price history for charts — combines our sales prices
    with competitor prices over time.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    since = datetime.utcnow() - timedelta(days=days)

    # our historical prices from sales
    sales = (
        db.query(SalesHistory)
        .filter(SalesHistory.product_id == product_id, SalesHistory.date >= since)
        .order_by(SalesHistory.date)
        .all()
    )

    # competitor prices grouped by day
    listings = (
        db.query(
            func.date(CompetitorListing.scraped_at).label("day"),
            func.avg(CompetitorListing.competitor_price).label("avg_price")
        )
        .filter(
            CompetitorListing.product_id == product_id,
            CompetitorListing.scraped_at >= since,
            CompetitorListing.competitor_price.isnot(None)
        )
        .group_by(func.date(CompetitorListing.scraped_at))
        .all()
    )

    comp_by_day = {str(r.day): round(r.avg_price, 2) for r in listings}

    # recommendations by day
    recs = (
        db.query(PriceRecommendation)
        .filter(
            PriceRecommendation.product_id == product_id,
            PriceRecommendation.created_at >= since
        )
        .order_by(PriceRecommendation.created_at)
        .all()
    )
    rec_by_day = {str(r.created_at.date()): r.recommended_price for r in recs}

    # build chart data points
    history = []
    for sale in sales:
        day_str = str(sale.date.date())
        history.append(PriceHistoryPoint(
            date=day_str,
            our_price=sale.price_at_time,
            competitor_avg=comp_by_day.get(day_str),
            recommended_price=rec_by_day.get(day_str)
        ))

    # if no sales history, build from current price
    if not history:
        for i in range(days):
            day = datetime.utcnow() - timedelta(days=days - i)
            day_str = str(day.date())
            history.append(PriceHistoryPoint(
                date=day_str,
                our_price=product.our_price,
                competitor_avg=comp_by_day.get(day_str),
                recommended_price=rec_by_day.get(day_str)
            ))

    return PriceHistoryResponse(
        product_id=product_id,
        product_name=product.name,
        history=history
    )


# ─────────────────────────────────────────────────────────────────────────────
# COMPETITORS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/competitors", response_model=List[CompetitorResponse])
def get_competitors(db: Session = Depends(get_db)):
    """Get all competitors."""
    return db.query(Competitor).all()


@router.get("/competitors/{product_id}/listings", response_model=List[CompetitorListingResponse])
def get_listings(product_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """Get latest scraped listings for a product."""
    return (
        db.query(CompetitorListing)
        .filter(CompetitorListing.product_id == product_id)
        .order_by(CompetitorListing.scraped_at.desc())
        .limit(limit)
        .all()
    )


# ─────────────────────────────────────────────────────────────────────────────
# SCRAPING
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/scrape/{product_id}")
def trigger_scrape(
    product_id: int,
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger a scrape for a product URL.
    Runs in background so the API responds immediately.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    competitor = db.query(Competitor).filter(
        Competitor.id == request.competitor_id
    ).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    def run_scrape():
        from db.database import SessionLocal
        scrape_db = SessionLocal()
        try:
            scrape_competitor_product(
                scrape_db, product_id, request.competitor_id, request.url
            )
        finally:
            scrape_db.close()

    background_tasks.add_task(run_scrape)

    return {
        "message": f"Scraping started for product {product_id}",
        "url": request.url,
        "status": "running"
    }


# ─────────────────────────────────────────────────────────────────────────────
# PRICING AGENT
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/analyze/{product_id}", response_model=RecommendationResponse)
def analyze_product(
    product_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Run the full LangGraph pricing agent for a product.
    Returns the new recommendation immediately.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = run_pricing_agent(product_id=product_id, db=db)

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    rec = db.query(PriceRecommendation).filter(
        PriceRecommendation.id == result["recommendation_id"]
    ).first()

    # attach product name for response
    rec_dict = {
        **rec.__dict__,
        "product_name": product.name
    }

    return RecommendationResponse(**{
        k: v for k, v in rec_dict.items() if not k.startswith("_")
    })


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/recommendations", response_model=List[RecommendationResponse])
def get_recommendations(
    status: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get all recommendations. Filter by status: pending / approved / rejected.
    """
    query = db.query(PriceRecommendation)
    if status:
        query = query.filter(PriceRecommendation.status == status)

    recs = query.order_by(PriceRecommendation.created_at.desc()).limit(limit).all()

    result = []
    for rec in recs:
        product = db.query(Product).filter(Product.id == rec.product_id).first()
        rec_data = {
            c.name: getattr(rec, c.name)
            for c in rec.__table__.columns
        }
        rec_data["product_name"] = product.name if product else None
        result.append(RecommendationResponse(**rec_data))

    return result


@router.patch("/recommendations/{rec_id}/approve")
def approve_recommendation(
    rec_id: int,
    body: RecommendationApprove,
    db: Session = Depends(get_db)
):
    """
    Approve or reject a price recommendation.
    In a real system, 'approved' would push the price live.
    """
    rec = db.query(PriceRecommendation).filter(
        PriceRecommendation.id == rec_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    if body.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")

    rec.status = body.status
    if body.status == "approved":
        rec.approved_at = datetime.utcnow()

        # update the product's actual price
        product = db.query(Product).filter(Product.id == rec.product_id).first()
        if product:
            old_price = product.our_price
            product.our_price = rec.recommended_price
            product.updated_at = datetime.utcnow()
            db.commit()
            return {
                "message": f"Price approved and updated",
                "product": product.name,
                "old_price": old_price,
                "new_price": rec.recommended_price,
                "status": "approved"
            }

    db.commit()
    return {
        "message": f"Recommendation {body.status}",
        "recommendation_id": rec_id,
        "status": body.status
    }


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD STATS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Summary numbers for the dashboard header cards."""
    today = datetime.utcnow().date()

    total_products = db.query(Product).count()

    pending = db.query(PriceRecommendation).filter(
        PriceRecommendation.status == "pending"
    ).count()

    approved_today = db.query(PriceRecommendation).filter(
        PriceRecommendation.status == "approved",
        func.date(PriceRecommendation.approved_at) == today
    ).count()

    # average margin across all products
    products = db.query(Product).all()
    if products:
        margins = [
            ((p.our_price - p.cost_price) / p.our_price) * 100
            for p in products
        ]
        avg_margin = round(sum(margins) / len(margins), 2)
    else:
        avg_margin = 0.0

    total_competitors = db.query(Competitor).count()

    last_listing = (
        db.query(CompetitorListing)
        .order_by(CompetitorListing.scraped_at.desc())
        .first()
    )

    return DashboardStats(
        total_products=total_products,
        pending_recommendations=pending,
        approved_today=approved_today,
        avg_margin=avg_margin,
        total_competitors=total_competitors,
        last_scrape=last_listing.scraped_at if last_listing else None
    )