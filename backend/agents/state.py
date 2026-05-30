"""
Shared state object that flows through every node in the LangGraph.
Think of it as a baton passed between runners in a relay race —
each node reads from it and adds its own results to it.
"""
from typing import Optional, List, TypedDict


class PricingState(TypedDict):
    # ── Input ─────────────────────────────────────────────────────────────
    product_id: int                        # which product to analyze

    # ── Populated by fetch_data node ──────────────────────────────────────
    product_name: Optional[str]
    our_price: Optional[float]
    cost_price: Optional[float]
    competitor_prices: Optional[List[float]]    # list of scraped competitor prices
    avg_units_sold: Optional[float]             # average daily units sold
    avg_revenue: Optional[float]                # average daily revenue

    # ── Populated by run_analysis node ────────────────────────────────────
    min_competitor_price: Optional[float]
    max_competitor_price: Optional[float]
    avg_competitor_price: Optional[float]
    current_margin_pct: Optional[float]         # current profit margin %
    price_vs_competitor: Optional[str]          # "above", "below", or "equal"
    analysis_summary: Optional[str]             # human-readable analysis text

    # ── Populated by generate_price node ──────────────────────────────────
    recommended_price: Optional[float]
    expected_margin: Optional[float]
    confidence_score: Optional[float]           # 0.0 to 1.0
    reasoning: Optional[str]                    # AI's full explanation

    # ── Populated by save_result node ─────────────────────────────────────
    recommendation_id: Optional[int]            # DB row ID of saved recommendation
    error: Optional[str]                        # any error message