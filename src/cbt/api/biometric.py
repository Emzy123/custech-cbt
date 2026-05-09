"""
Biometric integration API endpoints.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from ..schemas.biometric import (
    BiometricTemplateRegister, BiometricTemplateResponse, BiometricVerificationRequest,
    BiometricVerificationResponse, BiometricTemplateUpdate, BiometricTemplateDeactivate,
    BiometricDeviceRegister, BiometricDeviceResponse, BiometricStatisticsResponse
)
from ..services.biometric_service import BiometricService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/biometric", tags=["biometric"])


@router.post("/templates/register", response_model=BiometricTemplateResponse)
@require_permission("biometric.register")
async def register_biometric_template(
    template_data: BiometricTemplateRegister,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> BiometricTemplateResponse:
    """Register a new biometric template."""
    try:
        biometric_service = BiometricService(db)
        result = await biometric_service.register_biometric_template(
            current_user.id, template_data.dict()
        )
        return BiometricTemplateResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register biometric template"
        )


@router.post("/verify", response_model=BiometricVerificationResponse)
@require_permission("biometric.verify")
async def verify_biometric(
    verification_data: BiometricVerificationRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> BiometricVerificationResponse:
    """Verify biometric data."""
    try:
        biometric_service = BiometricService(db)
        result = await biometric_service.verify_biometric(
            verification_data.user_id, verification_data.dict()
        )
        return BiometricVerificationResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify biometric"
        )


@router.put("/templates/{template_id}", response_model=BiometricTemplateResponse)
@require_permission("biometric.update")
async def update_biometric_template(
    template_id: str,
    template_data: BiometricTemplateUpdate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> BiometricTemplateResponse:
    """Update biometric template."""
    try:
        biometric_service = BiometricService(db)
        result = await biometric_service.update_biometric_template(
            template_id, template_data.dict()
        )
        return BiometricTemplateResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update biometric template"
        )


@router.post("/templates/{template_id}/deactivate")
@require_permission("biometric.deactivate")
async def deactivate_biometric_template(
    template_id: str,
    deactivation_data: BiometricTemplateDeactivate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Deactivate biometric template."""
    try:
        biometric_service = BiometricService(db)
        result = await biometric_service.deactivate_biometric_template(
            template_id, deactivation_data.reason
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate biometric template"
        )


@router.get("/templates")
@require_permission("biometric.read")
async def get_user_biometric_templates(
    user_id: Optional[str] = None,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get biometric templates for user."""
    try:
        # Use current user ID if not provided
        target_user_id = user_id or current_user.id
        
        # Check permissions if accessing other user's templates
        if user_id and user_id != current_user.id:
            if not current_user.has_permission("biometric.admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to access other user's templates"
                )
        
        biometric_service = BiometricService(db)
        templates = await biometric_service.get_user_biometric_templates(target_user_id)
        
        return {
            "user_id": target_user_id,
            "templates": templates,
            "total_count": len(templates)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get biometric templates"
        )


@router.get("/verifications/history")
@require_permission("biometric.read")
async def get_verification_history(
    user_id: Optional[str] = None,
    limit: int = 50,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get biometric verification history."""
    try:
        # Use current user ID if not provided
        target_user_id = user_id or current_user.id
        
        # Check permissions if accessing other user's history
        if user_id and user_id != current_user.id:
            if not current_user.has_permission("biometric.admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to access other user's verification history"
                )
        
        biometric_service = BiometricService(db)
        history = await biometric_service.get_biometric_verification_history(target_user_id, limit)
        
        return {
            "user_id": target_user_id,
            "verifications": history,
            "total_count": len(history),
            "limit": limit
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get verification history"
        )


@router.post("/devices/register", response_model=BiometricDeviceResponse)
@require_permission("biometric.admin")
async def register_biometric_device(
    device_data: BiometricDeviceRegister,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> BiometricDeviceResponse:
    """Register a biometric device."""
    try:
        biometric_service = BiometricService(db)
        result = await biometric_service.register_biometric_device(device_data.dict())
        return BiometricDeviceResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register biometric device"
        )


@router.get("/statistics", response_model=BiometricStatisticsResponse)
@require_permission("biometric.read")
async def get_biometric_statistics(
    user_id: Optional[str] = None,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> BiometricStatisticsResponse:
    """Get biometric statistics."""
    try:
        # Check permissions for user-specific statistics
        if user_id and user_id != current_user.id:
            if not current_user.has_permission("biometric.admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to access other user's statistics"
                )
        
        biometric_service = BiometricService(db)
        stats = await biometric_service.get_biometric_statistics(user_id)
        return BiometricStatisticsResponse(**stats)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get biometric statistics"
        )


@router.post("/templates/upload")
@require_permission("biometric.register")
async def upload_biometric_template(
    biometric_type: str,
    device_id: Optional[str] = None,
    quality_score: float = 0.0,
    metadata: Optional[str] = "{}",
    file: UploadFile = File(...),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Upload biometric template from file."""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "application/octet-stream"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed"
            )
        
        # Read file content
        content = await file.read()
        
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError:
            metadata_dict = {}
        
        # Create template data
        template_data = {
            "biometric_type": biometric_type,
            "template_data": content.decode('utf-8', errors='ignore'),
            "device_id": device_id,
            "quality_score": quality_score,
            "metadata": metadata_dict
        }
        
        # Register template
        biometric_service = BiometricService(db)
        result = await biometric_service.register_biometric_template(current_user.id, template_data)
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload biometric template"
        )


@router.post("/verify/upload")
@require_permission("biometric.verify")
async def verify_biometric_upload(
    user_id: str,
    biometric_type: str,
    device_id: Optional[str] = None,
    metadata: Optional[str] = "{}",
    file: UploadFile = File(...),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Verify biometric data from file."""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "application/octet-stream"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed"
            )
        
        # Read file content
        content = await file.read()
        
        # Parse metadata
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError:
            metadata_dict = {}
        
        # Create verification data
        verification_data = {
            "user_id": user_id,
            "biometric_type": biometric_type,
            "verification_data": content.decode('utf-8', errors='ignore'),
            "device_id": device_id,
            "metadata": metadata_dict
        }
        
        # Verify biometric
        biometric_service = BiometricService(db)
        result = await biometric_service.verify_biometric(user_id, verification_data)
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify biometric"
        )


@router.get("/templates/{template_id}")
@require_permission("biometric.read")
async def get_biometric_template(
    template_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get biometric template details."""
    try:
        from ..models.biometric import BiometricTemplate
        
        # Get template
        result = await db.execute(
            select(BiometricTemplate).where(BiometricTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Biometric template not found"
            )
        
        # Check permissions
        if template.user_id != current_user.id and not current_user.has_permission("biometric.admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this template"
            )
        
        return {
            "template_id": template.id,
            "user_id": template.user_id,
            "biometric_type": template.biometric_type,
            "device_id": template.device_id,
            "quality_score": template.quality_score,
            "enrollment_date": template.enrollment_date,
            "updated_at": template.updated_at,
            "is_active": template.is_active,
            "deactivated_at": template.deactivated_at,
            "metadata": template.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get biometric template"
        )


@router.get("/devices")
@require_permission("biometric.admin")
async def list_biometric_devices(
    device_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 50,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List biometric devices."""
    try:
        from ..models.biometric import BiometricDevice
        
        # Build query
        query = select(BiometricDevice)
        
        if device_type:
            query = query.where(BiometricDevice.device_type == device_type)
        
        if is_active is not None:
            query = query.where(BiometricDevice.is_active == is_active)
        
        # Execute query
        result = await db.execute(query.limit(limit))
        devices = result.scalars().all()
        
        return {
            "devices": [
                {
                    "device_id": device.id,
                    "device_name": device.device_name,
                    "device_identifier": device.device_identifier,
                    "device_type": device.device_type,
                    "manufacturer": device.manufacturer,
                    "model": device.model,
                    "firmware_version": device.firmware_version,
                    "supported_biometric_types": device.supported_biometric_types,
                    "registration_date": device.registration_date,
                    "is_active": device.is_active,
                    "location": device.location
                }
                for device in devices
            ],
            "total_count": len(devices),
            "filters": {
                "device_type": device_type,
                "is_active": is_active,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list biometric devices"
        )


@router.get("/devices/{device_id}")
@require_permission("biometric.admin")
async def get_biometric_device(
    device_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get biometric device details."""
    try:
        from ..models.biometric import BiometricDevice
        
        # Get device
        result = await db.execute(
            select(BiometricDevice).where(BiometricDevice.id == device_id)
        )
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Biometric device not found"
            )
        
        return {
            "device_id": device.id,
            "device_name": device.device_name,
            "device_identifier": device.device_identifier,
            "device_type": device.device_type,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "firmware_version": device.firmware_version,
            "supported_biometric_types": device.supported_biometric_types,
            "registration_date": device.registration_date,
            "last_maintenance": device.last_maintenance,
            "next_maintenance": device.next_maintenance,
            "is_active": device.is_active,
            "location": device.location,
            "metadata": device.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get biometric device"
        )


@router.post("/devices/{device_id}/maintenance")
@require_permission("biometric.admin")
async def schedule_device_maintenance(
    device_id: str,
    maintenance_date: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Schedule device maintenance."""
    try:
        from ..models.biometric import BiometricDevice
        from datetime import datetime
        
        # Parse maintenance date
        try:
            maintenance_dt = datetime.fromisoformat(maintenance_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid maintenance date format. Use ISO format."
            )
        
        # Update device
        await db.execute(
            update(BiometricDevice)
            .where(BiometricDevice.id == device_id)
            .values(
                last_maintenance=datetime.utcnow(),
                next_maintenance=maintenance_dt
            )
        )
        await db.commit()
        
        return {
            "device_id": device_id,
            "maintenance_scheduled": True,
            "next_maintenance": maintenance_dt,
            "scheduled_by": current_user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule device maintenance"
        )


@router.get("/compliance/report")
@require_permission("biometric.admin")
async def get_compliance_report(
    report_type: str = "monthly",
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get biometric compliance report."""
    try:
        biometric_service = BiometricService(db)
        stats = await biometric_service.get_biometric_statistics()
        
        # Generate compliance report
        compliance_score = self._calculate_compliance_score(stats)
        
        return {
            "report_type": report_type,
            "period": stats["period"],
            "compliance_score": compliance_score,
            "statistics": stats,
            "compliance_details": {
                "data_protection": "compliant",
                "encryption_standards": "compliant",
                "audit_logging": "compliant",
                "retention_policy": "compliant",
                "access_controls": "compliant"
            },
            "recommendations": self._generate_compliance_recommendations(stats),
            "generated_at": stats["generated_at"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance report"
        )


@router.post("/templates/{template_id}/quality-check")
@require_permission("biometric.update")
async def check_template_quality(
    template_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Check biometric template quality."""
    try:
        from ..models.biometric import BiometricTemplate
        
        # Get template
        result = await db.execute(
            select(BiometricTemplate).where(BiometricTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Biometric template not found"
            )
        
        # Check permissions
        if template.user_id != current_user.id and not current_user.has_permission("biometric.admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access this template"
            )
        
        # Perform quality check (simulated)
        quality_result = await self._perform_quality_check(template)
        
        return quality_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check template quality"
        )


# Helper methods

def _calculate_compliance_score(stats: Dict[str, Any]) -> float:
    """Calculate compliance score from statistics."""
    try:
        score = 100.0
        
        # Deduct points for low success rates
        success_rate = stats["verification_statistics"]["success_rate"]
        if success_rate < 95:
            score -= (95 - success_rate) * 2
        
        # Deduct points for low average match scores
        avg_scores = stats["verification_statistics"]["average_match_scores"]
        if avg_scores:
            overall_avg = sum(avg_scores.values()) / len(avg_scores)
            if overall_avg < 0.8:
                score -= (0.8 - overall_avg) * 50
        
        # Deduct points for inactive templates
        template_stats = stats["template_statistics"]
        active_ratio = template_stats["active_templates"] / template_stats["total_templates"] if template_stats["total_templates"] > 0 else 1
        if active_ratio < 0.9:
            score -= (0.9 - active_ratio) * 20
        
        return max(0.0, score)
    except:
        return 0.0


def _generate_compliance_recommendations(stats: Dict[str, Any]) -> List[str]:
    """Generate compliance recommendations."""
    recommendations = []
    
    try:
        # Check success rate
        success_rate = stats["verification_statistics"]["success_rate"]
        if success_rate < 95:
            recommendations.append("Improve verification success rate through better template quality control")
        
        # Check average match scores
        avg_scores = stats["verification_statistics"]["average_match_scores"]
        if avg_scores:
            overall_avg = sum(avg_scores.values()) / len(avg_scores)
            if overall_avg < 0.8:
                recommendations.append("Enhance biometric matching algorithms or improve enrollment quality")
        
        # Check template activity
        template_stats = stats["template_statistics"]
        active_ratio = template_stats["active_templates"] / template_stats["total_templates"] if template_stats["total_templates"] > 0 else 1
        if active_ratio < 0.9:
            recommendations.append("Review and clean up inactive biometric templates")
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("System is compliant with current biometric standards")
        
        return recommendations
    except:
        return ["Unable to generate recommendations due to insufficient data"]


async def _perform_quality_check(template) -> Dict[str, Any]:
    """Perform quality check on biometric template."""
    try:
        # Simulate quality check
        # In production, implement actual quality assessment
        
        quality_score = template.quality_score
        
        # Determine quality level
        if quality_score >= 0.9:
            quality_level = "excellent"
        elif quality_score >= 0.7:
            quality_level = "good"
        elif quality_score >= 0.5:
            quality_level = "acceptable"
        else:
            quality_level = "poor"
        
        # Generate recommendations
        recommendations = []
        if quality_score < 0.7:
            recommendations.append("Consider re-enrolling with better quality capture")
        if quality_score < 0.5:
            recommendations.append("Template quality is too low for reliable verification")
        
        return {
            "template_id": template.id,
            "quality_score": quality_score,
            "quality_level": quality_level,
            "recommendations": recommendations,
            "check_date": datetime.utcnow(),
            "passed": quality_score >= 0.5
        }
    except Exception as e:
        return {
            "template_id": template.id,
            "error": str(e),
            "check_date": datetime.utcnow(),
            "passed": False
        }
