from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from src.utils.datetime_utils import utc_now
from ...data.database.models import User
from ...application.schemas.user import UserCreate, UserUpdate, UserPasswordChange
from ...data.database.connection import get_db
from ..authentication.auth_service import get_auth_service, AuthService

class UserManager:
    def __init__(self, db: Session, auth_service: AuthService):
        self.db = db
        self.auth_service = auth_service

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if username or email already exists
        if self.get_user_by_username_or_email(user_data.username, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )

        # Create new user
        hashed_password = self.auth_service.get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=f"{user_data.first_name} {user_data.last_name}".strip(),
            created_at=utc_now(),
            updated_at=utc_now()
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    def get_user_by_username_or_email(self, username: str, email: str) -> User:
        """Get user by username or email."""
        return self.db.query(User).filter(
            or_(User.username == username, User.email == email)
        ).first()

    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user information."""
        user = self.get_user_by_id(user_id)
        
        # Update user fields if provided
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.first_name is not None or user_data.last_name is not None:
            current_name = user.full_name.split(" ") if user.full_name else ["", ""]
            first_name = user_data.first_name or current_name[0]
            last_name = user_data.last_name or (current_name[1] if len(current_name) > 1 else "")
            user.full_name = f"{first_name} {last_name}".strip()
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        user.updated_at = utc_now()
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

    def change_password(self, user_id: int, password_data: UserPasswordChange) -> None:
        """Change user password."""
        user = self.get_user_by_id(user_id)
        
        # Verify current password
        if not self.auth_service.verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )
        
        # Update password
        user.hashed_password = self.auth_service.get_password_hash(password_data.new_password)
        user.updated_at = utc_now()
        
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

    def list_users(self, skip: int = 0, limit: int = 10) -> tuple[list[User], int]:
        """List users with pagination."""
        total = self.db.query(User).count()
        users = self.db.query(User).offset(skip).limit(limit).all()
        return users, total

    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        user = self.get_user_by_id(user_id)
        
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )

def get_user_manager(
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserManager:
    """Get UserManager instance."""
    return UserManager(db, auth_service)

db = next(get_db())
auth_service = get_auth_service(db)
user_manager = UserManager(db, auth_service)
