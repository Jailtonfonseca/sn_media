from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional # Adicionado Optional

from app.db import models, database
from app.schemas import clips as clip_schemas
from app.schemas import common as common_schemas # Para Msg de resposta
from app.core import security
from app.workers.tasks import process_video_clip_task # Importar a nova task

router = APIRouter()

# GET endpoint para listar clipes de um projeto
@router.get("/project/{project_id}", response_model=List[clip_schemas.SuggestedClipResponse])
def list_clips_for_project(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token)
):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project or project.owner_id != int(current_user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied")

    clips = db.query(models.SuggestedClip).filter(models.SuggestedClip.project_id == project_id).order_by(models.SuggestedClip.timestamp_inicio_segundos).all()
    return clips

# POST endpoint para aprovar e opcionalmente atualizar um clipe
@router.post("/{clip_id}/approve", response_model=clip_schemas.SuggestedClipResponse)
def approve_and_process_clip(
    clip_id: int,
    clip_update_data: Optional[clip_schemas.SuggestedClipUpdate] = None, # Dados para micro-ajustes
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token)
):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    clip = db.query(models.SuggestedClip).join(models.Project)        .filter(models.SuggestedClip.id == clip_id, models.Project.owner_id == int(current_user_id))        .first()

    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SuggestedClip not found or access denied")

    if clip_update_data:
        update_data = clip_update_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(clip, key, value)

    clip.status_aprovacao = "approved"
    # Resetar status de processamento caso já tenha sido processado e está sendo re-aprovado com mudanças
    clip.processing_status = "pending_approval_processing"
    clip.processed_clip_path = None
    clip.processing_error_detail = None

    db.commit()
    db.refresh(clip)

    # Disparar a tarefa de processamento do clipe
    process_video_clip_task.delay(clip.id)

    return clip

# NOVO endpoint para rejeitar um clipe
@router.post("/{clip_id}/reject", response_model=clip_schemas.SuggestedClipResponse) # Ou common_schemas.Msg
def reject_clip(
    clip_id: int,
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token)
):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    clip = db.query(models.SuggestedClip).join(models.Project)        .filter(models.SuggestedClip.id == clip_id, models.Project.owner_id == int(current_user_id))        .first()

    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SuggestedClip not found or access denied")

    clip.status_aprovacao = "rejected"
    # Opcional: limpar campos de processamento se foi aprovado e processado antes
    clip.processing_status = "skipped_rejected"
    # clip.processed_clip_path = None
    db.commit()
    db.refresh(clip)

    return clip # Retorna o clipe atualizado

# GET por ID (código existente)
@router.get("/{clip_id}", response_model=clip_schemas.SuggestedClipResponse)
def get_clip_details(
    clip_id: int,
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token)
):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    clip = db.query(models.SuggestedClip).join(models.Project)        .filter(models.SuggestedClip.id == clip_id, models.Project.owner_id == int(current_user_id))        .first()
    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found or access denied")
    return clip
