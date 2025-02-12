from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.rbac import require_role
from data_layer.database.connection import get_db
from data_layer.database.models.project import Project

router = APIRouter()

# ✅ Only "manager" role can create projects


@router.post("/projects/")
def create_project(name: str, description: str, db: Session = Depends(get_db), user=Depends(require_role("manager"))):
    new_project = Project(name=name, description=description)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return {"message": "Project created successfully"}
