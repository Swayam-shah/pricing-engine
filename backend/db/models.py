from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Product(Base):
    """
    Represents a product we are tracking.
    This is YOUR product, not the competitor's.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), unique=True, nullable=False)
    our_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    competitor_listings = relationship("CompetitorListing", back_populates="product")
    price_recommendations = relationship("PriceRecommendation", back_populates="product")
    sales_history = relationship("SalesHistory", back_populates="product")


class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    website_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    listings = relationship("CompetitorListing", back_populates="competitor")


class CompetitorListing(Base):
    """
    A scraped price snapshot of a competitor's product.
    Every scrape adds a new row — builds price history over time.
    """
    __tablename__ = "competitor_listings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False)
    competitor_url = Column(String(500), nullable=False)
    competitor_price = Column(Float, nullable=True)
    product_name_on_site = Column(String(255), nullable=True)
    in_stock = Column(Boolean, default=True)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    raw_scraped_text = Column(Text, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="competitor_listings")
    competitor = relationship("Competitor", back_populates="listings")


class SalesHistory(Base):
    __tablename__ = "sales_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    units_sold = Column(Integer, nullable=False)
    price_at_time = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)

    product = relationship("Product", back_populates="sales_history")


class PriceRecommendation(Base):
    __tablename__ = "price_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    current_price = Column(Float, nullable=False)
    recommended_price = Column(Float, nullable=False)
    min_competitor_price = Column(Float, nullable=True)
    max_competitor_price = Column(Float, nullable=True)
    avg_competitor_price = Column(Float, nullable=True)
    expected_margin = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="price_recommendations")