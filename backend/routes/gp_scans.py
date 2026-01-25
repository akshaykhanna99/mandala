"""API routes for GP scan management."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..db_models import AssetTable, GPScanTable
from ..schemas.gp_scans import (
    AssetCreate,
    AssetResponse,
    GPScanCreate,
    GPScanResponse,
)

router = APIRouter(prefix="/gp-scans", tags=["gp-scans"])


def _get_or_create_asset(
    db: Session,
    pipeline_result: dict,
    asset_id: Optional[int] = None
) -> AssetTable:
    """
    Get existing asset by ID, or create new asset from pipeline result.
    
    Args:
        db: Database session
        pipeline_result: Full pipeline result dict
        asset_id: Optional asset ID (if provided, fetch existing)
    
    Returns:
        AssetTable instance
    """
    # If asset_id provided, fetch existing asset
    if asset_id:
        asset = db.query(AssetTable).filter(AssetTable.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset with ID {asset_id} not found")
        return asset
    
    # Otherwise, create or find asset from pipeline result
    # Try to find by ticker or ISIN first
    ticker = pipeline_result.get("ticker")
    isin = pipeline_result.get("isin")
    name = pipeline_result.get("name")
    
    # If name not in pipeline_result, try to get from characterization
    if not name:
        # Try to extract from available fields
        char_summary = pipeline_result.get("characterization_summary", "")
        country = pipeline_result.get("asset_country", "Unknown")
        sector = pipeline_result.get("asset_sector", "Unknown")
        name = f"{sector} Asset - {country}"
    
    existing_asset = None
    if ticker:
        existing_asset = db.query(AssetTable).filter(AssetTable.ticker == ticker).first()
    if not existing_asset and isin:
        existing_asset = db.query(AssetTable).filter(AssetTable.isin == isin).first()
    if not existing_asset and name:
        existing_asset = db.query(AssetTable).filter(AssetTable.name == name).first()
    
    if existing_asset:
        return existing_asset
    
    # Create new asset from pipeline result
    exposures = pipeline_result.get("exposures", [])
    
    new_asset = AssetTable(
        name=name or "Unknown Asset",
        ticker=ticker,
        isin=isin,
        country=pipeline_result.get("asset_country"),
        region=pipeline_result.get("asset_region", "Unknown"),
        sub_region=pipeline_result.get("asset_sub_region"),
        asset_type=pipeline_result.get("asset_type", "Unknown"),
        asset_class=pipeline_result.get("asset_class", "Unknown"),
        sector=pipeline_result.get("asset_sector", "Unknown"),
        is_emerging_market="true" if pipeline_result.get("is_emerging_market") else "false",
        is_developed_market="true" if pipeline_result.get("is_developed_market") else "false",
        is_global_fund="true" if pipeline_result.get("is_global_fund") else "false",
        exposures=exposures,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)
    
    return new_asset


@router.post("", response_model=GPScanResponse, status_code=201)
def save_gp_scan(scan_data: GPScanCreate, db: Session = Depends(get_db)):
    """
    Save a GP risk scan result.
    
    If asset_id is not provided, creates a new asset from the pipeline result.
    """
    # Get or create asset
    asset = _get_or_create_asset(db, scan_data.pipeline_result, scan_data.asset_id)
    
    # Extract key metrics from pipeline result
    probabilities = scan_data.pipeline_result.get("probabilities", {})
    impact = scan_data.pipeline_result.get("impact", {})
    
    negative_prob = probabilities.get("negative") or probabilities.get("sell", 0.0)
    neutral_prob = probabilities.get("neutral") or probabilities.get("hold", 0.0)
    positive_prob = probabilities.get("positive") or probabilities.get("buy", 0.0)
    
    overall_direction = impact.get("overall_direction", "neutral")
    overall_magnitude = impact.get("overall_magnitude", 0.0)
    confidence = impact.get("confidence", 0.0)
    signal_count = scan_data.pipeline_result.get("signal_count", 0)
    top_themes = scan_data.pipeline_result.get("top_themes", [])[:5]  # Top 5
    
    # Create scan record
    scan = GPScanTable(
        asset_id=asset.id,
        risk_tolerance=scan_data.risk_tolerance,
        days_lookback=scan_data.days_lookback,
        scan_date=datetime.utcnow(),
        pipeline_result=scan_data.pipeline_result,
        negative_probability=negative_prob,
        neutral_probability=neutral_prob,
        positive_probability=positive_prob,
        overall_direction=overall_direction,
        overall_magnitude=overall_magnitude,
        confidence=confidence,
        signal_count=signal_count,
        top_themes=top_themes,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    return GPScanResponse(
        id=scan.id,
        asset_id=scan.asset_id,
        risk_tolerance=scan.risk_tolerance,
        days_lookback=scan.days_lookback,
        scan_date=scan.scan_date.isoformat() if scan.scan_date else "",
        negative_probability=scan.negative_probability,
        neutral_probability=scan.neutral_probability,
        positive_probability=scan.positive_probability,
        overall_direction=scan.overall_direction,
        overall_magnitude=scan.overall_magnitude,
        confidence=scan.confidence,
        signal_count=scan.signal_count,
        top_themes=scan.top_themes or [],
        created_at=scan.created_at.isoformat() if scan.created_at else "",
        updated_at=scan.updated_at.isoformat() if scan.updated_at else "",
    )


@router.get("", response_model=List[GPScanResponse])
def list_gp_scans(
    asset_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List GP scans, optionally filtered by asset_id."""
    query = db.query(GPScanTable)
    if asset_id:
        query = query.filter(GPScanTable.asset_id == asset_id)
    scans = query.order_by(GPScanTable.scan_date.desc()).limit(limit).all()
    
    return [
        GPScanResponse(
            id=scan.id,
            asset_id=scan.asset_id,
            risk_tolerance=scan.risk_tolerance,
            days_lookback=scan.days_lookback,
            scan_date=scan.scan_date.isoformat() if scan.scan_date else "",
            negative_probability=scan.negative_probability,
            neutral_probability=scan.neutral_probability,
            positive_probability=scan.positive_probability,
            overall_direction=scan.overall_direction,
            overall_magnitude=scan.overall_magnitude,
            confidence=scan.confidence,
            signal_count=scan.signal_count,
            top_themes=scan.top_themes or [],
            created_at=scan.created_at.isoformat() if scan.created_at else "",
            updated_at=scan.updated_at.isoformat() if scan.updated_at else "",
        )
        for scan in scans
    ]


@router.get("/{scan_id}", response_model=GPScanResponse)
def get_gp_scan(scan_id: int, db: Session = Depends(get_db)):
    """Get a specific GP scan by ID."""
    scan = db.query(GPScanTable).filter(GPScanTable.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail=f"GP scan {scan_id} not found")
    
    return GPScanResponse(
        id=scan.id,
        asset_id=scan.asset_id,
        risk_tolerance=scan.risk_tolerance,
        days_lookback=scan.days_lookback,
        scan_date=scan.scan_date.isoformat() if scan.scan_date else "",
        negative_probability=scan.negative_probability,
        neutral_probability=scan.neutral_probability,
        positive_probability=scan.positive_probability,
        overall_direction=scan.overall_direction,
        overall_magnitude=scan.overall_magnitude,
        confidence=scan.confidence,
        signal_count=scan.signal_count,
        top_themes=scan.top_themes or [],
        created_at=scan.created_at.isoformat() if scan.created_at else "",
        updated_at=scan.updated_at.isoformat() if scan.updated_at else "",
    )


@router.get("/{scan_id}/full", response_model=dict)
def get_gp_scan_full(scan_id: int, db: Session = Depends(get_db)):
    """Get full pipeline result for a GP scan."""
    scan = db.query(GPScanTable).filter(GPScanTable.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail=f"GP scan {scan_id} not found")
    
    return scan.pipeline_result


@router.get("/assets", response_model=List[AssetResponse])
def list_assets(limit: int = 100, db: Session = Depends(get_db)):
    """List all assets."""
    assets = db.query(AssetTable).order_by(AssetTable.name).limit(limit).all()
    
    return [
        AssetResponse(
            id=asset.id,
            name=asset.name,
            ticker=asset.ticker,
            isin=asset.isin,
            country=asset.country,
            region=asset.region,
            sub_region=asset.sub_region,
            asset_type=asset.asset_type,
            asset_class=asset.asset_class,
            sector=asset.sector,
            is_emerging_market=asset.is_emerging_market == "true",
            is_developed_market=asset.is_developed_market == "true",
            is_global_fund=asset.is_global_fund == "true",
            exposures=asset.exposures or [],
            created_at=asset.created_at.isoformat() if asset.created_at else "",
            updated_at=asset.updated_at.isoformat() if asset.updated_at else "",
        )
        for asset in assets
    ]


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    """Get a specific asset by ID."""
    asset = db.query(AssetTable).filter(AssetTable.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    
    return AssetResponse(
        id=asset.id,
        name=asset.name,
        ticker=asset.ticker,
        isin=asset.isin,
        country=asset.country,
        region=asset.region,
        sub_region=asset.sub_region,
        asset_type=asset.asset_type,
        asset_class=asset.asset_class,
        sector=asset.sector,
        is_emerging_market=asset.is_emerging_market == "true",
        is_developed_market=asset.is_developed_market == "true",
        is_global_fund=asset.is_global_fund == "true",
        exposures=asset.exposures or [],
        created_at=asset.created_at.isoformat() if asset.created_at else "",
        updated_at=asset.updated_at.isoformat() if asset.updated_at else "",
    )
