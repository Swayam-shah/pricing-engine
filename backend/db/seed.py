"""
Run this once to populate the database with sample data.
Command: python -m db.seed
"""
from datetime import datetime, timedelta
import random
from db.database import SessionLocal, init_db
from db.models import Product, Competitor, SalesHistory


def seed():
    init_db()
    db = SessionLocal()

    try:
        # ── Sample products (YOUR products) ──────────────────────────────
        products = [
            Product(
                name="Wireless Noise Cancelling Headphones",
                sku="WNC-001",
                our_price=89.99,
                cost_price=35.00,
                category="Electronics"
            ),
            Product(
                name="Ergonomic Office Chair",
                sku="EOC-002",
                our_price=249.99,
                cost_price=110.00,
                category="Furniture"
            ),
            Product(
                name="Stainless Steel Water Bottle 1L",
                sku="SWB-003",
                our_price=34.99,
                cost_price=12.00,
                category="Sports"
            ),
        ]

        for p in products:
            existing = db.query(Product).filter(Product.sku == p.sku).first()
            if not existing:
                db.add(p)

        db.commit()
        print("✅ Products seeded")

        # ── Sample competitors ────────────────────────────────────────────
        competitors = [
            Competitor(name="Amazon", website_url="https://amazon.com"),
            Competitor(name="Flipkart", website_url="https://flipkart.com"),
        ]

        for c in competitors:
            existing = db.query(Competitor).filter(Competitor.name == c.name).first()
            if not existing:
                db.add(c)

        db.commit()
        print("✅ Competitors seeded")

        # ── Sample sales history (last 30 days) ───────────────────────────
        products_in_db = db.query(Product).all()

        for product in products_in_db:
            existing_sales = db.query(SalesHistory).filter(
                SalesHistory.product_id == product.id
            ).count()

            if existing_sales == 0:
                for day_offset in range(30):
                    date = datetime.utcnow() - timedelta(days=day_offset)

                    # simulate realistic sales — higher sales at lower prices
                    price_variation = random.uniform(0.9, 1.1)
                    price = round(product.our_price * price_variation, 2)
                    units = random.randint(2, 20)

                    db.add(SalesHistory(
                        product_id=product.id,
                        date=date,
                        units_sold=units,
                        price_at_time=price,
                        revenue=round(price * units, 2)
                    ))

        db.commit()
        print("✅ Sales history seeded (30 days)")
        print("\n🎉 Database ready. You can now run the scraper.")

    except Exception as e:
        print(f"❌ Seed failed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed()