from fastapi import FastAPI
from app.core.config import settings
from app.apis import auth as auth_router
from app.apis import projects as project_router
from app.apis import clips as clips_router
from app.apis import publications as publications_router # Adicionar
from app.apis import media as media_router # Adicionar
from app.db.database import engine, Base

# Criar tabelas do banco de dados (apenas para desenvolvimento/teste inicial)
# Em produção, usar Alembic para migrações
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.get("/")
async def root():
    return {"message": "ViralClipper AI Backend is running!"}

# Incluir routers
app.include_router(auth_router.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(project_router.router, prefix=f"{settings.API_V1_STR}/projects", tags=["projects"])
app.include_router(clips_router.router, prefix=f"{settings.API_V1_STR}/clips", tags=["clips"])
app.include_router(publications_router.router, prefix=f"{settings.API_V1_STR}/publications", tags=["publications"]) # Adicionar
app.include_router(media_router.router, prefix=f"{settings.API_V1_STR}/media", tags=["media"]) # Adicionar

# Outros routers serão adicionados aqui
