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
        downloaded_path, duration_seconds = download_video(youtube_url, project_id, db) # Capturar duração
        print(f"Video for project {project_id} downloaded to: {downloaded_path}, Duration: {duration_seconds}s")

        analyze_retention_task.delay(project_id, youtube_url, duration_seconds) # Passar duração

        return {"project_id": project_id, "status": "download_complete", "path": downloaded_path, "duration": duration_seconds}
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
        print(f"Video processing failed for clip {clip_id}: {e}")
        # O erro já é tratado e status atualizado em process_clip, mas podemos logar aqui também
        # self.retry(exc=e, countdown=300) # Retry com delay maior
        # Não precisa atualizar o status aqui pois process_clip já o faz
        # A sessão do DB é gerenciada dentro de process_clip em caso de erro lá.
        # Se o erro for antes de chamar process_clip ou um erro inesperado aqui:
        if db.is_active:
             clip_to_update = db.query(models.SuggestedClip).filter(models.SuggestedClip.id == clip_id).first()
             if clip_to_update and clip_to_update.processing_status != "processing_failed":
                  clip_to_update.processing_status = "task_level_processing_failed"
                  clip_to_update.processing_error_detail = str(e)
                  db.commit()
        raise # Re-raise para Celery marcar como falha
    finally:
        if db.is_active:
            db.close()

@celery_app.task(name="app.workers.tasks.publish_scheduled_video_task", bind=True, max_retries=1) # Menos retries para APIs externas
def publish_scheduled_video_task(self, publication_id: int):
    db = SessionLocal()
    try:
        print(f"Starting publication task for publication ID: {publication_id}")
        publisher_service = YouTubePublishingService(db_session=db)
        success = publisher_service.publish_short_to_youtube(publication_id)

        if success:
            print(f"Publication {publication_id} processed successfully by task.")
            return {"publication_id": publication_id, "status": "published_successfully_or_simulated"}
        else:
            # Erro já foi logado e status atualizado pelo service
            print(f"Publication {publication_id} failed or simulated failure by task.")
            # Não precisa re-raise se o service já trata o erro e status.
            # Mas para Celery marcar como falha, um erro precisa ser levantado.
            # Vamos assumir que o service atualiza o status, e a task só reporta.
            # Para que o Celery marque como falha, o service deve levantar exceção em caso de falha.
            # Por enquanto, o service.publish_short_to_youtube retorna bool.
            # Se queremos que o Celery mostre como falha, o service deve levantar exceção,
            # ou a task deve levantar uma com base no 'success'.
            publication = db.query(models.ScheduledPublication).filter(models.ScheduledPublication.id == publication_id).first()
            if publication and publication.status_publicacao == "failed":
                 raise Exception(f"Publication failed: {publication.publication_error or 'Unknown error'}")
            return {"publication_id": publication_id, "status": "publication_attempted_check_db_for_status"}

    except Exception as e:
        # Se o service levantar uma exceção não tratada por ele, ou se a task levantar uma.
        print(f"Unhandled error in publish_scheduled_video_task for publication {publication_id}: {e}")
        # Tentar atualizar o status se possível, mas pode já estar feito ou a sessão pode estar ruim.
        # publication = db.query(models.ScheduledPublication).filter(models.ScheduledPublication.id == publication_id).first()
        # if publication and publication.status_publicacao not in ["failed", "published"]:
        #    publication.status_publicacao = "failed"
        #    publication.publication_error = f"Task level error: {str(e)}"
        #    db.commit()
        raise # Re-raise para Celery
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
def analyze_retention_task(self, project_id: int, video_youtube_id_or_url: str, video_duration_seconds: Optional[int]): # Adicionar duração
    db = SessionLocal()
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        print(f"Project {project_id} not found for retention analysis.")
        return {"project_id": project_id, "status": "project_not_found"}
    try:
        print(f"Starting retention analysis for project {project_id}")
        project.status = "processing_retention"
        db.commit()

        analyzer = YouTubeAnalyzerService(video_id=video_youtube_id_or_url, project_id=project_id)
        # Usar a duração real se disponível para mock_data, caso contrário, o mock interno decide
        effective_duration = video_duration_seconds if video_duration_seconds else 600
        retention_data = analyzer.get_audience_retention_data() # Mock não usa a duração passada diretamente, mas poderia ser ajustado

        serializable_retention_data = [list(item) for item in retention_data]
        project.retention_data_json = json.loads(json.dumps(serializable_retention_data))

        detected_peaks_timestamps = analyzer.detect_retention_peaks(retention_data)
        print(f"Project {project_id} - Detected retention peaks (timestamps): {detected_peaks_timestamps}")

        # Deletar clipes sugeridos antigos, se houver, para esta nova análise
        db.query(models.SuggestedClip).filter(models.SuggestedClip.project_id == project_id).delete()
        db.commit()

        # Criar novas instâncias de SuggestedClip
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
