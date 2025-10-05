from celery import Celery
from typing import Optional # Add Optional
from app.core.config import settings
from app.db.database import SessionLocal
from app.db import models # Import models
from app.services.video_downloader import download_video
from app.services.youtube_analyzer import YouTubeAnalyzerService
from app.services.video_processor import process_clip
from app.services.youtube_publisher import YouTubePublishingService # Adicionar
import json

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="app.workers.tasks.download_youtube_video_task", bind=True, max_retries=3)
def download_youtube_video_task(self, project_id: int, youtube_url: str):
    db = SessionLocal()
    try:
        print(f"Starting download for project {project_id}, URL: {youtube_url}")
        downloaded_path, duration_seconds = download_video(youtube_url, project_id, db)
        print(f"Video for project {project_id} downloaded to: {downloaded_path}, Duration: {duration_seconds}s")

        # Return data for the next task in the chain
        return {
            "project_id": project_id,
            "youtube_url": youtube_url,
            "duration_seconds": duration_seconds
        }
    except Exception as e:
        print(f"Download failed for project {project_id}: {e}")
        # self.retry(exc=e, countdown=60) # Example of retry
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if project:
            project.status = "download_failed"
            project.processing_error = str(e)
            db.commit()
        raise
    finally:
        db.close()

@celery_app.task(name="app.workers.tasks.process_video_clip_task", bind=True, max_retries=2) # Menos retries para tasks pesadas
def process_video_clip_task(self, clip_id: int):
    db = SessionLocal()
    clip = db.query(models.SuggestedClip).filter(models.SuggestedClip.id == clip_id).first()
    if not clip:
        print(f"Clip {clip_id} not found for processing.")
        db.close() # Close session
        return {"clip_id": clip_id, "status": "clip_not_found"}

    # Só processar se aprovado
    if clip.status_aprovacao != "approved":
        print(f"Clip {clip_id} is not approved. Current status: {clip.status_aprovacao}. Skipping processing.")
        clip.processing_status = "skipped_not_approved"
        db.commit()
        db.close()
        return {"clip_id": clip_id, "status": "skipped_not_approved"}

    try:
        print(f"Starting video processing for clip {clip_id}")
        clip.processing_status = "processing_queued" # Ou diretamente "processing"
        db.commit() # Commit status antes de chamar a função síncrona longa

        processed_path = process_clip(clip_id, db) # process_clip já faz commits de status interno

        print(f"Clip {clip_id} processed successfully. Output: {processed_path}")
        return {"clip_id": clip_id, "status": "processing_complete", "path": processed_path}
    except Exception as e:
        # The underlying process_clip service is responsible for setting the 'processing_failed' status in the DB.
        # This task's responsibility is to log the failure and re-raise the exception so Celery marks it as FAILED.
        print(f"Video processing task failed for clip {clip_id}: {e}")
        raise # Re-raise to ensure Celery marks the task as FAILED.
    finally:
        if db.is_active:
            db.close()

@celery_app.task(name="app.workers.tasks.publish_scheduled_video_task", bind=True, max_retries=1)
def publish_scheduled_video_task(self, publication_id: int):
    db = SessionLocal()
    try:
        print(f"Starting publication task for publication ID: {publication_id}")
        publisher_service = YouTubePublishingService(db_session=db)
        success = publisher_service.publish_short_to_youtube(publication_id)

        if success:
            print(f"Publication {publication_id} processed successfully by task.")
            return {"publication_id": publication_id, "status": "published"}
        else:
            # The service handles updating the DB status to 'failed'.
            # We raise an exception to ensure the Celery task is marked as FAILED for monitoring.
            publication = db.query(models.ScheduledPublication).filter(models.ScheduledPublication.id == publication_id).first()
            error_message = f"Publication {publication_id} failed as indicated by the publishing service."
            if publication and publication.publication_error:
                error_message += f" Reason: {publication.publication_error}"
            raise Exception(error_message)

    except Exception as e:
        # The service or the logic above should handle DB state.
        # We just log and re-raise to ensure Celery marks the task as failed.
        print(f"Error in publish_scheduled_video_task for publication {publication_id}: {e}")
        raise
    finally:
        db.close()

# Opcional: Tarefa periódica para verificar agendamentos (adiada para pós-MVP)
# @celery_app.task(name="app.workers.tasks.check_scheduled_publications_task")
# def check_scheduled_publications_task():
#     db = SessionLocal()
#     now = datetime.utcnow()
#     due_publications = db.query(models.ScheduledPublication).filter(
#         models.ScheduledPublication.data_agendamento <= now,
#         models.ScheduledPublication.status_publicacao == "pending"
#     ).all()
#
#     for pub in due_publications:
#         print(f"Found due publication: {pub.id}, dispatching publish_scheduled_video_task.")
#         publish_scheduled_video_task.delay(pub.id)
#     db.close()
#     return {"due_publications_found": len(due_publications)}

@celery_app.task(name="app.workers.tasks.analyze_retention_task", bind=True, max_retries=3)
def analyze_retention_task(self, download_result: dict):
    project_id = download_result["project_id"]
    youtube_url = download_result["youtube_url"]
    duration_seconds = download_result["duration_seconds"]

    db = SessionLocal()
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        print(f"Project {project_id} not found for retention analysis.")
        return {"project_id": project_id, "status": "project_not_found"}
    try:
        print(f"Starting retention analysis for project {project_id}")
        project.status = "processing_retention"
        db.commit()

        analyzer = YouTubeAnalyzerService(video_id=youtube_url, project_id=project_id)
        retention_data = analyzer.get_audience_retention_data()

        serializable_retention_data = [list(item) for item in retention_data]
        project.retention_data_json = json.loads(json.dumps(serializable_retention_data))

        detected_peaks_timestamps = analyzer.detect_retention_peaks(retention_data)
        print(f"Project {project_id} - Detected retention peaks (timestamps): {detected_peaks_timestamps}")

        # Delete only old clips that are still pending approval.
        # This preserves clips that have been approved or rejected by the user.
        db.query(models.SuggestedClip).filter(
            models.SuggestedClip.project_id == project_id,
            models.SuggestedClip.status_aprovacao == 'pending_approval'
        ).delete(synchronize_session=False)
        db.commit()

        # Create new instances of SuggestedClip
        for start_time, end_time in detected_peaks_timestamps:
            # Aplicar filtros básicos de duração do clipe aqui (Ex: Passo C do briefing)
            clip_duration = end_time - start_time
            if not (10 <= clip_duration <= 180): # Ex: clipes entre 10s e 3 minutos
                print(f"Skipping peak ({start_time}-{end_time}) for project {project_id} due to duration: {clip_duration}s")
                continue

            suggested_clip = models.SuggestedClip(
                project_id=project_id,
                timestamp_inicio_segundos=start_time,
                timestamp_fim_segundos=end_time,
                # score_viralidade_inicial pode ser preenchido aqui se o algoritmo o calcular
            )
            db.add(suggested_clip)

        project.status = "retention_analyzed"
        db.commit()

        # TODO: Próximo passo seria disparar uma tarefa para gerar os clipes com base nesses picos.
        # Se houver clipes sugeridos, pode-se mudar status para "clips_suggested"
        if db.query(models.SuggestedClip).filter(models.SuggestedClip.project_id == project_id).count() > 0:
            project.status = "clips_suggested" # Novo status
            db.commit()


        return {"project_id": project_id, "status": project.status, "peaks_found": len(detected_peaks_timestamps)}
    except Exception as e:
        print(f"Retention analysis failed for project {project_id}: {e}")
        if project:
            project.status = "retention_analysis_failed"
            project.processing_error = str(e)
            db.commit()
        raise
    finally:
        db.close()
