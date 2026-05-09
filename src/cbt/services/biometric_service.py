"""
Biometric integration service with secure template handling.
"""

import uuid
import hashlib
import secrets
import base64
import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from ..models.user import User
from ..models.biometric import BiometricTemplate, BiometricVerification, BiometricDevice
from ..core.redis import cache_manager
from ..core.security import security
from ..core.exceptions import ValidationError, AuthenticationError


class BiometricService:
    """Biometric integration service with secure template handling."""
    
    def __init__(self, db: Any):
        self.db = db
        self.cache = cache_manager
        self.security = security
    
    async def register_biometric_template(self, user_id: str, biometric_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new biometric template for a user.
        
        Args:
            user_id: User ID
            biometric_data: Biometric data including type, template, and metadata
            
        Returns:
            Registration result
        """
        try:
            # Validate user exists
            user_result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise ValidationError("User not found")
            
            # Check if biometric type already exists for user
            existing_template = await self.db.execute(
                select(BiometricTemplate).where(
                    and_(
                        BiometricTemplate.user_id == user_id,
                        BiometricTemplate.biometric_type == biometric_data["biometric_type"],
                        BiometricTemplate.is_active == True
                    )
                )
            )
            if existing_template.scalar_one_or_none():
                raise ValidationError(f"Biometric template of type {biometric_data['biometric_type']} already exists for user")
            
            # Process and encrypt biometric template
            processed_template = await self._process_biometric_template(biometric_data)
            
            # Create biometric template record
            template = BiometricTemplate(
                id=str(uuid.uuid4()),
                user_id=user_id,
                biometric_type=biometric_data["biometric_type"],
                template_data=processed_template["encrypted_template"],
                template_hash=processed_template["template_hash"],
                device_id=biometric_data.get("device_id"),
                quality_score=biometric_data.get("quality_score", 0.0),
                enrollment_date=datetime.utcnow(),
                is_active=True,
                metadata=biometric_data.get("metadata", {})
            )
            
            self.db.add(template)
            await self.db.commit()
            
            # Log biometric registration
            await self._log_biometric_event(
                user_id, "BIOMETRIC_TEMPLATE_REGISTERED",
                {
                    "template_id": template.id,
                    "biometric_type": biometric_data["biometric_type"],
                    "device_id": biometric_data.get("device_id")
                }
            )
            
            return {
                "template_id": template.id,
                "user_id": user_id,
                "biometric_type": biometric_data["biometric_type"],
                "enrollment_date": template.enrollment_date,
                "quality_score": template.quality_score,
                "status": "registered"
            }
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to register biometric template: {str(e)}")
    
    async def verify_biometric(self, user_id: str, biometric_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify biometric data against stored templates.
        
        Args:
            user_id: User ID
            biometric_data: Biometric data for verification
            
        Returns:
            Verification result
        """
        try:
            # Get active biometric templates for user
            templates_result = await self.db.execute(
                select(BiometricTemplate).where(
                    and_(
                        BiometricTemplate.user_id == user_id,
                        BiometricTemplate.biometric_type == biometric_data["biometric_type"],
                        BiometricTemplate.is_active == True
                    )
                )
            )
            templates = templates_result.scalars().all()
            
            if not templates:
                raise ValidationError(f"No active biometric template found for type {biometric_data['biometric_type']}")
            
            # Process verification data
            processed_verification = await self._process_verification_data(biometric_data)
            
            # Verify against each template
            best_match = None
            best_score = 0.0
            
            for template in templates:
                # Decrypt template
                decrypted_template = await self._decrypt_template(template.template_data)
                
                # Perform biometric matching
                match_result = await self._match_biometric_data(
                    processed_verification["processed_data"],
                    decrypted_template,
                    biometric_data["biometric_type"]
                )
                
                if match_result["match_score"] > best_score:
                    best_score = match_result["match_score"]
                    best_match = {
                        "template_id": template.id,
                        "match_score": match_result["match_score"],
                        "confidence": match_result["confidence"],
                        "verification_method": match_result["method"]
                    }
            
            # Determine verification result
            threshold = self._get_verification_threshold(biometric_data["biometric_type"])
            verification_passed = best_score >= threshold
            
            # Create verification record
            verification = BiometricVerification(
                id=str(uuid.uuid4()),
                user_id=user_id,
                template_id=best_match["template_id"] if best_match else None,
                biometric_type=biometric_data["biometric_type"],
                verification_data=processed_verification["encrypted_data"],
                verification_hash=processed_verification["verification_hash"],
                match_score=best_score,
                confidence=best_match["confidence"] if best_match else 0.0,
                verification_method=best_match["verification_method"] if best_match else "none",
                passed=verification_passed,
                verification_date=datetime.utcnow(),
                device_id=biometric_data.get("device_id"),
                metadata=biometric_data.get("metadata", {})
            )
            
            self.db.add(verification)
            await self.db.commit()
            
            # Log verification attempt
            await self._log_biometric_event(
                user_id, "BIOMETRIC_VERIFICATION_ATTEMPT",
                {
                    "verification_id": verification.id,
                    "biometric_type": biometric_data["biometric_type"],
                    "match_score": best_score,
                    "passed": verification_passed
                }
            )
            
            return {
                "verification_id": verification.id,
                "user_id": user_id,
                "biometric_type": biometric_data["biometric_type"],
                "passed": verification_passed,
                "match_score": best_score,
                "confidence": best_match["confidence"] if best_match else 0.0,
                "verification_date": verification.verification_date,
                "threshold": threshold
            }
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to verify biometric: {str(e)}")
    
    async def update_biometric_template(self, template_id: str, biometric_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing biometric template.
        
        Args:
            template_id: Template ID
            biometric_data: Updated biometric data
            
        Returns:
            Update result
        """
        try:
            # Get existing template
            template_result = await self.db.execute(
                select(BiometricTemplate).where(BiometricTemplate.id == template_id)
            )
            template = template_result.scalar_one_or_none()
            if not template:
                raise ValidationError("Biometric template not found")
            
            # Process and encrypt new template data
            processed_template = await self._process_biometric_template(biometric_data)
            
            # Update template
            template.template_data = processed_template["encrypted_template"]
            template.template_hash = processed_template["template_hash"]
            template.quality_score = biometric_data.get("quality_score", template.quality_score)
            template.updated_at = datetime.utcnow()
            template.metadata.update(biometric_data.get("metadata", {}))
            
            await self.db.commit()
            
            # Log template update
            await self._log_biometric_event(
                template.user_id, "BIOMETRIC_TEMPLATE_UPDATED",
                {
                    "template_id": template_id,
                    "biometric_type": template.biometric_type
                }
            )
            
            return {
                "template_id": template_id,
                "user_id": template.user_id,
                "biometric_type": template.biometric_type,
                "updated_at": template.updated_at,
                "quality_score": template.quality_score,
                "status": "updated"
            }
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to update biometric template: {str(e)}")
    
    async def deactivate_biometric_template(self, template_id: str, reason: str) -> Dict[str, Any]:
        """
        Deactivate a biometric template.
        
        Args:
            template_id: Template ID
            reason: Deactivation reason
            
        Returns:
            Deactivation result
        """
        try:
            # Get existing template
            template_result = await self.db.execute(
                select(BiometricTemplate).where(BiometricTemplate.id == template_id)
            )
            template = template_result.scalar_one_or_none()
            if not template:
                raise ValidationError("Biometric template not found")
            
            # Deactivate template
            template.is_active = False
            template.deactivated_at = datetime.utcnow()
            template.deactivation_reason = reason
            
            await self.db.commit()
            
            # Log template deactivation
            await self._log_biometric_event(
                template.user_id, "BIOMETRIC_TEMPLATE_DEACTIVATED",
                {
                    "template_id": template_id,
                    "biometric_type": template.biometric_type,
                    "reason": reason
                }
            )
            
            return {
                "template_id": template_id,
                "user_id": template.user_id,
                "biometric_type": template.biometric_type,
                "deactivated_at": template.deactivated_at,
                "reason": reason,
                "status": "deactivated"
            }
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to deactivate biometric template: {str(e)}")
    
    async def get_user_biometric_templates(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all biometric templates for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of biometric templates
        """
        try:
            templates_result = await self.db.execute(
                select(BiometricTemplate).where(BiometricTemplate.user_id == user_id)
            )
            templates = templates_result.scalars().all()
            
            return [
                {
                    "template_id": template.id,
                    "biometric_type": template.biometric_type,
                    "device_id": template.device_id,
                    "quality_score": template.quality_score,
                    "enrollment_date": template.enrollment_date,
                    "is_active": template.is_active,
                    "deactivated_at": template.deactivated_at,
                    "metadata": template.metadata
                }
                for template in templates
            ]
            
        except Exception as e:
            raise ValueError(f"Failed to get user biometric templates: {str(e)}")
    
    async def get_biometric_verification_history(self, user_id: str, 
                                                limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get biometric verification history for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of records to return
            
        Returns:
            List of verification records
        """
        try:
            verifications_result = await self.db.execute(
                select(BiometricVerification)
                .where(BiometricVerification.user_id == user_id)
                .order_by(BiometricVerification.verification_date.desc())
                .limit(limit)
            )
            verifications = verifications_result.scalars().all()
            
            return [
                {
                    "verification_id": verification.id,
                    "biometric_type": verification.biometric_type,
                    "match_score": verification.match_score,
                    "confidence": verification.confidence,
                    "passed": verification.passed,
                    "verification_date": verification.verification_date,
                    "device_id": verification.device_id
                }
                for verification in verifications
            ]
            
        except Exception as e:
            raise ValueError(f"Failed to get verification history: {str(e)}")
    
    async def register_biometric_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a biometric device.
        
        Args:
            device_data: Device information
            
        Returns:
            Device registration result
        """
        try:
            # Check if device already exists
            existing_device = await self.db.execute(
                select(BiometricDevice).where(
                    BiometricDevice.device_identifier == device_data["device_identifier"]
                )
            )
            if existing_device.scalar_one_or_none():
                raise ValidationError("Device already registered")
            
            # Create device record
            device = BiometricDevice(
                id=str(uuid.uuid4()),
                device_name=device_data["device_name"],
                device_identifier=device_data["device_identifier"],
                device_type=device_data["device_type"],
                manufacturer=device_data.get("manufacturer"),
                model=device_data.get("model"),
                firmware_version=device_data.get("firmware_version"),
                supported_biometric_types=device_data.get("supported_biometric_types", []),
                registration_date=datetime.utcnow(),
                is_active=True,
                metadata=device_data.get("metadata", {})
            )
            
            self.db.add(device)
            await self.db.commit()
            
            return {
                "device_id": device.id,
                "device_name": device.device_name,
                "device_identifier": device.device_identifier,
                "device_type": device.device_type,
                "registration_date": device.registration_date,
                "status": "registered"
            }
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to register biometric device: {str(e)}")
    
    async def get_biometric_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get biometric system statistics.
        
        Args:
            user_id: Optional user ID for user-specific stats
            
        Returns:
            Biometric statistics
        """
        try:
            base_query = select(BiometricTemplate)
            if user_id:
                base_query = base_query.where(BiometricTemplate.user_id == user_id)
            
            # Template statistics
            templates_result = await self.db.execute(base_query)
            templates = templates_result.scalars().all()
            
            active_templates = [t for t in templates if t.is_active]
            template_types = {}
            for template in templates:
                biometric_type = template.biometric_type
                if biometric_type not in template_types:
                    template_types[biometric_type] = {"total": 0, "active": 0}
                template_types[biometric_type]["total"] += 1
                if template.is_active:
                    template_types[biometric_type]["active"] += 1
            
            # Verification statistics
            verification_query = select(BiometricVerification)
            if user_id:
                verification_query = verification_query.where(BiometricVerification.user_id == user_id)
            
            verifications_result = await self.db.execute(verification_query)
            verifications = verifications_result.scalars().all()
            
            recent_verifications = [
                v for v in verifications 
                if v.verification_date >= datetime.utcnow() - timedelta(days=30)
            ]
            
            successful_verifications = [v for v in recent_verifications if v.passed]
            failed_verifications = [v for v in recent_verifications if not v.passed]
            
            # Calculate statistics
            total_verifications = len(recent_verifications)
            success_rate = (len(successful_verifications) / total_verifications * 100) if total_verifications > 0 else 0
            
            # Average match scores by type
            avg_scores_by_type = {}
            for verification in recent_verifications:
                biometric_type = verification.biometric_type
                if biometric_type not in avg_scores_by_type:
                    avg_scores_by_type[biometric_type] = []
                avg_scores_by_type[biometric_type].append(verification.match_score)
            
            for biometric_type in avg_scores_by_type:
                scores = avg_scores_by_type[biometric_type]
                avg_scores_by_type[biometric_type] = sum(scores) / len(scores)
            
            return {
                "template_statistics": {
                    "total_templates": len(templates),
                    "active_templates": len(active_templates),
                    "templates_by_type": template_types
                },
                "verification_statistics": {
                    "total_verifications": total_verifications,
                    "successful_verifications": len(successful_verifications),
                    "failed_verifications": len(failed_verifications),
                    "success_rate": round(success_rate, 2),
                    "average_match_scores": avg_scores_by_type
                },
                "period": "last_30_days",
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get biometric statistics: {str(e)}")
    
    # Private helper methods
    
    async def _process_biometric_template(self, biometric_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and encrypt biometric template."""
        try:
            # Extract template data
            template_data = biometric_data["template_data"]
            
            # Validate template format
            if not isinstance(template_data, (str, bytes)):
                raise ValidationError("Invalid template data format")
            
            # Convert to bytes if string
            if isinstance(template_data, str):
                template_data = template_data.encode('utf-8')
            
            # Generate template hash
            template_hash = hashlib.sha256(template_data).hexdigest()
            
            # Encrypt template data
            encrypted_template = await self._encrypt_template(template_data)
            
            return {
                "encrypted_template": encrypted_template,
                "template_hash": template_hash
            }
            
        except Exception as e:
            raise ValueError(f"Failed to process biometric template: {str(e)}")
    
    async def _process_verification_data(self, biometric_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and encrypt verification data."""
        try:
            # Extract verification data
            verification_data = biometric_data["verification_data"]
            
            # Validate verification data format
            if not isinstance(verification_data, (str, bytes)):
                raise ValidationError("Invalid verification data format")
            
            # Convert to bytes if string
            if isinstance(verification_data, str):
                verification_data = verification_data.encode('utf-8')
            
            # Generate verification hash
            verification_hash = hashlib.sha256(verification_data).hexdigest()
            
            # Encrypt verification data
            encrypted_data = await self._encrypt_template(verification_data)
            
            return {
                "processed_data": verification_data,
                "encrypted_data": encrypted_data,
                "verification_hash": verification_hash
            }
            
        except Exception as e:
            raise ValueError(f"Failed to process verification data: {str(e)}")
    
    async def _encrypt_template(self, template_data: bytes) -> str:
        """Encrypt biometric template data."""
        try:
            # Generate encryption key
            encryption_key = secrets.token_bytes(32)
            
            # Simple encryption (in production, use proper encryption library)
            # This is a placeholder - implement proper AES encryption
            encrypted_data = base64.b64encode(template_data).decode('utf-8')
            
            # Store encryption key securely (in production, use KMS)
            key_id = secrets.token_hex(16)
            await self.cache.set(f"biometric_key:{key_id}", encryption_key.hex(), ttl=86400 * 365)
            
            # Return encrypted data with key reference
            return f"{key_id}:{encrypted_data}"
            
        except Exception as e:
            raise ValueError(f"Failed to encrypt template: {str(e)}")
    
    async def _decrypt_template(self, encrypted_template: str) -> bytes:
        """Decrypt biometric template data."""
        try:
            # Extract key ID and encrypted data
            if ":" not in encrypted_template:
                raise ValueError("Invalid encrypted template format")
            
            key_id, encrypted_data = encrypted_template.split(":", 1)
            
            # Retrieve encryption key
            encryption_key_hex = await self.cache.get(f"biometric_key:{key_id}")
            if not encryption_key_hex:
                raise ValueError("Encryption key not found")
            
            encryption_key = bytes.fromhex(encryption_key_hex)
            
            # Decrypt data (placeholder - implement proper AES decryption)
            decrypted_data = base64.b64decode(encrypted_data.encode('utf-8'))
            
            return decrypted_data
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt template: {str(e)}")
    
    async def _match_biometric_data(self, verification_data: bytes, template_data: bytes, 
                                  biometric_type: str) -> Dict[str, Any]:
        """Match biometric data against template."""
        try:
            # Simulate biometric matching algorithm
            # In production, integrate with actual biometric SDK
            
            if biometric_type == "fingerprint":
                return await self._match_fingerprint(verification_data, template_data)
            elif biometric_type == "facial_recognition":
                return await self._match_facial_recognition(verification_data, template_data)
            elif biometric_type == "iris":
                return await self._match_iris(verification_data, template_data)
            else:
                raise ValueError(f"Unsupported biometric type: {biometric_type}")
                
        except Exception as e:
            raise ValueError(f"Failed to match biometric data: {str(e)}")
    
    async def _match_fingerprint(self, verification_data: bytes, template_data: bytes) -> Dict[str, Any]:
        """Match fingerprint biometric data."""
        # Simulate fingerprint matching
        # In production, use actual fingerprint matching algorithm
        
        # Calculate similarity score (0.0 to 1.0)
        similarity_score = self._calculate_similarity_score(verification_data, template_data)
        
        # Determine confidence based on similarity
        if similarity_score >= 0.9:
            confidence = "high"
        elif similarity_score >= 0.7:
            confidence = "medium"
        else:
            confidence = "low"
        
        return {
            "match_score": similarity_score,
            "confidence": confidence,
            "method": "minutiae_matching"
        }
    
    async def _match_facial_recognition(self, verification_data: bytes, template_data: bytes) -> Dict[str, Any]:
        """Match facial recognition biometric data."""
        # Simulate facial recognition matching
        # In production, use actual facial recognition algorithm
        
        similarity_score = self._calculate_similarity_score(verification_data, template_data)
        
        if similarity_score >= 0.85:
            confidence = "high"
        elif similarity_score >= 0.65:
            confidence = "medium"
        else:
            confidence = "low"
        
        return {
            "match_score": similarity_score,
            "confidence": confidence,
            "method": "feature_matching"
        }
    
    async def _match_iris(self, verification_data: bytes, template_data: bytes) -> Dict[str, Any]:
        """Match iris biometric data."""
        # Simulate iris matching
        # In production, use actual iris recognition algorithm
        
        similarity_score = self._calculate_similarity_score(verification_data, template_data)
        
        if similarity_score >= 0.95:
            confidence = "high"
        elif similarity_score >= 0.8:
            confidence = "medium"
        else:
            confidence = "low"
        
        return {
            "match_score": similarity_score,
            "confidence": confidence,
            "method": "iris_code_matching"
        }
    
    def _calculate_similarity_score(self, data1: bytes, data2: bytes) -> float:
        """Calculate similarity score between two data sets."""
        # Simple similarity calculation (placeholder)
        # In production, use proper biometric similarity algorithms
        
        if len(data1) != len(data2):
            return 0.0
        
        # Calculate Hamming distance
        distance = sum(b1 != b2 for b1, b2 in zip(data1, data2))
        max_distance = len(data1) * 8  # Maximum possible distance
        
        # Convert to similarity score (0.0 to 1.0)
        similarity = 1.0 - (distance / max_distance)
        
        # Add some randomness to simulate real biometric variation
        import random
        similarity += random.uniform(-0.1, 0.1)
        similarity = max(0.0, min(1.0, similarity))
        
        return round(similarity, 4)
    
    def _get_verification_threshold(self, biometric_type: str) -> float:
        """Get verification threshold for biometric type."""
        thresholds = {
            "fingerprint": 0.7,
            "facial_recognition": 0.65,
            "iris": 0.8,
            "voice": 0.6,
            "palm": 0.75
        }
        return thresholds.get(biometric_type, 0.7)
    
    async def _log_biometric_event(self, user_id: str, event_type: str, details: Dict[str, Any]):
        """Log biometric event."""
        try:
            event = {
                "user_id": user_id,
                "event_type": event_type,
                "details": details,
                "timestamp": datetime.utcnow()
            }
            
            # Store in cache (in production, use proper logging system)
            events_cache_key = f"biometric_events:{user_id}"
            existing_events = await self.cache.get(events_cache_key) or []
            existing_events.append(event)
            await self.cache.set(events_cache_key, existing_events, ttl=86400 * 30)  # 30 days
            
        except Exception as e:
            logging.error(f"Error: {str(e)}")
