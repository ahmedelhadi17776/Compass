import sys
import os
from datetime import datetime
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)

from Backend.data.database.models import User, Role, Permission, TaskStatus, TaskPriority, TaskCategory, Workflow, WorkflowStep, Task, TaskComment, TaskHistory, Base
from Backend.data.database.repositories.base_repository import BaseRepository
from Backend.data.database.repositories.auth_log_repository import AuthLogRepository
from Backend.data.database.repositories.user_repository import UserRepository

class TestDatabaseIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create an in-memory SQLite database for testing
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Create all tables
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        # Create a new session for each test
        self.session = self.TestingSessionLocal()
        
        # Clear all tables before each test
        for table in reversed(Base.metadata.sorted_tables):
            self.session.execute(table.delete())
        self.session.commit()

    def tearDown(self):
        # Close the session after each test
        self.session.close()

    @classmethod
    def tearDownClass(cls):
        # Drop all tables after all tests
        Base.metadata.drop_all(bind=cls.engine)

    def test_database_connection(self):
        """Test that we can connect to the database"""
        try:
            with self.engine.connect() as conn:
                self.assertTrue(conn.closed == False)
        except Exception as e:
            self.fail(f"Failed to connect to database: {str(e)}")

    def test_create_and_query_user(self):
        """Test user creation and querying"""
        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="testpass",
                full_name="Test User",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add and commit
            self.session.add(test_user)
            self.session.commit()
            
            # Query the user
            queried_user = self.session.query(User).filter_by(email="test@example.com").first()
            
            # Verify
            self.assertIsNotNone(queried_user)
            self.assertEqual(queried_user.username, "testuser")
            
            # Clean up
            self.session.delete(queried_user)
            self.session.commit()
            
        except Exception as e:
            self.fail(f"Failed to create and query user: {str(e)}")

    def test_relationships(self):
        """Test database relationships"""
        try:
            # Clean up any existing test data
            test_user = self.session.query(User).filter_by(email="test_rel@example.com").first()
            if test_user:
                self.session.delete(test_user)
                self.session.commit()

            test_role = self.session.query(Role).filter_by(name="test_role").first()
            if test_role:
                self.session.delete(test_role)
                self.session.commit()

            # Create a role first
            role = Role(
                name="test_role", 
                description="Test Role",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(role)
            self.session.commit()

            # Create permissions
            permission1 = Permission(
                name="create_task",
                description="Can create tasks",
                resource="task",
                action="create"
            )
            permission2 = Permission(
                name="edit_task",
                description="Can edit tasks",
                resource="task",
                action="edit"
            )
            self.session.add_all([permission1, permission2])
            self.session.commit()

            # Associate permissions with role
            role.permissions.extend([permission1, permission2])
            self.session.commit()

            # Create a user and associate with the role
            user = User(
                email="test_rel@example.com",
                username="testuser_rel",
                hashed_password="testpass",
                full_name="Test Relationship User",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            user.roles.append(role)
            self.session.add(user)
            self.session.commit()

            # Create task-related entities
            status = TaskStatus(name="In Progress", description="Task is being worked on")
            priority = TaskPriority(name="High", weight=3)
            category = TaskCategory(name="Development", description="Development tasks")
            self.session.add_all([status, priority, category])
            self.session.commit()

            # Create workflow
            workflow = Workflow(
                name="Test Workflow",
                description="Test workflow",
                is_active=True,
                created_by=user.id
            )
            self.session.add(workflow)
            self.session.commit()

            # Create workflow steps
            step1 = WorkflowStep(
                workflow_id=workflow.id,
                name="Step 1",
                description="First step",
                step_order=1,
                is_required=True,
                is_automated=False
            )
            step2 = WorkflowStep(
                workflow_id=workflow.id,
                name="Step 2",
                description="Second step",
                step_order=2,
                is_required=True,
                is_automated=True
            )
            self.session.add_all([step1, step2])
            self.session.commit()

            # Create task with all relationships
            task = Task(
                title="Test Task",
                description="Test Description",
                user_id=user.id,
                status_id=status.id,
                priority_id=priority.id,
                category_id=category.id,
                workflow_id=workflow.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(task)
            self.session.commit()

            # Create task comment and history
            comment = TaskComment(
                task_id=task.id,
                user_id=user.id,
                content="Test comment"
            )
            history = TaskHistory(
                task_id=task.id,
                user_id=user.id,
                change_type="comment_added",
                old_value=None,
                new_value={"comment": "Test comment"}
            )
            self.session.add_all([comment, history])
            self.session.commit()

            # Test the relationships
            queried_user = self.session.query(User).filter_by(email="test_rel@example.com").first()
            self.assertIsNotNone(queried_user)
            self.assertEqual(len(queried_user.roles), 1)
            self.assertEqual(queried_user.roles[0].name, "test_role")
            self.assertEqual(len(queried_user.roles[0].permissions), 2)

            queried_task = self.session.query(Task).filter_by(id=task.id).first()
            self.assertIsNotNone(queried_task)
            self.assertEqual(queried_task.status.name, "In Progress")
            self.assertEqual(queried_task.priority.name, "High")
            self.assertEqual(queried_task.category.name, "Development")
            self.assertEqual(queried_task.workflow.name, "Test Workflow")
            self.assertEqual(len(queried_task.comments), 1)
            self.assertEqual(len(queried_task.history), 1)

            # Clean up - delete in correct order to handle foreign key constraints
            self.session.delete(comment)
            self.session.delete(history)
            self.session.delete(task)
            self.session.delete(step1)
            self.session.delete(step2)
            self.session.delete(workflow)
            self.session.delete(status)
            self.session.delete(priority)
            self.session.delete(category)
            self.session.delete(user)
            self.session.delete(role)
            self.session.commit()

        except Exception as e:
            self.fail(f"Failed to test relationships: {str(e)}")

    def test_complete_auth_flow(self):
        """Test complete authentication flow"""
        try:
            # Register new user
            register_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123!",
                "full_name": "Test User"
            }
            user_repo = UserRepository(self.session)
            user_repo.register_user(register_data)
            self.session.commit()
            
            # Login with credentials
            login_data = {
                "username": register_data["username"],
                "password": register_data["password"]
            }
            user_repo = UserRepository(self.session)
            token = user_repo.login_user(login_data)
            self.assertIsNotNone(token)
            
            # Access protected endpoint
            user_repo = UserRepository(self.session)
            user = user_repo.get_user_by_token(token)
            self.assertIsNotNone(user)
            self.assertEqual(user.username, register_data["username"])
            self.assertEqual(user.email, register_data["email"])
            
            # Update user information
            update_data = {
                "full_name": "Updated Name",
                "email": "updated@example.com"
            }
            user_repo = UserRepository(self.session)
            user_repo.update_user(user.id, update_data)
            self.session.commit()
            
            user_repo = UserRepository(self.session)
            user = user_repo.get_user_by_id(user.id)
            self.assertEqual(user.full_name, update_data["full_name"])
            self.assertEqual(user.email, update_data["email"])
            
        except Exception as e:
            self.fail(f"Failed to test complete authentication flow: {str(e)}")

    def test_invalid_registration(self):
        """Test invalid registration"""
        try:
            # Test duplicate username
            user_data = {
                "username": "testuser",
                "email": "test1@example.com",
                "password": "TestPass123!",
                "full_name": "Test User"
            }
            user_repo = UserRepository(self.session)
            user_repo.register_user(user_data)
            self.session.commit()
            
            # Try registering with same username
            user_data["email"] = "test2@example.com"
            with self.assertRaises(Exception):
                user_repo.register_user(user_data)
                
        except Exception as e:
            self.fail(f"Failed to test invalid registration: {str(e)}")

    def test_invalid_login(self):
        """Test invalid login"""
        try:
            # Test login with non-existent user
            login_data = {
                "username": "nonexistent",
                "password": "wrongpass"
            }
            user_repo = UserRepository(self.session)
            with self.assertRaises(Exception):
                user_repo.login_user(login_data)
                
        except Exception as e:
            self.fail(f"Failed to test invalid login: {str(e)}")

    def test_invalid_token(self):
        """Test invalid token"""
        try:
            # Test accessing protected endpoint with invalid token
            user_repo = UserRepository(self.session)
            with self.assertRaises(Exception):
                user_repo.get_user_by_token("invalid_token")
                
        except Exception as e:
            self.fail(f"Failed to test invalid token: {str(e)}")

    def test_password_change(self):
        """Test password change"""
        try:
            # 1. Register and login
            user_data = {
                "username": "passuser",
                "email": "pass@example.com",
                "password": "OldPass123!",
                "full_name": "Password User"
            }
            user_repo = UserRepository(self.session)
            user_repo.register_user(user_data)
            self.session.commit()
            token = user_repo.login_user(user_data)
            
            # 2. Change password
            password_data = {
                "current_password": "OldPass123!",
                "new_password": "NewPass123!"
            }
            user_repo = UserRepository(self.session)
            user_repo.change_password(token, password_data)
            self.session.commit()
            
            # 3. Try logging in with new password
            login_data = {
                "username": user_data["username"],
                "password": "NewPass123!"
            }
            user_repo = UserRepository(self.session)
            user_repo.login_user(login_data)
            
        except Exception as e:
            self.fail(f"Failed to test password change: {str(e)}")

    def test_rate_limiting(self):
        """Test rate limiting"""
        try:
            # Attempt multiple rapid requests to trigger rate limiting
            for _ in range(70):  # More than our limit of 60 requests per minute
                user_repo = UserRepository(self.session)
                user_repo.login_user({
                    "username": "test",
                    "password": "test"
                })
            
            with self.assertRaises(Exception):
                user_repo.login_user({
                    "username": "test",
                    "password": "test"
                })
                
        except Exception as e:
            self.fail(f"Failed to test rate limiting: {str(e)}")

    def test_admin_access(self):
        """Test admin access"""
        try:
            # 1. Create admin user
            admin_data = {
                "username": "admin",
                "email": "admin@example.com",
                "password": "AdminPass123!",
                "full_name": "Admin User"
            }
            user_repo = UserRepository(self.session)
            user_repo.register_user(admin_data)
            self.session.commit()
            admin_token = user_repo.login_user(admin_data)
            
            # Set admin flag in database
            admin_user = self.session.query(User).filter(User.username == "admin").first()
            admin_user.is_admin = True
            self.session.commit()
            
            # 2. Create regular user
            user_data = {
                "username": "user",
                "email": "user@example.com",
                "password": "UserPass123!",
                "full_name": "Regular User"
            }
            user_repo = UserRepository(self.session)
            user_repo.register_user(user_data)
            self.session.commit()
            user_token = user_repo.login_user(user_data)
            
            # 3. Test admin access to user list
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            user_headers = {"Authorization": f"Bearer {user_token}"}

            # Admin should be able to list users
            user_repo = UserRepository(self.session)
            users = user_repo.get_all_users(admin_token)
            self.assertGreaterEqual(len(users), 2)  # Should see both admin and regular user

            # Regular user should not be able to list users
            with self.assertRaises(Exception):
                user_repo.get_all_users(user_token)
                
        except Exception as e:
            self.fail(f"Failed to test admin access: {str(e)}")

if __name__ == '__main__':
    unittest.main()
