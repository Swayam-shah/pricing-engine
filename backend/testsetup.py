"""
Run this to verify your entire Day 1 setup works.
Command: python test_setup.py
"""
import sys

def test_env():
    print("1️⃣  Testing environment variables...")
    from config import settings
    assert settings.GEMINI_API_KEY, "GEMINI_API_KEY missing"
    assert settings.GROQ_API_KEY, "GROQ_API_KEY missing"
    assert settings.FIRECRAWL_API_KEY, "FIRECRAWL_API_KEY missing"
    assert settings.DATABASE_URL, "DATABASE_URL missing"
    print("   ✅ All environment variables loaded\n")

def test_database():
    print("2️⃣  Testing database connection...")
    from db.database import init_db, SessionLocal
    from db.models import Product
    init_db()
    db = SessionLocal()
    count = db.query(Product).count()
    db.close()
    print(f"   ✅ Database connected. Products in DB: {count}\n")

def test_groq():
    print("3️⃣  Testing Groq API...")
    from config import settings
    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Say 'Groq working' only."}],
        max_tokens=10,
    )
    reply = response.choices[0].message.content
    print(f"   ✅ Groq response: {reply}\n")

def test_gemini():
    print("4️⃣  Testing Gemini API...")
    from config import settings
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content("Say 'Gemini working' only.")
    print(f"   ✅ Gemini response: {response.text.strip()}\n")
def test_firecrawl():
    print("5️⃣  Testing Firecrawl API...")
    from config import settings
    from firecrawl import FirecrawlApp
    app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
    result = app.scrape_url("https://example.com")
    assert result, "No result returned"
    print(f"   ✅ Firecrawl working\n")

if __name__ == "__main__":
    tests = [test_env, test_database, test_groq, test_gemini, test_firecrawl]
    failed = []

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"   ❌ FAILED: {e}\n")
            failed.append(test.__name__)

    if failed:
        print(f"❌ {len(failed)} test(s) failed: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("🎉 All tests passed! Day 1 setup complete.")
        print("   Next step: run 'python -m db.seed' to populate sample data.")