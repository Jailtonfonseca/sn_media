from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class ScheduledPublicationBase(BaseModel):
    plataforma_destino: str = Field(..., examples=["youtube_shorts", "instagram_reels", "tiktok"])
    data_agendamento: datetime

class ScheduledPublicationCreate(ScheduledPublicationBase):
    suggested_clip_id: int

class ScheduledPublicationUpdate(BaseModel):
    data_agendamento: Optional[datetime] = None
    status_publicacao: Optional[str] = Field(None, examples=["pending", "publishing", "published", "failed"])

class ScheduledPublicationResponse(ScheduledPublicationBase):
    id: int
    suggested_clip_id: int
    status_publicacao: str
    id_publicacao_plataforma: Optional[str] = None
    metricas_desempenho_json: Optional[Any] = None
    publication_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        # from_attributes = True # Pydantic v2

# Adicionar ao final de clips.py para resolver forward reference
# from .publications import ScheduledPublicationResponse
# SuggestedClipResponse.model_rebuild() # Pydantic v2
# SuggestedClipResponse.update_forward_refs() # Pydantic v1
