from src.data.database.connection import SessionLocal
from src.data.database.models import User, Task  # SQLAlchemy models
from src.services.authentication.auth_service import AuthService
from datetime import datetime, timedelta

def test_db():
    """Test database operations."""
    db = SessionLocal()
    auth_service = AuthService(db)
    
    try:
        # Test User Creation
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=auth_service.get_password_hash("testpassword"),
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print("Test user created successfully!")

        # Test User Query
        queried_user = db.query(User).filter(User.email == "test@example.com").first()
        print(f"Queried User: {queried_user.username}, {queried_user.email}")

        # Test Task Creation
        test_task = Task(
            title="Test Task",
            description="This is a test task",
            user_id=test_user.id,
            due_date=datetime.utcnow() + timedelta(days=1),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(test_task)
        db.commit()
        print("Test task created successfully!")

        # Test Task Query
        tasks = db.query(Task).filter(Task.user_id == test_user.id).all()
        print(f"Found {len(tasks)} tasks for test user")

        # Clean up test data
        db.delete(test_task)
        db.delete(test_user)
        db.commit()
        print("Test data cleaned up successfully!")

    except Exception as e:
        print(f"Error during database test: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_db()
