# Modelos SQLAlchemy serão definidos aqui posteriormente
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float, Boolean # Adicionar Float, Boolean
from sqlalchemy.orm import relationship # Adicionar relationship
from .database import Base
from datetime import datetime # Adicionar datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Campos para Google OAuth
    google_user_id = Column(String, unique=True, index=True, nullable=True)
    google_auth_token = Column(Text, nullable=True) # Para armazenar access_token
    google_refresh_token = Column(Text, nullable=True) # Para armazenar refresh_token

    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    title_base = Column(String, index=True)
    # Novos campos para Project
    description_base = Column(Text, nullable=True)
    hashtags_base = Column(JSON, nullable=True) # Armazenar como lista de strings
    duracao_video_original_segundos = Column(Integer, nullable=True)

    youtube_url = Column(String, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending_download")
    original_video_path = Column(String, nullable=True)
    retention_data_json = Column(JSON, nullable=True)
    processing_error = Column(Text, nullable=True)

    owner = relationship("User", back_populates="projects")
    suggested_clips = relationship("SuggestedClip", back_populates="project", cascade="all, delete-orphan")

class SuggestedClip(Base):
    __tablename__ = "suggested_clips"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    timestamp_inicio_segundos = Column(Integer, nullable=False)
    timestamp_fim_segundos = Column(Integer, nullable=False)
    score_viralidade_inicial = Column(Float, nullable=True) # Pode ser calculado no futuro

    # Status de aprovação pelo usuário
    status_aprovacao = Column(String, default="pending") # pending, approved, rejected

    # Campos personalizáveis pelo usuário
    titulo_personalizado = Column(String, nullable=True)
    descricao_personalizada = Column(Text, nullable=True)
    hashtags_personalizadas = Column(JSON, nullable=True) # Lista de strings

    # Caminho para o arquivo de vídeo do clipe cortado (após processamento)
    processed_clip_path = Column(String, nullable=True)
    processing_status = Column(String, nullable=True) # ex: pending_processing, processing, processed, processing_failed
    processing_error_detail = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="suggested_clips")
    scheduled_publications = relationship("ScheduledPublication", back_populates="suggested_clip", cascade="all, delete-orphan")


class ScheduledPublication(Base):
    __tablename__ = "scheduled_publications"
    id = Column(Integer, primary_key=True, index=True)
    suggested_clip_id = Column(Integer, ForeignKey("suggested_clips.id"), nullable=False)

    plataforma_destino = Column(String, nullable=False) # "youtube_shorts", "instagram_reels", "tiktok"
    data_agendamento = Column(DateTime, nullable=False)

    status_publicacao = Column(String, default="pending") # pending, publishing, published, failed
    id_publicacao_plataforma = Column(String, nullable=True) # ID do post na plataforma social
    metricas_desempenho_json = Column(JSON, nullable=True) # Para buscar depois
    publication_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    suggested_clip = relationship("SuggestedClip", back_populates="scheduled_publications")
