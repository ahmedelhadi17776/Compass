"""Password management module."""
import re
from typing import Optional, Tuple
from passlib.context import CryptContext
from .constants import MIN_PASSWORD_LENGTH, PASSWORD_SPECIAL_CHARS
from .exceptions import WeakPasswordError

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class PasswordManager:
    """Password management service."""

    def __init__(self):
        self.pwd_context = pwd_context

    def hash_password(self, password: str) -> str:
        """Hash a password using Argon2."""
        self._validate_password(password)
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def _validate_password(self, password: str) -> None:
        """Validate password strength."""
        errors = []

        if len(password) < MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {
                          MIN_PASSWORD_LENGTH} characters long")

        if not re.search(r'[A-Z]', password):
            errors.append(
                "Password must contain at least one uppercase letter")

        if not re.search(r'[a-z]', password):
            errors.append(
                "Password must contain at least one lowercase letter")

        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")

        if not any(char in PASSWORD_SPECIAL_CHARS for char in password):
            errors.append(f"Password must contain at least one special character ({
                          PASSWORD_SPECIAL_CHARS})")

        if errors:
            raise WeakPasswordError("\n".join(errors))

    def password_strength_check(self, password: str) -> Tuple[int, list[str]]:
        """Check password strength and return score and suggestions."""
        score = 0
        suggestions = []

        # Length check
        length_score = min(len(password) // 4, 5)
        score += length_score
        if length_score < 3:
            suggestions.append("Consider using a longer password")

        # Character variety checks
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            suggestions.append("Add uppercase letters")

        if re.search(r'[a-z]', password):
            score += 1
        else:
            suggestions.append("Add lowercase letters")

        if re.search(r'\d', password):
            score += 1
        else:
            suggestions.append("Add numbers")

        special_chars = sum(
            1 for char in password if char in PASSWORD_SPECIAL_CHARS)
        score += min(special_chars, 2)
        if special_chars == 0:
            suggestions.append("Add special characters")

        # Check for common patterns
        if re.search(r'(.)\1{2,}', password):  # Repeated characters
            score -= 1
            suggestions.append("Avoid repeated characters")

        if re.search(r'(123|abc|qwerty)', password.lower()):
            score -= 1
            suggestions.append("Avoid common patterns")

        return max(0, min(score, 10)), suggestions
