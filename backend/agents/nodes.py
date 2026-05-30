"""
The 4 nodes of the LangGraph pricing agent.
Uses Groq (Llama 3.3 70B) for price recommendation — fast and free.
Gemini kept as fallback.
"""
import json
import pandas as pd
from groq import Groq
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from config import settings
from db.models import Product, CompetitorListing, SalesHistory, PriceRecommendation
from agents.state import PricingState

# ── Initialize Groq client ────────────────────────────────────────────────────
groq_client = Groq(api_key=settings.GROQ_API_KEY)


def fetch_data(state: PricingState, db: Session) -> PricingState:
    print(f"\n📦 [Node 1] Fetching data for product_id={state['product_id']}")
    try:
        product_id = state["product_id"]
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {**state, "error": f"Product {product_id} not found"}

        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        listings = (
            db.query(CompetitorListing)
            .filter(
                CompetitorListing.product_id == product_id,
                CompetitorListing.scraped_at >= seven_days_ago,
                CompetitorListing.competitor_price.isnot(None)
            ).all()
        )
        competitor_prices = [l.competitor_price for l in listings]

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sales = (
            db.query(SalesHistory)
            .filter(
                SalesHistory.product_id == product_id,
                SalesHistory.date >= thirty_days_ago
            ).all()
        )

        if sales:
            df = pd.DataFrame([{
                "units_sold": s.units_sold,
                "revenue": s.revenue,
                "price": s.price_at_time
            } for s in sales])
            avg_units = round(df["units_sold"].mean(), 2)
            avg_revenue = round(df["revenue"].mean(), 2)
        else:
            avg_units = 0.0
            avg_revenue = 0.0

        print(f"   ✅ Product: {product.name} @ ${product.our_price}")
        print(f"   ✅ Competitor prices found: {len(competitor_prices)}")
        print(f"   ✅ Sales records found: {len(sales)}")

        return {
            **state,
            "product_name": product.name,
            "our_price": product.our_price,
            "cost_price": product.cost_price,
            "competitor_prices": competitor_prices,
            "avg_units_sold": avg_units,
            "avg_revenue": avg_revenue,
        }
    except Exception as e:
        print(f"   ❌ fetch_data error: {e}")
        return {**state, "error": str(e)}


def run_analysis(state: PricingState, db: Session) -> PricingState:
    print(f"\n📊 [Node 2] Running analysis...")
    try:
        our_price = state["our_price"]
        cost_price = state["cost_price"]
        competitor_prices = state.get("competitor_prices", [])

        current_margin = round(((our_price - cost_price) / our_price) * 100, 2)

        if competitor_prices:
            df = pd.Series(competitor_prices)
            min_price = round(df.min(), 2)
            max_price = round(df.max(), 2)
            avg_price = round(df.mean(), 2)
            median_price = round(df.median(), 2)
        else:
            min_price = round(our_price * 0.85, 2)
            max_price = round(our_price * 1.15, 2)
            avg_price = round(our_price * 0.95, 2)
            median_price = round(our_price * 0.96, 2)
            print("   ⚠️  No competitor prices in DB — using estimated values for demo")

        if our_price > avg_price * 1.05:
            position = "above"
        elif our_price < avg_price * 0.95:
            position = "below"
        else:
            position = "equal"

        avg_units = state.get("avg_units_sold", 0)
        if avg_units > 15:
            demand = "high"
        elif avg_units > 8:
            demand = "moderate"
        else:
            demand = "low"

        summary = f"""
Product: {state['product_name']}
Our Current Price: ${our_price}
Our Cost Price: ${cost_price}
Current Profit Margin: {current_margin}%
Minimum Allowed Price (15% margin floor): ${round(cost_price * 1.15, 2)}

Competitor Market Data:
- Lowest competitor price: ${min_price}
- Highest competitor price: ${max_price}
- Average competitor price: ${avg_price}
- Median competitor price: ${median_price}
- Our position vs market: {position} average

Sales Performance (last 30 days):
- Avg daily units sold: {avg_units}
- Avg daily revenue: ${state.get('avg_revenue', 0)}
- Demand level: {demand}
        """.strip()

        print(f"   ✅ Margin: {current_margin}% | Position: {position} competitors | Demand: {demand}")

        return {
            **state,
            "min_competitor_price": min_price,
            "max_competitor_price": max_price,
            "avg_competitor_price": avg_price,
            "current_margin_pct": current_margin,
            "price_vs_competitor": position,
            "analysis_summary": summary,
        }
    except Exception as e:
        print(f"   ❌ run_analysis error: {e}")
        return {**state, "error": str(e)}


def generate_price(state: PricingState, db: Session) -> PricingState:
    print(f"\n🤖 [Node 3] Generating price recommendation via Groq...")

    prompt = f"""
You are an expert e-commerce pricing strategist.
Analyze this product data and recommend an optimal selling price.

{state['analysis_summary']}

Your objectives:
1. Maximize revenue without losing customers to competitors
2. Never price below the minimum allowed price (cost + 15% margin)
3. Stay competitive — within 20% of competitor average unless strongly justified
4. Consider demand level when pricing (high demand = can price higher)

Respond ONLY with this exact JSON object. No explanation, no markdown, no code fences:
{{"recommended_price": 84.99, "expected_margin": 42.5, "confidence_score": 0.85, "reasoning": "2-3 sentence explanation of why this price was chosen"}}
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a pricing strategist. Always respond with valid JSON only. No markdown, no explanation outside the JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()
        raw = _clean_json(raw)
        data = json.loads(raw)
        _validate_recommendation(data, state)

        print(f"   ✅ [Groq] Recommended: ${data['recommended_price']} | Margin: {data['expected_margin']}% | Confidence: {data['confidence_score']}")

        return {
            **state,
            "recommended_price": float(data["recommended_price"]),
            "expected_margin": float(data["expected_margin"]),
            "confidence_score": float(data["confidence_score"]),
            "reasoning": data["reasoning"],
        }
    except Exception as groq_error:
        print(f"   ⚠️  Groq failed: {groq_error}")

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        for model_name in ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-pro"]:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                raw = response.text.strip()
                raw = _clean_json(raw)
                data = json.loads(raw)
                _validate_recommendation(data, state)
                print(f"   ✅ [Gemini/{model_name}] Recommended: ${data['recommended_price']}")
                return {
                    **state,
                    "recommended_price": float(data["recommended_price"]),
                    "expected_margin": float(data["expected_margin"]),
                    "confidence_score": float(data["confidence_score"]),
                    "reasoning": data["reasoning"],
                }
            except Exception:
                continue
    except Exception as gemini_error:
        print(f"   ⚠️  Gemini fallback also failed: {gemini_error}")

    print(f"   🔧 Using rule-based fallback pricing...")
    return _rule_based_price(state)


def _clean_json(raw: str) -> str:
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                return part
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        return raw[start:end]
    return raw


def _validate_recommendation(data: dict, state: PricingState):
    min_price = round(state["cost_price"] * 1.15, 2)
    if data["recommended_price"] < min_price:
        data["recommended_price"] = min_price
        data["expected_margin"] = 15.0
        data["reasoning"] += f" (Price adjusted to maintain minimum 15% margin floor of ${min_price}.)"


def _rule_based_price(state: PricingState) -> PricingState:
    cost = state["cost_price"]
    avg_comp = state.get("avg_competitor_price") or state["our_price"]
    min_price = round(cost * 1.15, 2)
    target = round(avg_comp * 0.95, 2)
    recommended = max(target, min_price)
    margin = round(((recommended - cost) / recommended) * 100, 2)
    return {
        **state,
        "recommended_price": recommended,
        "expected_margin": margin,
        "confidence_score": 0.6,
        "reasoning": f"Rule-based: priced 5% below competitor average (${avg_comp}) while maintaining {margin}% margin above cost floor."
    }


def save_result(state: PricingState, db: Session) -> PricingState:
    print(f"\n💾 [Node 4] Saving recommendation to database...")
    try:
        # supersede any existing pending recommendation for this product
        existing = db.query(PriceRecommendation).filter(
            PriceRecommendation.product_id == state["product_id"],
            PriceRecommendation.status == "pending"
        ).first()

        if existing:
            existing.status = "superseded"
            db.commit()
            print(f"   ↩️  Superseded old recommendation ID: {existing.id}")

        rec = PriceRecommendation(
            product_id=state["product_id"],
            current_price=state["our_price"],
            recommended_price=state["recommended_price"],
            min_competitor_price=state.get("min_competitor_price"),
            max_competitor_price=state.get("max_competitor_price"),
            avg_competitor_price=state.get("avg_competitor_price"),
            expected_margin=state.get("expected_margin"),
            confidence_score=state.get("confidence_score"),
            reasoning=state.get("reasoning"),
            status="pending",
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

        print(f"   ✅ Saved recommendation ID: {rec.id} | Status: pending")
        print(f"   📋 Awaiting approval in dashboard")
        return {**state, "recommendation_id": rec.id}

    except Exception as e:
        print(f"   ❌ save_result error: {e}")
        return {**state, "error": str(e)}