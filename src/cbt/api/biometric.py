"""
Biometric integration API endpoints.
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from ..schemas.biometric import (
    BiometricTemplateRegister,
    BiometricTemplateResponse,
    BiometricVerificationRequest,
    BiometricVerificationResponse,
    BiometricTemplateUpdate,
    BiometricTemplateDeactivate,
    BiometricDeviceRegister,
    BiometricDeviceResponse,
    BiometricStatisticsResponse,
)
from ..services.biometric_service import BiometricService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/biometric", tags=["biometric"])


def _get_biometric_service(db: Any = Depends(get_db)) -> BiometricService:
    return BiometricService(db)


@router.post(
    "/templates/register",
    response_model=BiometricTemplateResponse,
    dependencies=[Depends(require_permission("biometric.register"))],
)
async def register_biometric_template(
    template_data: BiometricTemplateRegister,
    service: BiometricService = Depends(_get_biometric_service),
    current_user: Any = Depends(get_current_active_user),
) -> BiometricTemplateResponse:
    """Register a new biometric template for the authenticated user."""
    try:
        result = await service.register_biometric_template(
            current_user.id, template_data.model_dump(mode="json")
        )
        return BiometricTemplateResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register biometric template",
        )


@router.get(
    "/templates",
    dependencies=[Depends(require_permission("biometric.read"))],
)
async def get_user_biometric_templates(
    user_id: Optional[str] = None,
    service: BiometricService = Depends(_get_biometric_service),
    current_user: Any = Depends(get_current_active_user),
) -> Any:
    """Get biometric templates for the current user (or another user for admins)."""
    try:
        target_user_id = user_id or current_user.id
        templates = await service.get_user_biometric_templates(target_user_id)
        return {
            "user_id": target_user_id,
            "templates": templates,
            "total_count": len(templates),
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get biometric templates",
        )


@router.post(
    "/verify",
    response_model=BiometricVerificationResponse,
    dependencies=[Depends(require_permission("biometric.verify"))],
)
async def verify_biometric(
    verification_data: BiometricVerificationRequest,
    service: BiometricService = Depends(_get_biometric_service),
    current_user: Any = Depends(get_current_active_user),
) -> BiometricVerificationResponse:
    """Verify biometric data against stored templates."""
    try:
        result = await service.verify_biometric(
            current_user.id, verification_data.model_dump(mode="json")
        )
        return BiometricVerificationResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify biometric",
        )


@router.put(
    "/templates/{template_id}",
    response_model=BiometricTemplateResponse,
    dependencies=[Depends(require_permission("biometric.update"))],
)
async def update_biometric_template(
    template_id: str,
    template_data: BiometricTemplateUpdate,
    service: BiometricService = Depends(_get_biometric_service),
    current_user: Any = Depends(get_current_active_user),
) -> BiometricTemplateResponse:
    """Update an existing biometric template."""
    try:
        result = await service.update_biometric_template(
            template_id, template_data.model_dump(mode="json")
        )
        return BiometricTemplateResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update biometric template",
        )


@router.post(
    "/templates/{template_id}/deactivate",
    dependencies=[Depends(require_permission("biometric.deactivate"))],
)
async def deactivate_biometric_template(
    template_id: str,
    deactivation_data: BiometricTemplateDeactivate,
    service: BiometricService = Depends(_get_biometric_service),
    current_user: Any = Depends(get_current_active_user),
) -> Any:
    """Deactivate a biometric template."""
    try:
        return await service.deactivate_biometric_template(
            template_id, deactivation_data.reason
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate biometric template",
        )


@router.post(
    "/devices/register",
    response_model=BiometricDeviceResponse,
    dependencies=[Depends(require_permission("biometric.admin"))],
)
async def register_biometric_device(
    device_data: BiometricDeviceRegister,
    service: BiometricService = Depends(_get_biometric_service),
    current_user: Any = Depends(get_current_active_user),
) -> BiometricDeviceResponse:
    """Register a biometric device."""
    try:
        result = await service.register_biometric_device(device_data.model_dump(mode="json"))
        return BiometricDeviceResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register biometric device",
        )


@router.get(
    "/statistics",
    response_model=BiometricStatisticsResponse,
    dependencies=[Depends(require_permission("biometric.read"))],
)
async def get_biometric_statistics(
    user_id: Optional[str] = None,
    service: BiometricService = Depends(_get_biometric_service),
    current_user: Any = Depends(get_current_active_user),
) -> BiometricStatisticsResponse:
    """Get biometric statistics."""
    try:
        stats = await service.get_biometric_statistics(user_id)
        return BiometricStatisticsResponse(**stats)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get biometric statistics",
        )
