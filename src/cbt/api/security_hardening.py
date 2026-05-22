"""
Security hardening and SAST/DAST scanning API endpoints.
"""

from typing import Any, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status as http_status

from ..schemas.security import SASTScanRequest, SASTScanResponse
from ..services.security_hardening_service import SecurityHardeningService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/security", tags=["security-hardening"])


def _get_security_service(db: Any = Depends(get_db)) -> SecurityHardeningService:
    return SecurityHardeningService(db)


@router.post(
    "/sast/scan",
    response_model=SASTScanResponse,
    dependencies=[Depends(require_permission("security.scan"))],
)
async def run_sast_scan(
    scan_request: SASTScanRequest,
    background_tasks: BackgroundTasks,
    service: SecurityHardeningService = Depends(_get_security_service),
    current_user: Any = Depends(get_current_active_user),
) -> SASTScanResponse:
    """Run Static Application Security Testing (SAST) scan."""
    try:
        if scan_request.scan_type == "comprehensive":
            # Fire off a quick scan synchronously so we have a real scan_id,
            # then return it immediately (simulates background for long scans).
            result = await service.run_sast_scan(scan_request.scan_type)
        else:
            result = await service.run_sast_scan(scan_request.scan_type)
        return SASTScanResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run SAST scan",
        )


@router.get(
    "/scans",
    dependencies=[Depends(require_permission("security.read"))],
)
async def list_scans(
    limit: int = 50,
    service: SecurityHardeningService = Depends(_get_security_service),
    current_user: Any = Depends(get_current_active_user),
) -> Any:
    """List recent security scans."""
    try:
        return await service.get_scans(limit=limit)
    except Exception:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list scans",
        )


@router.get(
    "/scan/{scan_id}",
    dependencies=[Depends(require_permission("security.read"))],
)
async def get_scan(
    scan_id: str,
    service: SecurityHardeningService = Depends(_get_security_service),
    current_user: Any = Depends(get_current_active_user),
) -> Any:
    """Get a security scan by ID with its vulnerability list."""
    try:
        result = await service.get_scan(scan_id)
        if result is None:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Scan not found",
            )
        return result
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scan",
        )


@router.get(
    "/dashboard",
    dependencies=[Depends(require_permission("security.read"))],
)
async def get_security_dashboard(
    service: SecurityHardeningService = Depends(_get_security_service),
    current_user: Any = Depends(get_current_active_user),
) -> Any:
    """Get security dashboard overview."""
    try:
        return await service.get_security_dashboard()
    except Exception:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security dashboard",
        )
