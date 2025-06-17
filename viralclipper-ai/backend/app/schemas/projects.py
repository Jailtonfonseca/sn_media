from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Any
from datetime import datetime

# Manter Schemas de User aqui para referência se necessário, mas eles estão em users.py
# from .users import UserResponse

class ProjectBase(BaseModel):
    youtube_url: HttpUrl
    title_base: Optional[str] = Field("Untitled Project", max_length=255)
    description_base: Optional[str] = None
    hashtags_base: Optional[List[str]] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int # Poderia ser UserResponse se quisermos aninhar
    created_at: datetime
    status: str
    original_video_path: Optional[str] = None
    duracao_video_original_segundos: Optional[int] = None
    retention_data_json: Optional[Any] = None
    processing_error: Optional[str] = None
    # suggested_clips: List['SuggestedClipResponse'] = [] # Adicionar depois com forward ref

    class Config:
        orm_mode = True
        # from_attributes = True # Pydantic v2

from .clips import SuggestedClipResponse # Supondo que clips.py está no mesmo diretório
# ProjectResponse.update_forward_refs() # Para Pydantic v1 - update_forward_refs is deprecated
ProjectResponse.model_rebuild() # Para Pydantic v2
