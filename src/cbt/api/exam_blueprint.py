"""
Exam blueprint and configuration API endpoints.
"""

from typing import List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..schemas.exam_blueprint import (
    ExamBlueprintCreate, ExamBlueprintUpdate, ExamBlueprintResponse,
    BlueprintValidationRequest, BlueprintValidationResponse,
    ExamScheduleCreate, ExamScheduleResponse, ConflictDetectionRequest,
    ConflictDetectionResponse, QuestionSelectionRequest, QuestionSelectionResponse,
    ExamConfigurationSummary, BlueprintTemplateCreate, BlueprintTemplate,
    BlueprintStatistics, ExamConfigurationRequest, ExamConfigurationResponse
)
from ..services.exam_blueprint_service import ExamBlueprintService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/exam-blueprint", tags=["exam-blueprint"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("exam.create"))])
async def create_blueprint(
    blueprint_data: ExamBlueprintCreate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create exam blueprint."""
    try:
        blueprint_service = ExamBlueprintService(db)
        blueprint = await blueprint_service.create_blueprint(blueprint_data, current_user.id)
        return blueprint
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create blueprint"
        )


@router.post("/{blueprint_id}/validate", response_model=BlueprintValidationResponse, dependencies=[Depends(require_permission("exam.update"))])
async def validate_blueprint(
    blueprint_id: str,
    validation_request: BlueprintValidationRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> BlueprintValidationResponse:
    """Validate exam blueprint."""
    try:
        blueprint_service = ExamBlueprintService(db)
        validation_request.blueprint_id = blueprint_id
        result = await blueprint_service.validate_blueprint(validation_request, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Blueprint validation failed"
        )


@router.get("/{blueprint_id}", dependencies=[Depends(require_permission("exam.read"))])
async def get_blueprint(
    blueprint_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get blueprint by ID."""
    try:
        blueprint_service = ExamBlueprintService(db)
        blueprint = await blueprint_service._get_blueprint(blueprint_id)
        if not blueprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blueprint not found"
            )
        return blueprint
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get blueprint"
        )


@router.put("/{blueprint_id}", dependencies=[Depends(require_permission("exam.update"))])
async def update_blueprint(
    blueprint_id: str,
    blueprint_data: ExamBlueprintUpdate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update blueprint."""
    try:
        blueprint_service = ExamBlueprintService(db)
        # Get existing blueprint
        blueprint = await blueprint_service._get_blueprint(blueprint_id)
        if not blueprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blueprint not found"
            )
        
        # Update fields
        for field, value in blueprint_data.model_dump(exclude_unset=True).items():
            if field in blueprint:
                blueprint[field] = value
        
        blueprint["updated_at"] = datetime.utcnow()
        blueprint["updated_by"] = current_user.id
        blueprint["status"] = "draft"  # Reset status when updated
        
        await blueprint_service._store_blueprint(blueprint)
        return blueprint
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update blueprint"
        )


@router.delete("/{blueprint_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("exam.delete"))])
async def delete_blueprint(
    blueprint_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete blueprint."""
    try:
        blueprint_service = ExamBlueprintService(db)
        blueprint = await blueprint_service._get_blueprint(blueprint_id)
        if not blueprint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blueprint not found"
            )
        
        # Soft delete by setting status
        blueprint["status"] = "deleted"
        blueprint["updated_at"] = datetime.utcnow()
        blueprint["updated_by"] = current_user.id
        
        await blueprint_service._store_blueprint(blueprint)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete blueprint"
        )


# Schedule Management
@router.post("/schedule", response_model=ExamScheduleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("exam.schedule"))])
async def create_schedule(
    schedule_data: ExamScheduleCreate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExamScheduleResponse:
    """Create exam schedule."""
    try:
        blueprint_service = ExamBlueprintService(db)
        schedule = await blueprint_service.create_exam_schedule(schedule_data, current_user.id)
        return schedule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schedule"
        )


@router.post("/schedule/{schedule_id}/detect-conflicts", response_model=ConflictDetectionResponse, dependencies=[Depends(require_permission("exam.schedule"))])
async def detect_conflicts(
    schedule_id: str,
    conflict_request: ConflictDetectionRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ConflictDetectionResponse:
    """Detect scheduling conflicts."""
    try:
        blueprint_service = ExamBlueprintService(db)
        result = await blueprint_service.detect_conflicts(conflict_request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conflict detection failed"
        )


@router.get("/schedule/{schedule_id}", dependencies=[Depends(require_permission("exam.read"))])
async def get_schedule(
    schedule_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get schedule by ID."""
    try:
        blueprint_service = ExamBlueprintService(db)
        schedule = await blueprint_service._get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )
        return schedule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get schedule"
        )


@router.put("/schedule/{schedule_id}/confirm", dependencies=[Depends(require_permission("exam.schedule"))])
async def confirm_schedule(
    schedule_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Confirm exam schedule."""
    try:
        blueprint_service = ExamBlueprintService(db)
        schedule = await blueprint_service._get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule not found"
            )
        
        schedule["status"] = "confirmed"
        schedule["updated_at"] = datetime.utcnow()
        schedule["updated_by"] = current_user.id
        
        await blueprint_service._store_schedule(schedule)
        return schedule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm schedule"
        )


# Question Selection
@router.post("/select-questions", response_model=QuestionSelectionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("exam.create"))])
async def select_questions(
    selection_request: QuestionSelectionRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> QuestionSelectionResponse:
    """Select questions for exam."""
    try:
        blueprint_service = ExamBlueprintService(db)
        result = await blueprint_service.select_questions(selection_request, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Question selection failed"
        )


@router.get("/selection/{selection_id}", dependencies=[Depends(require_permission("exam.read"))])
async def get_question_selection(
    selection_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get question selection by ID."""
    try:
        blueprint_service = ExamBlueprintService(db)
        selection = await blueprint_service._get_selection(selection_id)
        if not selection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question selection not found"
            )
        return selection
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get question selection"
        )


# Configuration Summary
@router.get("/examination/{examination_id}/configuration-summary", response_model=ExamConfigurationSummary, dependencies=[Depends(require_permission("exam.read"))])
async def get_configuration_summary(
    examination_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExamConfigurationSummary:
    """Get complete exam configuration summary."""
    try:
        blueprint_service = ExamBlueprintService(db)
        summary = await blueprint_service.get_configuration_summary(examination_id)
        return summary
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get configuration summary"
        )


# Blueprint Templates
@router.post("/templates", response_model=BlueprintTemplate, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("exam.create"))])
async def create_blueprint_template(
    template_data: BlueprintTemplateCreate,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> BlueprintTemplate:
    """Create reusable blueprint template."""
    try:
        blueprint_service = ExamBlueprintService(db)
        template = await blueprint_service.create_blueprint_template(template_data, current_user.id)
        return template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create blueprint template"
        )


@router.get("/templates", response_model=List[BlueprintTemplate], dependencies=[Depends(require_permission("exam.read"))])
async def list_blueprint_templates(
    course_id: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[BlueprintTemplate]:
    """List blueprint templates."""
    try:
        # Simplified - would query database
        return []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list blueprint templates"
        )


@router.get("/templates/{template_id}", response_model=BlueprintTemplate, dependencies=[Depends(require_permission("exam.read"))])
async def get_blueprint_template(
    template_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> BlueprintTemplate:
    """Get blueprint template by ID."""
    try:
        # Simplified - would query database
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get blueprint template"
        )


@router.post("/templates/{template_id}/use", response_model=dict, dependencies=[Depends(require_permission("exam.create"))])
async def use_blueprint_template(
    template_id: str,
    examination_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Use blueprint template for new exam."""
    try:
        # Get template
        template = await get_blueprint_template(template_id, db, current_user)
        
        # Create blueprint from template
        blueprint_data = ExamBlueprintCreate(
            examination_id=examination_id,
            total_questions=template.total_questions,
            total_points=template.total_points,
            requirements=template.requirements,
            randomization_enabled=template.settings.get("randomization_enabled", True),
            option_shuffle_enabled=template.settings.get("option_shuffle_enabled", True),
            question_order_randomization=template.settings.get("question_order_randomization", True)
        )
        
        blueprint_service = ExamBlueprintService(db)
        blueprint = await blueprint_service.create_blueprint(blueprint_data, current_user.id)
        
        return {
            "success": True,
            "message": "Blueprint created from template",
            "blueprint_id": blueprint["id"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to use blueprint template"
        )


# Statistics
@router.get("/statistics", response_model=BlueprintStatistics, dependencies=[Depends(require_permission("exam.read"))])
async def get_blueprint_statistics(
    course_id: Optional[str] = Query(None),
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> BlueprintStatistics:
    """Get blueprint statistics."""
    try:
        # Simplified - would query database and calculate statistics
        return BlueprintStatistics(
            total_blueprints=0,
            validated_blueprints=0,
            pending_validation=0,
            failed_validation=0,
            by_course={},
            by_difficulty_distribution={},
            by_cognitive_level_distribution={},
            average_questions_per_blueprint=0.0,
            average_points_per_blueprint=0.0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get blueprint statistics"
        )


# Complete Configuration
@router.post("/configure", response_model=ExamConfigurationResponse, dependencies=[Depends(require_permission("exam.create"))])
async def configure_complete_exam(
    config_request: ExamConfigurationRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> ExamConfigurationResponse:
    """Configure complete exam (blueprint, schedule, question selection)."""
    try:
        blueprint_service = ExamBlueprintService(db)
        errors = []
        warnings = []
        
        # Create blueprint
        try:
            blueprint = await blueprint_service.create_blueprint(config_request.blueprint, current_user.id)
            blueprint_response = blueprint
        except ValueError as e:
            errors.append(f"Blueprint creation failed: {str(e)}")
            blueprint_response = None
        
        # Create schedule
        try:
            schedule = await blueprint_service.create_exam_schedule(config_request.schedule, current_user.id)
            schedule_response = schedule
        except ValueError as e:
            errors.append(f"Schedule creation failed: {str(e)}")
            schedule_response = None
        
        # Validate blueprint if requested
        validation_results = None
        if config_request.auto_validate and blueprint_response:
            try:
                validation_request = BlueprintValidationRequest(blueprint_id=blueprint_response["id"])
                validation_results = await blueprint_service.validate_blueprint(validation_request, current_user.id)
                if not validation_results.is_valid:
                    errors.extend(validation_results.validation_errors)
                    warnings.extend(validation_results.validation_warnings)
            except Exception as e:
                warnings.append(f"Blueprint validation failed: {str(e)}")
        
        # Detect conflicts if requested
        conflict_results = None
        if config_request.auto_detect_conflicts and schedule_response:
            try:
                conflict_request = ConflictDetectionRequest(examination_id=config_request.examination_id)
                conflict_results = await blueprint_service.detect_conflicts(conflict_request)
                if conflict_results.has_conflicts:
                    warnings.append("Scheduling conflicts detected")
            except Exception as e:
                warnings.append(f"Conflict detection failed: {str(e)}")
        
        # Select questions
        selection_response = None
        if blueprint_response:
            try:
                selection_response = await blueprint_service.select_questions(config_request.question_selection, current_user.id)
            except ValueError as e:
                errors.append(f"Question selection failed: {str(e)}")
        
        success = len(errors) == 0
        
        return ExamConfigurationResponse(
            success=success,
            examination_id=config_request.examination_id,
            blueprint=blueprint_response,
            schedule=schedule_response,
            question_selection=selection_response,
            validation_results=validation_results,
            conflict_results=conflict_results,
            errors=errors,
            warnings=warnings,
            configured_at=datetime.utcnow(),
            configured_by=current_user.id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Complete exam configuration failed: {str(e)}"
        )
