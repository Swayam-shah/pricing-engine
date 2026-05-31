"""
Search API routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.search_agent import run_search

router = APIRouter()


class SearchRequest(BaseModel):
    query: str


@router.post("/search")
def search_products(request: SearchRequest):
    """
    Search for a product across all e-commerce platforms.
    Returns price comparison, market stats, and AI recommendations.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    result = run_search(request.query.strip())

    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/search/test")
def test_search():
    """Quick test endpoint"""
    return {"status": "search API working"}