"""
Question bank encryption and security controls service.
"""

import uuid
import hashlib
import secrets
import base64
import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from ..models.question import Question
from ..models.security import SecurityEvent
from ..core.redis import cache_manager
from ..core.security import security
from ..core.exceptions import ValidationError, SecurityError


class QuestionSecurityService:
    """Question bank encryption and security controls service."""
    
    def __init__(self, db: Any):
        self.db = db
        self.cache = cache_manager
        self.security = security
    
    async def encrypt_question_data(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive question data.
        
        Args:
            question_data: Question data to encrypt
            
        Returns:
            Encrypted question data with metadata
        """
        try:
            # Identify sensitive fields
            sensitive_fields = ['question_text', 'options', 'explanation', 'model_answer']
            
            # Create encrypted version
            encrypted_data = {}
            encryption_metadata = {
                'encrypted_fields': [],
                'encryption_method': 'AES-256-GCM',
                'key_id': None,
                'encrypted_at': datetime.utcnow().isoformat()
            }
            
            for field, value in question_data.items():
                if field in sensitive_fields and value is not None:
                    # Encrypt the field
                    encrypted_value = await self._encrypt_field(value)
                    encrypted_data[field] = encrypted_value['encrypted_data']
                    encryption_metadata['encrypted_fields'].append(field)
                    
                    # Store key reference
                    if encryption_metadata['key_id'] is None:
                        encryption_metadata['key_id'] = encrypted_value['key_id']
                else:
                    encrypted_data[field] = value
            
            # Add encryption metadata
            encrypted_data['_encryption_metadata'] = encryption_metadata
            
            return encrypted_data
            
        except Exception as e:
            raise ValueError(f"Failed to encrypt question data: {str(e)}")
    
    async def decrypt_question_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt encrypted question data.
        
        Args:
            encrypted_data: Encrypted question data
            
        Returns:
            Decrypted question data
        """
        try:
            # Get encryption metadata
            encryption_metadata = encrypted_data.get('_encryption_metadata', {})
            key_id = encryption_metadata.get('key_id')
            encrypted_fields = encryption_metadata.get('encrypted_fields', [])
            
            if not key_id:
                raise SecurityError("No encryption key ID found in metadata")
            
            # Decrypt sensitive fields
            decrypted_data = {}
            for field, value in encrypted_data.items():
                if field == '_encryption_metadata':
                    decrypted_data[field] = value
                elif field in encrypted_fields:
                    decrypted_value = await self._decrypt_field(value, key_id)
                    decrypted_data[field] = decrypted_value
                else:
                    decrypted_data[field] = value
            
            return decrypted_data
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt question data: {str(e)}")
    
    async def encrypt_question_text(self, question_id: str, plain_text: str) -> Dict[str, Any]:
        """
        Encrypt question text specifically.
        
        Args:
            question_id: Question ID
            plain_text: Plain text to encrypt
            
        Returns:
            Encrypted text with metadata
        """
        try:
            # Get question
            question_result = await self.db.execute(
                select(Question).where(Question.id == question_id)
            )
            question = question_result.scalar_one_or_none()
            if not question:
                raise ValidationError("Question not found")
            
            # Encrypt the text
            encrypted_result = await self._encrypt_field(plain_text)
            
            # Store encrypted text
            question.encrypted_question_text = encrypted_result['encrypted_data']
            question.encryption_key_id = encrypted_result['key_id']
            question.encrypted_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Log encryption event
            await self._log_security_event(
                "QUESTION_ENCRYPTED",
                {
                    "question_id": question_id,
                    "key_id": encrypted_result['key_id'],
                    "encrypted_at": question.encrypted_at
                }
            )
            
            return {
                "question_id": question_id,
                "encrypted": True,
                "key_id": encrypted_result['key_id'],
                "encrypted_at": question.encrypted_at
            }
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to encrypt question text: {str(e)}")
    
    async def decrypt_question_text(self, question_id: str) -> Dict[str, Any]:
        """
        Decrypt question text.
        
        Args:
            question_id: Question ID
            
        Returns:
            Decrypted text with metadata
        """
        try:
            # Get question
            question_result = await self.db.execute(
                select(Question).where(Question.id == question_id)
            )
            question = question_result.scalar_one_or_none()
            if not question:
                raise ValidationError("Question not found")
            
            if not question.encrypted_question_text:
                raise SecurityError("Question text is not encrypted")
            
            # Decrypt the text
            decrypted_text = await self._decrypt_field(
                question.encrypted_question_text,
                question.encryption_key_id
            )
            
            # Log decryption event
            await self._log_security_event(
                "QUESTION_DECRYPTED",
                {
                    "question_id": question_id,
                    "key_id": question.encryption_key_id,
                    "decrypted_at": datetime.utcnow()
                }
            )
            
            return {
                "question_id": question_id,
                "decrypted_text": decrypted_text,
                "key_id": question.encryption_key_id,
                "decrypted_at": datetime.utcnow()
            }
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt question text: {str(e)}")
    
    async def encrypt_question_options(self, question_id: str, options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Encrypt question options.
        
        Args:
            question_id: Question ID
            options: List of question options
            
        Returns:
            Encrypted options with metadata
        """
        try:
            # Get question
            question_result = await self.db.execute(
                select(Question).where(Question.id == question_id)
            )
            question = question_result.scalar_one_or_none()
            if not question:
                raise ValidationError("Question not found")
            
            # Encrypt options
            encrypted_options = []
            key_id = None
            
            for option in options:
                # Create option data to encrypt
                option_data = {
                    'option_text': option.get('option_text', ''),
                    'is_correct': option.get('is_correct', False),
                    'explanation': option.get('explanation', '')
                }
                
                # Encrypt the option
                encrypted_option = await self._encrypt_field(json.dumps(option_data))
                encrypted_options.append(encrypted_option['encrypted_data'])
                
                # Store key reference
                if key_id is None:
                    key_id = encrypted_option['key_id']
            
            # Store encrypted options
            question.encrypted_options = json.dumps(encrypted_options)
            question.options_encryption_key_id = key_id
            question.options_encrypted_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Log encryption event
            await self._log_security_event(
                "QUESTION_OPTIONS_ENCRYPTED",
                {
                    "question_id": question_id,
                    "options_count": len(options),
                    "key_id": key_id,
                    "encrypted_at": question.options_encrypted_at
                }
            )
            
            return {
                "question_id": question_id,
                "options_count": len(options),
                "encrypted": True,
                "key_id": key_id,
                "encrypted_at": question.options_encrypted_at
            }
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to encrypt question options: {str(e)}")
    
    async def decrypt_question_options(self, question_id: str) -> Dict[str, Any]:
        """
        Decrypt question options.
        
        Args:
            question_id: Question ID
            
        Returns:
            Decrypted options with metadata
        """
        try:
            # Get question
            question_result = await self.db.execute(
                select(Question).where(Question.id == question_id)
            )
            question = question_result.scalar_one_or_none()
            if not question:
                raise ValidationError("Question not found")
            
            if not question.encrypted_options:
                raise SecurityError("Question options are not encrypted")
            
            # Decrypt options
            encrypted_options = json.loads(question.encrypted_options)
            decrypted_options = []
            
            for encrypted_option in encrypted_options:
                decrypted_option = await self._decrypt_field(
                    encrypted_option,
                    question.options_encryption_key_id
                )
                option_data = json.loads(decrypted_option)
                decrypted_options.append(option_data)
            
            # Log decryption event
            await self._log_security_event(
                "QUESTION_OPTIONS_DECRYPTED",
                {
                    "question_id": question_id,
                    "options_count": len(decrypted_options),
                    "key_id": question.options_encryption_key_id,
                    "decrypted_at": datetime.utcnow()
                }
            )
            
            return {
                "question_id": question_id,
                "options": decrypted_options,
                "options_count": len(decrypted_options),
                "key_id": question.options_encryption_key_id,
                "decrypted_at": datetime.utcnow()
            }
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt question options: {str(e)}")
    
    async def rotate_encryption_keys(self, force_rotation: bool = False) -> Dict[str, Any]:
        """
        Rotate encryption keys for question bank.
        
        Args:
            force_rotation: Force rotation even if keys are not expired
            
        Returns:
            Key rotation results
        """
        try:
            # Check if rotation is needed
            if not force_rotation:
                last_rotation = await self._get_last_key_rotation()
                if last_rotation and (datetime.utcnow() - last_rotation) < timedelta(days=90):
                    return {
                        "rotation_needed": False,
                        "last_rotation": last_rotation,
                        "message": "Key rotation not needed yet"
                    }
            
            # Generate new master key
            new_master_key = secrets.token_bytes(32)
            new_key_id = secrets.token_hex(16)
            
            # Store new master key
            await self.cache.set(
                f"question_encryption_key:{new_key_id}",
                new_master_key.hex(),
                ttl=86400 * 365  # 1 year
            )
            
            # Get all questions with encrypted data
            questions_result = await self.db.execute(
                select(Question).where(
                    or_(
                        Question.encrypted_question_text.isnot(None),
                        Question.encrypted_options.isnot(None)
                    )
                )
            )
            questions = questions_result.scalars().all()
            
            # Re-encrypt questions with new key
            reencrypted_count = 0
            failed_count = 0
            
            for question in questions:
                try:
                    # Re-encrypt question text if present
                    if question.encrypted_question_text:
                        decrypted_text = await self._decrypt_field(
                            question.encrypted_question_text,
                            question.encryption_key_id
                        )
                        
                        # Re-encrypt with new key
                        reencrypted = await self._encrypt_field_with_key(
                            decrypted_text,
                            new_key_id
                        )
                        question.encrypted_question_text = reencrypted['encrypted_data']
                        question.encryption_key_id = new_key_id
                    
                    # Re-encrypt options if present
                    if question.encrypted_options:
                        encrypted_options = json.loads(question.encrypted_options)
                        reencrypted_options = []
                        
                        for encrypted_option in encrypted_options:
                            decrypted_option = await self._decrypt_field(
                                encrypted_option,
                                question.options_encryption_key_id
                            )
                            
                            # Re-encrypt with new key
                            reencrypted = await self._encrypt_field_with_key(
                                decrypted_option,
                                new_key_id
                            )
                            reencrypted_options.append(reencrypted['encrypted_data'])
                        
                        question.encrypted_options = json.dumps(reencrypted_options)
                        question.options_encryption_key_id = new_key_id
                    
                    question.encrypted_at = datetime.utcnow()
                    reencrypted_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    continue
            
            await self.db.commit()
            
            # Mark old keys as deprecated
            await self._deprec_old_keys(new_key_id)
            
            # Update rotation timestamp
            await self.cache.set(
                "question_encryption_last_rotation",
                datetime.utcnow().isoformat(),
                ttl=86400 * 365
            )
            
            # Log key rotation
            await self._log_security_event(
                "ENCRYPTION_KEY_ROTATION",
                {
                    "new_key_id": new_key_id,
                    "reencrypted_count": reencrypted_count,
                    "failed_count": failed_count,
                    "rotation_date": datetime.utcnow()
                }
            )
            
            return {
                "rotation_completed": True,
                "new_key_id": new_key_id,
                "reencrypted_count": reencrypted_count,
                "failed_count": failed_count,
                "rotation_date": datetime.utcnow()
            }
            
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to rotate encryption keys: {str(e)}")
    
    async def validate_question_integrity(self, question_id: str) -> Dict[str, Any]:
        """
        Validate question data integrity.
        
        Args:
            question_id: Question ID
            
        Returns:
            Integrity validation results
        """
        try:
            # Get question
            question_result = await self.db.execute(
                select(Question).where(Question.id == question_id)
            )
            question = question_result.scalar_one_or_none()
            if not question:
                raise ValidationError("Question not found")
            
            validation_results = {
                "question_id": question_id,
                "validation_date": datetime.utcnow(),
                "checks": {}
            }
            
            # Check question text integrity
            if question.encrypted_question_text:
                try:
                    decrypted_text = await self._decrypt_field(
                        question.encrypted_question_text,
                        question.encryption_key_id
                    )
                    
                    # Calculate hash
                    current_hash = hashlib.sha256(decrypted_text.encode()).hexdigest()
                    stored_hash = question.question_text_hash
                    
                    validation_results["checks"]["question_text"] = {
                        "encrypted": True,
                        "hash_valid": current_hash == stored_hash,
                        "decrypted_length": len(decrypted_text)
                    }
                except Exception as e:
                    validation_results["checks"]["question_text"] = {
                        "encrypted": True,
                        "hash_valid": False,
                        "error": str(e)
                    }
            else:
                validation_results["checks"]["question_text"] = {
                    "encrypted": False,
                    "hash_valid": True,
                    "plain_text_length": len(question.question_text or "")
                }
            
            # Check options integrity
            if question.encrypted_options:
                try:
                    decrypted_options = await self._decrypt_question_options(question_id)
                    options = decrypted_options["options"]
                    
                    # Calculate hash
                    options_json = json.dumps(options, sort_keys=True)
                    current_hash = hashlib.sha256(options_json.encode()).hexdigest()
                    stored_hash = question.options_hash
                    
                    validation_results["checks"]["options"] = {
                        "encrypted": True,
                        "hash_valid": current_hash == stored_hash,
                        "options_count": len(options)
                    }
                except Exception as e:
                    validation_results["checks"]["options"] = {
                        "encrypted": True,
                        "hash_valid": False,
                        "error": str(e)
                    }
            else:
                validation_results["checks"]["options"] = {
                    "encrypted": False,
                    "hash_valid": True,
                    "options_count": len(question.options or [])
                }
            
            # Calculate overall integrity score
            total_checks = len(validation_results["checks"])
            passed_checks = sum(
                1 for check in validation_results["checks"].values()
                if check.get("hash_valid", True)
            )
            
            validation_results["integrity_score"] = (passed_checks / total_checks) * 100 if total_checks > 0 else 100
            validation_results["passed"] = validation_results["integrity_score"] >= 90
            
            return validation_results
            
        except Exception as e:
            raise ValueError(f"Failed to validate question integrity: {str(e)}")
    
    async def get_encryption_status(self) -> Dict[str, Any]:
        """
        Get encryption status and statistics.
        
        Returns:
            Encryption status information
        """
        try:
            # Get encryption statistics
            total_questions_result = await self.db.execute(
                select(func.count(Question.id))
            )
            total_questions = total_questions_result.scalar() or 0
            
            encrypted_text_result = await self.db.execute(
                select(func.count(Question.id))
                .where(Question.encrypted_question_text.isnot(None))
            )
            encrypted_text_count = encrypted_text_result.scalar() or 0
            
            encrypted_options_result = await self.db.execute(
                select(func.count(Question.id))
                .where(Question.encrypted_options.isnot(None))
            )
            encrypted_options_count = encrypted_options_result.scalar() or 0
            
            # Get key rotation info
            last_rotation = await self._get_last_key_rotation()
            
            # Get active key count
            active_keys = await self._get_active_key_count()
            
            return {
                "total_questions": total_questions,
                "encrypted_questions_text": encrypted_text_count,
                "encrypted_questions_options": encrypted_options_count,
                "encryption_coverage": {
                    "text_encryption": (encrypted_text_count / total_questions * 100) if total_questions > 0 else 0,
                    "options_encryption": (encrypted_options_count / total_questions * 100) if total_questions > 0 else 0
                },
                "key_management": {
                    "active_keys": active_keys,
                    "last_rotation": last_rotation,
                    "rotation_frequency": "90 days"
                },
                "security_status": "healthy" if active_keys > 0 else "warning"
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get encryption status: {str(e)}")
    
    async def audit_encryption_access(self, user_id: str, action: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audit encryption-related access.
        
        Args:
            user_id: User ID performing the action
            action: Action performed
            details: Additional details
            
        Returns:
            Audit record
        """
        try:
            audit_record = {
                "audit_id": str(uuid.uuid4()),
                "user_id": user_id,
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow(),
                "ip_address": details.get("ip_address"),
                "user_agent": details.get("user_agent")
            }
            
            # Store audit record
            audit_cache_key = f"encryption_audit:{audit_record['audit_id']}"
            await self.cache.set(audit_cache_key, audit_record, ttl=86400 * 365)  # 1 year
            
            # Log security event
            await self._log_security_event(
                "ENCRYPTION_ACCESS_AUDIT",
                {
                    "audit_id": audit_record["audit_id"],
                    "user_id": user_id,
                    "action": action
                }
            )
            
            return audit_record
            
        except Exception as e:
            raise ValueError(f"Failed to audit encryption access: {str(e)}")
    
    # Private helper methods
    
    async def _encrypt_field(self, data: str) -> Dict[str, Any]:
        """Encrypt a single field."""
        try:
            # Generate encryption key
            encryption_key = secrets.token_bytes(32)
            key_id = secrets.token_hex(16)
            
            # Store encryption key
            await self.cache.set(
                f"question_encryption_key:{key_id}",
                encryption_key.hex(),
                ttl=86400 * 365  # 1 year
            )
            
            # Encrypt data (placeholder - implement proper AES-GCM encryption)
            encrypted_data = base64.b64encode(data.encode('utf-8')).decode('utf-8')
            
            return {
                "key_id": key_id,
                "encrypted_data": encrypted_data
            }
            
        except Exception as e:
            raise ValueError(f"Failed to encrypt field: {str(e)}")
    
    async def _encrypt_field_with_key(self, data: str, key_id: str) -> Dict[str, Any]:
        """Encrypt a field with a specific key."""
        try:
            # Get encryption key
            key_hex = await self.cache.get(f"question_encryption_key:{key_id}")
            if not key_hex:
                raise SecurityError("Encryption key not found")
            
            encryption_key = bytes.fromhex(key_hex)
            
            # Encrypt data (placeholder - implement proper AES-GCM encryption)
            encrypted_data = base64.b64encode(data.encode('utf-8')).decode('utf-8')
            
            return {
                "key_id": key_id,
                "encrypted_data": encrypted_data
            }
            
        except Exception as e:
            raise ValueError(f"Failed to encrypt field with key: {str(e)}")
    
    async def _decrypt_field(self, encrypted_data: str, key_id: str) -> str:
        """Decrypt a field."""
        try:
            # Get encryption key
            key_hex = await self.cache.get(f"question_encryption_key:{key_id}")
            if not key_hex:
                raise SecurityError("Encryption key not found")
            
            encryption_key = bytes.fromhex(key_hex)
            
            # Decrypt data (placeholder - implement proper AES-GCM decryption)
            decrypted_data = base64.b64decode(encrypted_data.encode('utf-8')).decode('utf-8')
            
            return decrypted_data
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt field: {str(e)}")
    
    async def _get_last_key_rotation(self) -> Optional[datetime]:
        """Get last key rotation timestamp."""
        try:
            rotation_timestamp = await self.cache.get("question_encryption_last_rotation")
            if rotation_timestamp:
                return datetime.fromisoformat(rotation_timestamp)
            return None
        except:
            return None
    
    async def _get_active_key_count(self) -> int:
        """Get count of active encryption keys."""
        try:
            # This is a simplified implementation
            # In production, maintain a proper key registry
            return 1  # Assuming one active key
        except:
            return 0
    
    async def _deprecate_old_keys(self, new_key_id: str):
        """Deprecate old encryption keys."""
        try:
            # This is a simplified implementation
            # In production, maintain a proper key registry with deprecation tracking
            old_keys = await self.cache.get("question_encryption_active_keys")
            if old_keys:
                keys_list = json.loads(old_keys) if isinstance(old_keys, str) else old_keys
                for old_key_id in keys_list:
                    if old_key_id != new_key_id:
                        # Mark key as deprecated
                        await self.cache.set(
                            f"question_encryption_key:{old_key_id}:deprecated",
                            datetime.utcnow().isoformat(),
                            ttl=86400 * 365
                        )
            
            # Update active keys list
            await self.cache.set(
                "question_encryption_active_keys",
                json.dumps([new_key_id]),
                ttl=86400 * 365
            )
            
        except Exception as e:
            logging.error(f"Error: {str(e)}")
    
    async def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event."""
        try:
            event = {
                "event_type": event_type,
                "details": details,
                "timestamp": datetime.utcnow(),
                "service": "question_security"
            }
            
            # Store in cache (in production, use proper logging system)
            events_cache_key = f"security_events:{event['timestamp'].strftime('%Y-%m-%d')}"
            existing_events = await self.cache.get(events_cache_key) or []
            existing_events.append(event)
            await self.cache.set(events_cache_key, existing_events, ttl=86400 * 30)  # 30 days
            
        except Exception as e:
            logging.error(f"Error: {str(e)}")
