# ViralClipper AI

ViralClipper AI is a smart tool designed to help content creators find the most engaging and "viral-worthy" moments in their long-form videos and automatically turn them into clips for social media platforms like TikTok, Instagram Reels, and YouTube Shorts.

## 🚀 Project Vision

The goal is to create a fully automated "content repurposing" pipeline. A creator provides a long video, and ViralClipper AI analyzes audience engagement, identifies the best moments, reformats them into vertical clips, adds smart captions, and schedules them for posting, all with minimal human intervention. This allows creators to maximize their reach and grow their audience efficiently.

## ✨ Core Features (MVP)

*   **YouTube Video Ingestion**: Start a new project by simply providing a YouTube video URL.
*   **Automated Download**: The system automatically downloads the source video for processing.
*   **Audience Retention Analysis**: Simulates analyzing YouTube's audience retention data to find where viewers are most engaged.
*   **Peak Detection**: Automatically identifies "peaks" in retention, suggesting them as potential viral clips.
*   **Clip Suggestion**: The suggested clips (timestamps) are saved and presented to the user for approval.
*   **Asynchronous Processing**: Uses a robust task queue (Celery) to handle heavy tasks like downloading and video processing without blocking the user interface.
*   **Manual Clip Approval**: Users can review the suggested clips and approve the ones they want to create.
*   **Automated Clip Generation**: Approved clips are automatically cut and formatted using FFmpeg.

## ⚙️ How It Works: The Workflow

The process begins when a user submits a YouTube URL. The backend then kicks off a series of asynchronous tasks to download, analyze, and process the video, suggesting the best clips for the user to approve.

![Video Processing Workflow](docs/workflow.md)

## 🏗️ System Architecture

The system is built on a modern, containerized architecture that separates concerns for scalability and maintainability. It includes a web-based frontend (placeholder), a FastAPI backend, a PostgreSQL database for data storage, and Celery workers for background processing.

![System Architecture Diagram](docs/architecture.md)

## 🛠️ Technologies

*   **Backend**: Python, FastAPI
*   **Database**: PostgreSQL
*   **Task Queue**: Celery, RabbitMQ
*   **Video Processing**: FFmpeg, yt-dlp
*   **Containerization**: Docker, Docker Compose
*   **Testing**: Pytest

## 🚀 Getting Started

### Prerequisites

*   Docker and Docker Compose installed on your machine.

### Setup and Execution

1.  **Clone the repository.**
    ```bash
    git clone <your-repo-url>
    cd viralclipper-ai
    ```

2.  **Set Up Environment Variables:**
    *   In the `backend/` directory, copy the example environment file:
        ```bash
        cp backend/.env_example backend/.env
        ```
    *   The default values in `backend/.env` are suitable for local development.

3.  **Launch the Application:**
    *   From the root `viralclipper-ai/` directory, run:
        ```bash
        docker-compose up --build -d
        ```
    *   The `-d` flag runs the containers in detached mode.

4.  **Accessing Services:**
    *   **Backend API**: `http://localhost:8000`
    *   **API Docs (Swagger UI)**: `http://localhost:8000/docs`
    *   **RabbitMQ Management**: `http://localhost:15672` (Default user: `guest`, pass: `guest`)

5.  **Stopping the Application:**
    ```bash
    docker-compose down
    ```

## 🧪 Running Tests

1.  Ensure the Docker containers are running (`docker-compose up -d`).
2.  Execute the tests inside the backend container:
    ```bash
    docker-compose exec backend pytest app/tests/
    ```

## 🗺️ API Endpoints

For a detailed overview of all API endpoints, schemas, and to interact with the API directly, please visit the Swagger documentation at `http://localhost:8000/docs`.

## 🛣️ Roadmap (Post-MVP)

*   **Full Frontend Implementation**: Build a user-friendly interface in React or Vue.
*   **Real YouTube API Integration**: Connect to the real YouTube Analytics API to use actual retention data.
*   **Multi-Platform Publishing**: Add integrations for TikTok, Instagram, and other platforms.
*   **Smart Crop & Reframing**: Automatically detect faces or subjects to keep them in the frame for vertical formats.
*   **Auto-Captioning**: Generate and burn subtitles into the video clips.
*   **AI-Powered Feedback Loop**: Use performance data from published clips to improve future clip suggestions.