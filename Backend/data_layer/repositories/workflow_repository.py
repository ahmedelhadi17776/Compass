from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from Backend.data_layer.database.models.workflow import Workflow, WorkflowStatus
from Backend.data_layer.database.models.user import User
from Backend.data_layer.database.models.organization import Organization
from typing import List, Optional, Dict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload


class WorkflowRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_workflow(self, user_id: int = None, created_by: int = None, organization_id: int = None, **kwargs) -> Workflow:
        # Use either user_id or created_by, with user_id taking precedence
        created_by = user_id if user_id is not None else created_by
        if created_by is None:
            raise ValueError("Either user_id or created_by must be provided")
        if organization_id is None:
            raise ValueError("organization_id must be provided")

        try:
            # Verify that both user and organization exist
            result = await self.db_session.execute(
                select(User).where(User.id == created_by)
            )
            user = result.scalar_one_or_none()
            if user is None:
                raise ValueError(f"User with ID {created_by} does not exist")

            org_result = await self.db_session.execute(
                select(Organization).where(Organization.id == organization_id)
            )
            org = org_result.scalar_one_or_none()
            if org is None:
                raise ValueError(
                    f"Organization with ID {organization_id} does not exist")

            # Remove status from kwargs if it exists to avoid conflict with model default
            kwargs.pop('status', None)

            # Create the workflow with verified IDs
            workflow = Workflow(
                created_by=created_by,
                organization_id=organization_id,
                **kwargs
            )
            self.db_session.add(workflow)
            await self.db_session.flush()  # Flush to get the ID but don't commit yet
            await self.db_session.refresh(workflow)
            await self.db_session.commit()
            return workflow

        except IntegrityError as e:
            await self.db_session.rollback()
            raise ValueError(f"Failed to create workflow: {str(e)}")
        except Exception as e:
            await self.db_session.rollback()
            raise

    async def get_workflow(self, workflow_id: int, with_steps: bool = False) -> Optional[Workflow]:
        query = select(Workflow).where(Workflow.id == workflow_id)
        if with_steps:
            query = query.options(selectinload(Workflow.steps))
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def update_workflow_status(self, workflow_id: int, status: str) -> bool:
        try:
            stmt = update(Workflow).where(
                Workflow.id == workflow_id).values(status=status)
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db_session.rollback()
            raise

    async def get_user_workflows(self, user_id: int) -> List[Workflow]:
        result = await self.db_session.execute(
            select(Workflow)
            .where(Workflow.created_by == user_id)
            .options(selectinload(Workflow.steps))
        )
        return result.scalars().all()
