from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db import models, database
from app.schemas import users as user_schemas
from app.schemas import common as common_schemas
from app.core import security
from app.core.config import settings
# Placeholder para lógica OAuth com Google
from urllib.parse import urlencode

router = APIRouter()

@router.post("/register", response_model=user_schemas.UserResponse)
def register_user(user_in: user_schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed_password = security.get_password_hash(user_in.password)
    db_user = models.User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=common_schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/google/connect", summary="Redirect to Google OAuth2 consent screen")
async def google_connect():
    # Este é um placeholder. A implementação real usaria uma biblioteca OAuth.
    # Construir a URL de autorização do Google
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile", # Adicionar escopos necessários
        "access_type": "offline", # Para obter refresh_token
        "prompt": "consent"
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    # Em uma aplicação real, você redirecionaria o usuário para esta URL.
    # from fastapi.responses import RedirectResponse
    # return RedirectResponse(auth_url)
    return {"message": "Simulating redirect to Google OAuth. In a real app, this would be a 307 redirect.", "auth_url": auth_url}


@router.get("/google/callback", summary="Callback endpoint for Google OAuth2")
async def google_callback(code: Optional[str] = None, error: Optional[str] = None, db: Session = Depends(database.get_db)):
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Google OAuth Error: {error}")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code from Google")

    # Placeholder: trocar código por token e buscar informações do usuário
    # Aqui você usaria httpx ou requests para fazer uma POST para o token endpoint do Google
    # e depois para o userinfo endpoint.
    # Exemplo de dados que você obteria (simulado):
    google_user_email = "user_from_google@example.com"
    google_user_id = "google_user_id_123"
    google_access_token = "mock_google_access_token"
    google_refresh_token = "mock_google_refresh_token" # Se scope 'offline' foi pedido

    user = db.query(models.User).filter(models.User.google_user_id == google_user_id).first()
    if not user:
        user = db.query(models.User).filter(models.User.email == google_user_email).first()
        if not user: # Novo usuário
            # Criar um usuário sem senha, pois a autenticação será via Google
            # Você pode gerar uma senha aleatória ou deixar o campo nullable
            # e ajustar a lógica de login para permitir login via Google sem senha local.
            user = models.User(
                email=google_user_email,
                google_user_id=google_user_id,
                google_auth_token=google_access_token,
                google_refresh_token=google_refresh_token,
                # hashed_password="", # Ou gere uma senha aleatória e improvável
                full_name="User From Google" # Obter nome do userinfo
            )
            db.add(user)
        else: # Usuário existente por email, vincular conta Google
            user.google_user_id = google_user_id
            user.google_auth_token = google_access_token
            user.google_refresh_token = google_refresh_token
    else: # Usuário já existe com este Google ID, atualizar tokens
        user.google_auth_token = google_access_token
        user.google_refresh_token = google_refresh_token

    db.commit()
    db.refresh(user)

    # Gerar um token JWT para o seu sistema
    access_token = security.create_access_token(data={"sub": str(user.id)})
    # Em uma aplicação real, você redirecionaria para o frontend com o token
    # return RedirectResponse(url=f"http://localhost:3000/auth/callback?token={access_token}")
    return {"message": "Google OAuth callback successful (simulated). Token generated.", "access_token": access_token, "token_type": "bearer"}

# Placeholder para uma rota protegida
@router.get("/users/me", response_model=user_schemas.UserResponse)
async def read_users_me(current_user_id: str = Depends(security.decode_access_token), db: Session = Depends(database.get_db)):
    if current_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = db.query(models.User).filter(models.User.id == int(current_user_id)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
