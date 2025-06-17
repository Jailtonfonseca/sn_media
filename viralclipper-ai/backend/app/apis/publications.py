from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db import models, database
from app.schemas import publications as publication_schemas
from app.schemas import common as common_schemas # Import for Msg
from app.core import security
from app.workers.tasks import publish_scheduled_video_task # Adicionar
from datetime import datetime # Já deve estar lá

router = APIRouter()

@router.post("/schedule", response_model=publication_schemas.ScheduledPublicationResponse, status_code=status.HTTP_201_CREATED)
def schedule_clip_publication(
    publication_in: publication_schemas.ScheduledPublicationCreate,
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token)
):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Verificar se o clipe existe e pertence ao usuário e está aprovado e processado
    clip = db.query(models.SuggestedClip).join(models.Project)        .filter(models.SuggestedClip.id == publication_in.suggested_clip_id,                 models.Project.owner_id == int(current_user_id))        .first()

    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SuggestedClip not found or access denied.")

    if clip.status_aprovacao != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Clip is not approved.")

    if clip.processing_status != "processed" or not clip.processed_clip_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Clip is not processed or processed file path is missing.")

    # Verificar se já existe um agendamento para este clipe e plataforma na mesma data (opcional)
    # existing_schedule = db.query(models.ScheduledPublication).filter_by(
    #    suggested_clip_id=publication_in.suggested_clip_id,
    #    plataforma_destino=publication_in.plataforma_destino,
    #    data_agendamento=publication_in.data_agendamento
    # ).first()
    # if existing_schedule:
    #    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This clip is already scheduled for this platform at this time.")

    db_publication = models.ScheduledPublication(
        suggested_clip_id=publication_in.suggested_clip_id,
        plataforma_destino=publication_in.plataforma_destino,
        data_agendamento=publication_in.data_agendamento,
        status_publicacao="pending" # Status inicial
    )
    db.add(db_publication)
    db.commit()
    db.refresh(db_publication)

    # Disparar a tarefa de publicação (simulação no MVP ignora data_agendamento real)
    print(f"MVP: Triggering immediate (simulated) publication for publication ID: {db_publication.id}")
    publish_scheduled_video_task.delay(db_publication.id)

    return db_publication

@router.get("/clip/{clip_id}", response_model=List[publication_schemas.ScheduledPublicationResponse])
def list_schedules_for_clip(
    clip_id: int,
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token)
):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Verificar se o clipe pertence ao usuário
    clip_check = db.query(models.SuggestedClip).join(models.Project)        .filter(models.SuggestedClip.id == clip_id, models.Project.owner_id == int(current_user_id))        .first()
    if not clip_check:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found or access denied")

    schedules = db.query(models.ScheduledPublication)        .filter(models.ScheduledPublication.suggested_clip_id == clip_id)        .order_by(models.ScheduledPublication.data_agendamento)        .all()
    return schedules

@router.get("/project/{project_id}", response_model=List[publication_schemas.ScheduledPublicationResponse])
def list_schedules_for_project(
    project_id: int,
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token)
):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    project_check = db.query(models.Project)        .filter(models.Project.id == project_id, models.Project.owner_id == int(current_user_id))        .first()
    if not project_check:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied")

    schedules = db.query(models.ScheduledPublication)        .join(models.SuggestedClip)        .filter(models.SuggestedClip.project_id == project_id)        .order_by(models.ScheduledPublication.data_agendamento)        .all()
    return schedules

@router.delete("/{publication_id}", response_model=common_schemas.Msg)
def delete_scheduled_publication(
    publication_id: int,
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token)
):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    publication = db.query(models.ScheduledPublication)        .join(models.SuggestedClip).join(models.Project)        .filter(models.ScheduledPublication.id == publication_id, models.Project.owner_id == int(current_user_id))        .first()

    if not publication:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled publication not found or access denied")

    if publication.status_publicacao == "published" or publication.status_publicacao == "publishing":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete a publication that is already published or currently publishing.")

    db.delete(publication)
    db.commit()
    return {"message": "Scheduled publication deleted successfully"}
