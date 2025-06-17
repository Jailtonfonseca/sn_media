from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SuggestedClipBase(BaseModel):
    timestamp_inicio_segundos: int
    timestamp_fim_segundos: int
    score_viralidade_inicial: Optional[float] = None
    status_aprovacao: Optional[str] = Field("pending", examples=["pending", "approved", "rejected"])
    titulo_personalizado: Optional[str] = Field(None, max_length=255)
    descricao_personalizada: Optional[str] = None
    hashtags_personalizadas: Optional[List[str]] = None

class SuggestedClipCreate(SuggestedClipBase):
    project_id: int # Necessário ao criar diretamente via API, ou preenchido pelo sistema

class SuggestedClipUpdate(BaseModel): # Para o usuário atualizar/aprovar
    status_aprovacao: Optional[str] = Field(None, examples=["pending", "approved", "rejected"])
    timestamp_inicio_segundos: Optional[int] = None # Para micro-ajustes
    timestamp_fim_segundos: Optional[int] = None   # Para micro-ajustes
    titulo_personalizado: Optional[str] = Field(None, max_length=255)
    descricao_personalizada: Optional[str] = None
    hashtags_personalizadas: Optional[List[str]] = None

class SuggestedClipResponse(SuggestedClipBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    processed_clip_path: Optional[str] = None
    processing_status: Optional[str] = None
    # scheduled_publications: List['ScheduledPublicationResponse'] = [] # Adicionar depois

    class Config:
        orm_mode = True
        # from_attributes = True # Pydantic v2

from .publications import ScheduledPublicationResponse
# SuggestedClipResponse.update_forward_refs() # Para Pydantic v1 - update_forward_refs is deprecated
SuggestedClipResponse.model_rebuild() # Para Pydantic v2
