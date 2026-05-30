"""
Test the full LangGraph pricing agent end to end.
Command: python test_agent.py
"""
from db.database import SessionLocal
from agents.graph import run_pricing_agent

def main():
    db = SessionLocal()
    try:
        # test with product_id=1 (Wireless Headphones from seed data)
        print("Testing agent with product_id=1 (Wireless Headphones)...")
        result = run_pricing_agent(product_id=1, db=db)

        if result.get("error"):
            print(f"\n❌ Test failed: {result['error']}")
        else:
            print(f"\n✅ Test passed!")
            print(f"   Recommendation ID in DB: {result['recommendation_id']}")

        # test with product_id=2 (Office Chair)
        print("\nTesting agent with product_id=2 (Office Chair)...")
        result2 = run_pricing_agent(product_id=2, db=db)

        if not result2.get("error"):
            print(f"✅ Test 2 passed!")

    finally:
        db.close()

if __name__ == "__main__":
    main()