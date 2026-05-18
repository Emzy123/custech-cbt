"""
Question bank encryption and security controls API endpoints.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from ..schemas.question_security import (
    QuestionEncryptionRequest, QuestionEncryptionResponse, QuestionDecryptionRequest,
    QuestionDecryptionResponse, KeyRotationRequest, KeyRotationResponse,
    QuestionIntegrityResponse, EncryptionStatusResponse, SecurityAuditRequest
)
from ..services.question_security_service import QuestionSecurityService
from ..core.database import get_db
from .deps import get_current_active_user, require_permission

router = APIRouter(prefix="/question-security", tags=["question-security"])


@router.post("/encrypt", response_model=QuestionEncryptionResponse, dependencies=[Depends(require_permission("question.encrypt"))])
async def encrypt_question_data(
    encryption_request: QuestionEncryptionRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> QuestionEncryptionResponse:
    """Encrypt question data."""
    try:
        security_service = QuestionSecurityService(db)
        result = await security_service.encrypt_question_data(encryption_request.question_data)
        
        # Audit the encryption access
        await security_service.audit_encryption_access(
            current_user.id,
            "QUESTION_DATA_ENCRYPTED",
            {
                "question_id": encryption_request.question_data.get("id"),
                "fields_encrypted": result.get("_encryption_metadata", {}).get("encrypted_fields", [])
            }
        )
        
        return QuestionEncryptionResponse(
            success=True,
            encrypted_data=result,
            metadata=result.get("_encryption_metadata", {})
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to encrypt question data"
        )


@router.post("/decrypt", response_model=QuestionDecryptionResponse, dependencies=[Depends(require_permission("question.decrypt"))])
async def decrypt_question_data(
    decryption_request: QuestionDecryptionRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> QuestionDecryptionResponse:
    """Decrypt question data."""
    try:
        security_service = QuestionSecurityService(db)
        result = await security_service.decrypt_question_data(decryption_request.encrypted_data)
        
        # Audit the decryption access
        await security_service.audit_encryption_access(
            current_user.id,
            "QUESTION_DATA_DECRYPTED",
            {
                "question_id": result.get("id"),
                "fields_decrypted": result.get("_encryption_metadata", {}).get("encrypted_fields", [])
            }
        )
        
        return QuestionDecryptionResponse(
            success=True,
            decrypted_data=result,
            metadata=result.get("_encryption_metadata", {})
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt question data"
        )


@router.post("/questions/{question_id}/encrypt-text", dependencies=[Depends(require_permission("question.encrypt"))])
async def encrypt_question_text(
    question_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Encrypt question text."""
    try:
        from ..models.question import Question

        # Get question
        question = await Question.get(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )

        security_service = QuestionSecurityService(db)
        result = await security_service.encrypt_question_text(question_id, question.question_text)
        
        # Audit the encryption access
        await security_service.audit_encryption_access(
            current_user.id,
            "QUESTION_TEXT_ENCRYPTED",
            {
                "question_id": question_id,
                "key_id": result["key_id"]
            }
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
            detail="Failed to encrypt question text"
        )


@router.post("/questions/{question_id}/decrypt-text", dependencies=[Depends(require_permission("question.decrypt"))])
async def decrypt_question_text(
    question_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Decrypt question text."""
    try:
        security_service = QuestionSecurityService(db)
        result = await security_service.decrypt_question_text(question_id)
        
        # Audit the decryption access
        await security_service.audit_encryption_access(
            current_user.id,
            "QUESTION_TEXT_DECRYPTED",
            {
                "question_id": question_id,
                "key_id": result["key_id"]
            }
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
            detail="Failed to decrypt question text"
        )


@router.post("/questions/{question_id}/encrypt-options", dependencies=[Depends(require_permission("question.encrypt"))])
async def encrypt_question_options(
    question_id: str,
    options_data: List[Dict[str, Any]],
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Encrypt question options."""
    try:
        security_service = QuestionSecurityService(db)
        result = await security_service.encrypt_question_options(question_id, options_data)
        
        # Audit the encryption access
        await security_service.audit_encryption_access(
            current_user.id,
            "QUESTION_OPTIONS_ENCRYPTED",
            {
                "question_id": question_id,
                "options_count": len(options_data),
                "key_id": result["key_id"]
            }
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
            detail="Failed to encrypt question options"
        )


@router.post("/questions/{question_id}/decrypt-options", dependencies=[Depends(require_permission("question.decrypt"))])
async def decrypt_question_options(
    question_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Decrypt question options."""
    try:
        security_service = QuestionSecurityService(db)
        result = await security_service.decrypt_question_options(question_id)
        
        # Audit the decryption access
        await security_service.audit_encryption_access(
            current_user.id,
            "QUESTION_OPTIONS_DECRYPTED",
            {
                "question_id": question_id,
                "options_count": result["options_count"],
                "key_id": result["key_id"]
            }
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
            detail="Failed to decrypt question options"
        )


@router.post("/keys/rotate", response_model=KeyRotationResponse, dependencies=[Depends(require_permission("question.security.admin"))])
async def rotate_encryption_keys(
    rotation_request: KeyRotationRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> KeyRotationResponse:
    """Rotate encryption keys."""
    try:
        security_service = QuestionSecurityService(db)
        result = await security_service.rotate_encryption_keys(rotation_request.force_rotation)
        
        # Audit the key rotation
        await security_service.audit_encryption_access(
            current_user.id,
            "ENCRYPTION_KEY_ROTATION",
            {
                "new_key_id": result.get("new_key_id"),
                "reencrypted_count": result.get("reencrypted_count", 0),
                "forced": rotation_request.force_rotation
            }
        )
        
        return KeyRotationResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rotate encryption keys"
        )


@router.get("/questions/{question_id}/integrity", response_model=QuestionIntegrityResponse, dependencies=[Depends(require_permission("question.security.read"))])
async def validate_question_integrity(
    question_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> QuestionIntegrityResponse:
    """Validate question data integrity."""
    try:
        security_service = QuestionSecurityService(db)
        result = await security_service.validate_question_integrity(question_id)
        
        return QuestionIntegrityResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate question integrity"
        )


@router.get("/status", response_model=EncryptionStatusResponse, dependencies=[Depends(require_permission("question.security.read"))])
async def get_encryption_status(
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> EncryptionStatusResponse:
    """Get encryption status and statistics."""
    try:
        security_service = QuestionSecurityService(db)
        result = await security_service.get_encryption_status()
        
        return EncryptionStatusResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get encryption status"
        )


@router.post("/audit", dependencies=[Depends(require_permission("question.security.audit"))])
async def audit_encryption_access(
    audit_request: SecurityAuditRequest,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Audit encryption-related access."""
    try:
        security_service = QuestionSecurityService(db)
        result = await security_service.audit_encryption_access(
            audit_request.user_id,
            audit_request.action,
            audit_request.details
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
            detail="Failed to audit encryption access"
        )


@router.get("/questions/{question_id}/security-info", dependencies=[Depends(require_permission("question.security.read"))])
async def get_question_security_info(
    question_id: str,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get security information for a question."""
    try:
        from ..models.question import Question

        # Get question
        question = await Question.get(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )

        # Get security information
        security_info = {
            "question_id": question_id,
            "encryption_status": {
                "text_encrypted": question.encrypted_question_text is not None,
                "options_encrypted": question.encrypted_options is not None,
                "text_key_id": question.encryption_key_id,
                "options_key_id": question.options_encryption_key_id,
                "encrypted_at": question.encrypted_at,
                "options_encrypted_at": question.options_encrypted_at
            },
            "hash_status": {
                "text_hash": question.question_text_hash,
                "options_hash": question.options_hash
            },
            "security_level": "high" if (
                question.encrypted_question_text and question.encrypted_options
            ) else "medium" if (
                question.encrypted_question_text or question.encrypted_options
            ) else "low"
        }
        
        return security_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get question security info"
        )


@router.post("/questions/batch/encrypt", dependencies=[Depends(require_permission("question.encrypt"))])
async def batch_encrypt_questions(
    question_ids: List[str],
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Batch encrypt multiple questions."""
    try:
        from ..models.question import Question, QuestionOption

        security_service = QuestionSecurityService(db)

        results = {
            "batch_id": str(uuid.uuid4()),
            "total_questions": len(question_ids),
            "processed": 0,
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for question_id in question_ids:
            try:
                # Get question
                question = await Question.get(question_id)
                if not question:
                    results["errors"].append(f"Question {question_id} not found")
                    results["failed"] += 1
                    continue

                # Encrypt question text
                if question.question_text and not question.encrypted_question_text:
                    await security_service.encrypt_question_text(question_id, question.question_text)
                    question = await Question.get(question_id)

                # Encrypt question options (from QuestionOption documents)
                opts = await QuestionOption.find(QuestionOption.question_id == question_id).to_list()
                if opts and not question.encrypted_options:
                    options_payload = [
                        {
                            "option_text": o.option_text,
                            "is_correct": o.is_correct,
                            "explanation": o.explanation or "",
                        }
                        for o in opts
                    ]
                    await security_service.encrypt_question_options(question_id, options_payload)

                results["success"] += 1

            except Exception as e:
                results["errors"].append(f"Question {question_id}: {str(e)}")
                results["failed"] += 1

            results["processed"] += 1
        
        # Audit the batch encryption
        await security_service.audit_encryption_access(
            current_user.id,
            "BATCH_QUESTION_ENCRYPTION",
            {
                "batch_id": results["batch_id"],
                "total_questions": results["total_questions"],
                "success_count": results["success"],
                "failed_count": results["failed"]
            }
        )
        
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to batch encrypt questions"
        )


@router.post("/questions/batch/validate-integrity", dependencies=[Depends(require_permission("question.security.read"))])
async def batch_validate_integrity(
    question_ids: List[str],
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Batch validate integrity of multiple questions."""
    try:
        security_service = QuestionSecurityService(db)
        
        results = {
            "batch_id": str(uuid.uuid4()),
            "total_questions": len(question_ids),
            "processed": 0,
            "passed": 0,
            "failed": 0,
            "average_integrity_score": 0.0,
            "validation_results": []
        }
        
        total_score = 0.0
        
        for question_id in question_ids:
            try:
                validation_result = await security_service.validate_question_integrity(question_id)
                results["validation_results"].append(validation_result)
                
                if validation_result["passed"]:
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                
                total_score += validation_result["integrity_score"]
                
            except Exception as e:
                results["validation_results"].append({
                    "question_id": question_id,
                    "error": str(e),
                    "passed": False,
                    "integrity_score": 0.0
                })
                results["failed"] += 1
            
            results["processed"] += 1
        
        # Calculate average integrity score
        if results["processed"] > 0:
            results["average_integrity_score"] = total_score / results["processed"]
        
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to batch validate integrity"
        )


@router.get("/security-events", dependencies=[Depends(require_permission("question.security.admin"))])
async def get_security_events(
    event_type: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 100,
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get security events."""
    try:
        from datetime import datetime
        security_service = QuestionSecurityService(db)
        
        # Get events from cache
        if date:
            events_cache_key = f"security_events:{date}"
        else:
            events_cache_key = f"security_events:{datetime.utcnow().strftime('%Y-%m-%d')}"
        
        events = await security_service.cache.get(events_cache_key) or []
        
        # Filter by event type if specified
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]
        
        # Apply limit
        if len(events) > limit:
            events = events[-limit:]
        
        return {
            "events": events,
            "total_events": len(events),
            "filters": {
                "event_type": event_type,
                "date": date,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security events"
        )


@router.get("/encryption-keys", dependencies=[Depends(require_permission("question.security.admin"))])
async def get_encryption_keys(
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get encryption keys information."""
    try:
        security_service = QuestionSecurityService(db)
        
        # Get active keys
        active_keys = await security_service.cache.get("question_encryption_active_keys")
        active_keys_list = json.loads(active_keys) if active_keys else []
        
        # Get key information
        keys_info = []
        for key_id in active_keys_list:
            key_info = {
                "key_id": key_id,
                "status": "active",
                "created_at": None,  # Would need to track this in production
                "last_used": None   # Would need to track this in production
            }
            keys_info.append(key_info)
        
        # Get last rotation
        last_rotation = await security_service._get_last_key_rotation()
        
        return {
            "active_keys": keys_info,
            "total_keys": len(keys_info),
            "last_rotation": last_rotation,
            "rotation_frequency": "90 days"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get encryption keys"
        )


@router.post("/security-policy/update", dependencies=[Depends(require_permission("question.security.admin"))])
async def update_security_policy(
    policy_data: Dict[str, Any],
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Update security policy."""
    try:
        security_service = QuestionSecurityService(db)
        
        # Store policy in cache
        policy_cache_key = "question_security_policy"
        await security_service.cache.set(policy_cache_key, policy_data, ttl=86400 * 365)
        
        # Audit policy update
        await security_service.audit_encryption_access(
            current_user.id,
            "SECURITY_POLICY_UPDATED",
            {
                "policy_changes": list(policy_data.keys())
            }
        )
        
        return {
            "policy_updated": True,
            "updated_at": datetime.utcnow(),
            "updated_by": current_user.id,
            "policy_sections": list(policy_data.keys())
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update security policy"
        )


@router.get("/security-policy", dependencies=[Depends(require_permission("question.security.read"))])
async def get_security_policy(
    db: Any = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get current security policy."""
    try:
        security_service = QuestionSecurityService(db)
        
        # Get policy from cache
        policy_cache_key = "question_security_policy"
        policy = await security_service.cache.get(policy_cache_key)
        
        if not policy:
            # Return default policy
            policy = {
                "encryption_required": True,
                "key_rotation_frequency": "90_days",
                "integrity_validation": True,
                "audit_logging": True,
                "access_control": "role_based",
                "data_retention": "7_years"
            }
        
        return {
            "policy": policy,
            "last_updated": policy.get("last_updated"),
            "version": policy.get("version", "1.0")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security policy"
        )
