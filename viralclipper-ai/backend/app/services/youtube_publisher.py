import time
import random
from app.db import models
from sqlalchemy.orm import Session
from app.core.config import settings # Para GOOGLE_CLIENT_ID, etc.
# from google.oauth2.credentials import Credentials # Para uso real
# from googleapiclient.discovery import build # Para uso real
# from googleapiclient.http import MediaFileUpload # Para uso real

class YouTubePublishingService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def publish_short_to_youtube(self, publication_id: int) -> bool:
        publication = self.db.query(models.ScheduledPublication).filter(models.ScheduledPublication.id == publication_id).first()
        if not publication:
            print(f"Publication {publication_id} not found.")
            return False

        clip = publication.suggested_clip
        if not clip:
            publication.status_publicacao = "failed"
            publication.publication_error = "SuggestedClip not found."
            self.db.commit()
            return False

        project = clip.project
        if not project:
            publication.status_publicacao = "failed"
            publication.publication_error = "Project not found for clip."
            self.db.commit()
            return False

        user = project.owner
        if not user:
            publication.status_publicacao = "failed"
            publication.publication_error = "User (owner) not found for project."
            self.db.commit()
            return False

        if not clip.processed_clip_path:
            publication.status_publicacao = "failed"
            publication.publication_error = "Processed clip path is missing."
            self.db.commit()
            return False

        # Simulação de publicação
        print(f"Simulating YouTube Short publication for publication ID: {publication.id}")
        print(f"  User: {user.email}, Clip ID: {clip.id}, Path: {clip.processed_clip_path}")
        print(f"  Title: {clip.titulo_personalizado or project.title_base or 'My Awesome Short'}")
        print(f"  Description: {clip.descricao_personalizada or project.description_base or 'Check out this cool short!'}")
        print(f"  Hashtags: {clip.hashtags_personalizadas or project.hashtags_base or ['#short', '#viral']}" )

        publication.status_publicacao = "publishing"
        self.db.commit()

        # Simular tempo de upload e processamento da API
        time.sleep(random.randint(5, 15)) # Simula o tempo de upload

        # Simular sucesso ou falha
        if random.random() < 0.9: # 90% de chance de sucesso na simulação
            publication.status_publicacao = "published"
            publication.id_publicacao_plataforma = f"mock_youtube_id_{random.randint(10000, 99999)}"
            print(f"Mock publication successful for {publication.id}. YouTube ID: {publication.id_publicacao_plataforma}")
        else:
            publication.status_publicacao = "failed"
            publication.publication_error = "Simulated API error during YouTube upload."
            print(f"Mock publication failed for {publication.id}: {publication.publication_error}")

        self.db.commit()
        return publication.status_publicacao == "published"

        # ----- INÍCIO DA LÓGICA REAL (COMENTADA PARA MVP) -----
        # if not user.google_auth_token: # Ou melhor, verificar se o token é válido e tem os escopos
        #     publication.status_publicacao = "failed"
        #     publication.publication_error = "User not authenticated with Google or missing YouTube scopes."
        #     self.db.commit()
        #     return False
        #
        # try:
        #     credentials = Credentials(
        #         token=user.google_auth_token,
        #         refresh_token=user.google_refresh_token, # Essencial para obter novos access_tokens
        #         token_uri='https://oauth2.googleapis.com/token',
        #         client_id=settings.GOOGLE_CLIENT_ID,
        #         client_secret=settings.GOOGLE_CLIENT_SECRET,
        #         scopes=settings.YOUTUBE_API_SCOPES
        #     )
        #
        #     if credentials.expired and credentials.refresh_token:
        #         # Lidar com refresh do token aqui se necessário, ou assumir que o frontend/auth lida com isso
        #         # credentials.refresh(Request()) # Request de google.auth.transport.requests
        #         pass
        #
        #     youtube_service = build('youtube', 'v3', credentials=credentials)
        #
        #     video_title = clip.titulo_personalizado or project.title_base or f"Clip from {project.title_base}"
        #     video_description = clip.descricao_personalizada or project.description_base or "Uploaded by ViralClipper AI"
        #     video_tags = clip.hashtags_personalizadas or project.hashtags_base or []
        #
        #     media_body = MediaFileUpload(clip.processed_clip_path, chunksize=-1, resumable=True)
        #
        #     request_body = {
        #         'snippet': {
        #             'title': video_title,
        #             'description': video_description,
        #             'tags': video_tags,
        #             'categoryId': '22' # Exemplo: People & Blogs. Varia conforme o conteúdo.
        #         },
        #         'status': {
        #             'privacyStatus': 'private', # 'public', 'private', or 'unlisted'
        #             'selfDeclaredMadeForKids': False # Importante
        #         }
        #     }
        #
        #     response = youtube_service.videos().insert(
        #         part='snippet,status',
        #         body=request_body,
        #         media_body=media_body
        #     ).execute()
        #
        #     publication.status_publicacao = "published"
        #     publication.id_publicacao_plataforma = response.get('id')
        #     self.db.commit()
        #     return True
        #
        # except Exception as e:
        #     publication.status_publicacao = "failed"
        #     publication.publication_error = str(e)
        #     self.db.commit()
        #     print(f"Error publishing to YouTube for publication {publication.id}: {e}")
        #     return False
        # ----- FIM DA LÓGICA REAL -----
