"""
Signup verification service for generating, storing, and validating verification codes
"""
import secrets
import string
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from core.config import settings
from core.security.password import get_password_hash, verify_password
from models.verification_code import VerificationCode
from models.user import User

logger = logging.getLogger(__name__)


class SignupVerificationService:
    """Service for managing signup verification codes"""

    @staticmethod
    def generate_code(length: Optional[int] = None) -> str:
        """
        Generate a random verification code

        Args:
            length: Length of the code (defaults to settings.VERIFICATION_CODE_LENGTH)

        Returns:
            Random alphanumeric code (uppercase)
        """
        length = length or settings.VERIFICATION_CODE_LENGTH
        alphabet = string.ascii_uppercase + string.digits
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        return code

    @staticmethod
    def hash_code(code: str) -> str:
        """
        Hash a verification code using bcrypt

        Args:
            code: Plain text verification code

        Returns:
            Hashed code
        """
        return get_password_hash(code)

    @staticmethod
    def verify_code_hash(plain_code: str, hashed_code: str) -> bool:
        """
        Verify a plain code against its hash

        Args:
            plain_code: Plain text verification code
            hashed_code: Hashed verification code

        Returns:
            True if code matches, False otherwise
        """
        return verify_password(plain_code, hashed_code)

    @staticmethod
    def create_verification_code(
        db: Session,
        user_id: uuid.UUID,
        purpose: str = "signup",
    ) -> tuple[VerificationCode, str]:
        """
        Create a new verification code for a user

        This will:
        1. Invalidate any previous active codes for the same user/purpose
        2. Generate a new random code
        3. Hash and store it in the database

        Args:
            db: Database session
            user_id: User ID
            purpose: Purpose of the code (default: "signup")

        Returns:
            Tuple of (VerificationCode model, plain_code string)
        """
        # Invalidate previous active codes
        db.query(VerificationCode).filter(
            and_(
                VerificationCode.user_id == user_id,
                VerificationCode.purpose == purpose,
                VerificationCode.consumed_at.is_(None),
            )
        ).update({"consumed_at": datetime.utcnow()})

        # Generate new code
        plain_code = SignupVerificationService.generate_code()
        code_hash = SignupVerificationService.hash_code(plain_code)

        # Calculate expiry time
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES
        )

        # Create verification code record
        verification_code = VerificationCode(
            user_id=user_id,
            code_hash=code_hash,
            purpose=purpose,
            expires_at=expires_at,
        )

        db.add(verification_code)
        db.commit()
        db.refresh(verification_code)

        logger.info(
            f"Verification code created",
            extra={
                "user_id": str(user_id),
                "purpose": purpose,
                "expires_at": expires_at.isoformat(),
            }
        )

        return verification_code, plain_code

    @staticmethod
    def validate_and_consume_code(
        db: Session,
        user_id: uuid.UUID,
        plain_code: str,
        purpose: str = "signup",
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a verification code and mark it as consumed

        Args:
            db: Database session
            user_id: User ID
            plain_code: Plain text verification code to validate
            purpose: Purpose of the code (default: "signup")

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        # Find the most recent active code for this user/purpose
        verification_code = (
            db.query(VerificationCode)
            .filter(
                and_(
                    VerificationCode.user_id == user_id,
                    VerificationCode.purpose == purpose,
                    VerificationCode.consumed_at.is_(None),
                )
            )
            .order_by(VerificationCode.created_at.desc())
            .first()
        )

        if not verification_code:
            logger.warning(
                f"No active verification code found",
                extra={"user_id": str(user_id), "purpose": purpose}
            )
            return False, "Invalid or expired verification code"

        # Check if expired
        if datetime.utcnow() > verification_code.expires_at:
            logger.warning(
                f"Verification code expired",
                extra={
                    "user_id": str(user_id),
                    "purpose": purpose,
                    "expires_at": verification_code.expires_at.isoformat(),
                }
            )
            return False, "Verification code has expired"

        # Verify code hash
        if not SignupVerificationService.verify_code_hash(plain_code, verification_code.code_hash):
            logger.warning(
                f"Invalid verification code provided",
                extra={"user_id": str(user_id), "purpose": purpose}
            )
            return False, "Invalid verification code"

        # Mark as consumed
        verification_code.consumed_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"Verification code validated and consumed",
            extra={
                "user_id": str(user_id),
                "purpose": purpose,
                "code_id": str(verification_code.id),
            }
        )

        return True, None

    @staticmethod
    def mark_user_verified(db: Session, user_id: uuid.UUID) -> bool:
        """
        Mark a user as verified (if using is_verified field)

        Args:
            db: Database session
            user_id: User ID

        Returns:
            True if user was found and updated, False otherwise
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Note: The current User model doesn't have is_verified field
        # This is a placeholder for future implementation
        # When adding is_verified field to User model, uncomment:
        # user.is_verified = True
        # db.commit()

        logger.info(f"User marked as verified", extra={"user_id": str(user_id)})
        return True
