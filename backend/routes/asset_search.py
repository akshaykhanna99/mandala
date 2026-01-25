"""FastAPI routes for asset search."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..asset_search import search_asset, AssetInfo


router = APIRouter(prefix="/asset-search", tags=["asset-search"])


class AssetSearchRequest(BaseModel):
    """Asset search request."""
    query: str


class AssetSearchResponse(BaseModel):
    """Asset search response."""
    name: str
    ticker: Optional[str]
    isin: Optional[str]
    country: Optional[str]
    region: Optional[str]
    sub_region: Optional[str]
    sector: Optional[str]
    asset_class: Optional[str]
    description: Optional[str]
    confidence: float


@router.post("/search")
def search_for_asset(request: AssetSearchRequest) -> AssetSearchResponse:
    """
    Search for an asset using web search + Claude Haiku extraction.

    Args:
        request: AssetSearchRequest with query string

    Returns:
        AssetSearchResponse with extracted asset information
    """
    if not request.query or len(request.query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    # Search for asset
    asset_info = search_asset(request.query.strip())

    if not asset_info:
        raise HTTPException(status_code=404, detail="Asset not found")

    return AssetSearchResponse(
        name=asset_info.name,
        ticker=asset_info.ticker,
        isin=asset_info.isin,
        country=asset_info.country,
        region=asset_info.region,
        sub_region=asset_info.sub_region,
        sector=asset_info.sector,
        asset_class=asset_info.asset_class,
        description=asset_info.description,
        confidence=asset_info.confidence,
    )
