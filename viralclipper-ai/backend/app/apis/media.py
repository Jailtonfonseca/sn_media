from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.db import models, database
from app.core import security
from app.core.config import settings # Para MEDIA_ROOT_PATH

router = APIRouter()

@router.get("/projects/{project_id}/clips/{clip_filename}")
async def get_clip_media_file(
    project_id: int,
    clip_filename: str, # e.g., clip_123.mp4
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token)
):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Verificar se o usuário tem acesso ao projeto
    project = db.query(models.Project)        .filter(models.Project.id == project_id, models.Project.owner_id == int(current_user_id))        .first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied")

    # Validar o nome do arquivo para evitar Path Traversal
    if ".." in clip_filename or "/" in clip_filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename.")

    # Construir o caminho do arquivo
    # O processed_clip_path no DB já tem o caminho completo, mas aqui estamos construindo a partir do nome do arquivo
    # Isso é mais seguro se o `processed_clip_path` não for usado diretamente na URL.
    # O `clip_filename` deve corresponder ao que foi salvo.

    file_path = Path(settings.MEDIA_ROOT_PATH) / f"project_{project_id}" / "clips" / clip_filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip media file not found.")

    # Opcional: verificar se este filename pertence a um clip_id válido para este projeto
    # e se o clip_id corresponde ao filename.
    # Ex: clip_id_from_filename = clip_filename.split('_')[1].split('.')[0]
    # clip_db_check = db.query(models.SuggestedClip).filter_by(id=int(clip_id_from_filename), project_id=project_id).first()
    # if not clip_db_check or Path(clip_db_check.processed_clip_path).name != clip_filename:
    #    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip media inconsistency.")

    return FileResponse(path=str(file_path), media_type='video/mp4', filename=clip_filename)

# Similarmente para o vídeo original se necessário
@router.get("/projects/{project_id}/original/{original_video_filename}")
async def get_original_video_media_file(
    project_id: int,
    original_video_filename: str, # e.g., original_video.mp4
    db: Session = Depends(database.get_db),
    current_user_id: str = Depends(security.decode_access_token)
):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    project = db.query(models.Project)        .filter(models.Project.id == project_id, models.Project.owner_id == int(current_user_id))        .first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or access denied")

    if ".." in original_video_filename or "/" in original_video_filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename.")

    # O project.original_video_path já contém o caminho completo.
    # Podemos usar isso para verificar se o nome do arquivo corresponde.
    if not project.original_video_path or Path(project.original_video_path).name != original_video_filename:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original video filename mismatch or not found.")

    file_path = Path(project.original_video_path) # Usar o caminho do DB que é absoluto no container

    if not file_path.exists() or not file_path.is_file():
        # Isso pode indicar um problema se o DB diz que existe mas o arquivo não.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original video media file not found on disk.")

    return FileResponse(path=str(file_path), media_type='video/mp4', filename=original_video_filename)
