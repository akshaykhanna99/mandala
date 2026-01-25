"""In-memory audit store for geopolitical risk scans."""
from typing import Dict, List, Optional
from .schemas.geo_risk import GeoRiskScanResult


class GeoRiskStore:
    """Simple in-memory store for scan results (MVP)."""
    
    def __init__(self, max_scans: int = 100):
        self._scans: Dict[str, GeoRiskScanResult] = {}
        self._max_scans = max_scans
    
    def store(self, result: GeoRiskScanResult) -> None:
        """Store a scan result."""
        self._scans[result.scan_id] = result
        
        # Evict oldest if over limit
        if len(self._scans) > self._max_scans:
            # Sort by created_at and remove oldest
            sorted_scans = sorted(
                self._scans.items(),
                key=lambda x: x[1].created_at,
            )
            oldest_id = sorted_scans[0][0]
            del self._scans[oldest_id]
    
    def get(self, scan_id: str) -> Optional[GeoRiskScanResult]:
        """Retrieve a scan by ID."""
        return self._scans.get(scan_id)
    
    def list_by_client(self, client_id: str, limit: int = 10) -> List[GeoRiskScanResult]:
        """List scans for a specific client, newest first."""
        matching = [
            scan for scan in self._scans.values()
            if scan.inputs.client_id == client_id
        ]
        # Sort by created_at descending
        matching.sort(key=lambda x: x.created_at, reverse=True)
        return matching[:limit]
    
    def list_all(self, limit: int = 20) -> List[GeoRiskScanResult]:
        """List all scans, newest first."""
        scans = list(self._scans.values())
        scans.sort(key=lambda x: x.created_at, reverse=True)
        return scans[:limit]


# Global singleton instance
_store = GeoRiskStore()


def get_store() -> GeoRiskStore:
    """Get the global store instance."""
    return _store
