from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List # Adicionar List
from app.db import models, database
from app.schemas import projects as project_schemas
from app.core import security
from app.workers.tasks import download_youtube_video_task

router = APIRouter()

# POST /api/v1/projects/ - Criar novo projeto (Existente)
@router.post("/", response_model=project_schemas.ProjectResponse, status_code=status.HTTP_202_ACCEPTED)
def create_project(
    project_in: project_schemas.ProjectCreate,
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token)
):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = db.query(models.User).filter(models.User.id == int(current_user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_project = models.Project(
        youtube_url=str(project_in.youtube_url),
        title_base=project_in.title_base,
        description_base=project_in.description_base, # Novo
        hashtags_base=project_in.hashtags_base,       # Novo
        owner_id=user.id,
        status="pending_download"
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    download_youtube_video_task.delay(db_project.id, str(db_project.youtube_url))
    return db_project

# NOVO: GET /api/v1/projects/ - Listar todos os projetos do usuário
@router.get("/", response_model=List[project_schemas.ProjectResponse])
def list_user_projects(
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token),
    skip: int = 0, # Adicionar paginação básica
    limit: int = 100 # Adicionar paginação básica
):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    projects = db.query(models.Project)        .filter(models.Project.owner_id == int(current_user_id))        .order_by(models.Project.created_at.desc())        .offset(skip)        .limit(limit)        .all()
    return projects

# GET /api/v1/projects/{project_id} - Detalhes de um projeto (Existente)
@router.get("/{project_id}", response_model=project_schemas.ProjectResponse)
def get_project_details(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token)
):
    # ... (código existente) ...
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == int(current_user_id)).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or not owned by user")
    return project
