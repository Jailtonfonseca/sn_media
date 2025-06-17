# ViralClipper AI

Este projeto visa construir um sistema automatizado para identificar clipes de alto engajamento em vídeos longos do YouTube e publicá-los em plataformas de vídeos curtos.

# ViralClipper AI (MVP)

Este projeto visa construir um sistema automatizado para identificar clipes de alto engajamento em vídeos longos do YouTube e publicá-los em plataformas de vídeos curtos. Esta é a implementação do Produto Mínimo Viável (MVP).

## Visão Geral da Arquitetura (MVP)

O sistema é uma aplicação web com:
- **Frontend**: (Placeholder no MVP) Interação do usuário.
- **Backend**: API Python (FastAPI) para gerenciar lógica de negócios, processamento de vídeo e interações com banco de dados.
- **Banco de Dados**: PostgreSQL para armazenar dados de usuários, projetos, clipes e agendamentos.
- **Fila de Tarefas**: Celery com RabbitMQ para processamento assíncrono de tarefas pesadas (download, análise, corte de vídeo, publicação).
- **Processamento de Vídeo**: FFmpeg para cortar e reformatar clipes.
- **Armazenamento de Mídia**: Arquivos de vídeo são armazenados localmente no volume Docker `media_data`.

## Tecnologias Principais (Backend MVP)

- Python 3.9+
- FastAPI: Para a API REST.
- SQLAlchemy: ORM para interagir com o PostgreSQL.
- Pydantic: Para validação de dados e schemas da API.
- Celery: Para tarefas assíncronas.
- RabbitMQ: Message broker para Celery.
- PostgreSQL: Banco de dados relacional.
- FFmpeg: Para processamento de vídeo.
- yt-dlp: Para download de vídeos do YouTube.
- Docker & Docker Compose: Para containerização e orquestração do ambiente de desenvolvimento.
- Pytest: Para testes unitários.

## Configuração e Execução do Ambiente de Desenvolvimento

1.  **Clone o repositório.**
    ```bash
    git clone <your-repo-url>
    cd viralclipper-ai
    ```
2.  **Variáveis de Ambiente (Backend):**
    *   No diretório `backend/`, copie `.env_example` para `backend/.env`.
        ```bash
        cp backend/.env_example backend/.env
        ```
    *   Revise `backend/.env` e ajuste as variáveis se necessário (as padrões devem funcionar para desenvolvimento local).
    *   **Importante para OAuth do Google (Pós-MVP):** Preencha `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` com suas credenciais do Google Cloud Console quando for implementar a integração real.

3.  **Execute com Docker Compose:**
    A partir do diretório raiz `viralclipper-ai/`:
    ```bash
    docker-compose up --build -d # O -d executa em modo detached
    ```
4.  **Acessando os Serviços:**
    *   Backend API: `http://localhost:8000`
    *   Documentação Interativa da API (Swagger): `http://localhost:8000/docs`
    *   Documentação Alternativa da API (ReDoc): `http://localhost:8000/redoc`
    *   RabbitMQ Management UI: `http://localhost:15672` (usuário/senha padrão: guest/guest ou user/password se configurado no docker-compose)
    *   PostgreSQL: Acessível na porta `5432` (para clientes como pgAdmin ou DBeaver).

5.  **Para parar os serviços:**
    ```bash
    docker-compose down
    ```

## Executando os Testes (Backend)

Os testes unitários usam Pytest. Para executá-los:

1.  Certifique-se de que os containers Docker estão em execução (especialmente o do backend).
2.  Execute os testes dentro do container do backend:
    ```bash
    docker-compose exec backend pytest app/tests/
    ```
    Ou, para incluir cobertura (se configurado no pytest.ini):
    ```bash
    docker-compose exec backend pytest app/tests/ --cov=app
    ```

## Resumo dos Endpoints da API (MVP)

Consulte a documentação interativa da API (Swagger UI) em `http://localhost:8000/docs` para detalhes completos sobre os endpoints, schemas de request/response e para testá-los diretamente do navegador.

Principais grupos de endpoints:
- `/api/v1/auth/`: Autenticação de usuários (registro, login, stubs OAuth).
- `/api/v1/projects/`: Gerenciamento de projetos de vídeo.
- `/api/v1/clips/`: Gerenciamento de clipes sugeridos (aprovação, rejeição).
- `/api/v1/publications/`: Agendamento de publicações de clipes.
- `/api/v1/media/`: Acesso a arquivos de mídia (vídeos originais e processados).

## Próximos Passos (Pós-MVP)

- Implementação completa do frontend.
- Integração real com APIs do YouTube (Analytics e Data API para upload).
- Integração com outras plataformas sociais (Instagram Reels, TikTok).
- Algoritmo de detecção de picos mais avançado (Filtros C e D).
- "Smart Crop" com detecção de objetos/rostos.
- Legendas automáticas.
- Loop de feedback com IA/ML para otimização.
- Scheduler robusto para publicações (ex: Celery Beat).
- Melhorias na segurança, escalabilidade e monitoramento para produção.
