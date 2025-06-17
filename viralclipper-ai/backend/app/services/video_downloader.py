import yt_dlp
import os
from pathlib import Path
from app.core.config import settings
from app.db import models
from sqlalchemy.orm import Session

def download_video(youtube_url: str, project_id: int, db: Session) -> tuple[str, int | None]: # Retornar path e duração
    project_media_path = Path(settings.MEDIA_ROOT_PATH) / f"project_{project_id}"
    project_media_path.mkdir(parents=True, exist_ok=True)

    filename_template = "original_video.%(ext)s"
    output_path_template = str(project_media_path / filename_template)

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path_template,
        'noplaylist': True,
        'quiet': True,
        'merge_output_format': 'mp4',
    }

    downloaded_file_path = None
    duration = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True)
            duration = info_dict.get('duration') # Extrair duração

            if 'filepath' in info_dict:
                 downloaded_file_path = info_dict['filepath']
            elif 'requested_downloads' in info_dict and                  len(info_dict['requested_downloads']) > 0 and                  'filepath' in info_dict['requested_downloads'][0]:
                 downloaded_file_path = info_dict['requested_downloads'][0]['filepath']
            else:
                # Fallback if filepath is not directly available
                for f_item in project_media_path.iterdir():
                    if f_item.stem == "original_video": # Check for the base name without extension
                        downloaded_file_path = str(f_item)
                        break
            if not downloaded_file_path or not Path(downloaded_file_path).exists():
                 raise Exception("Downloaded file not found after yt-dlp execution.")

        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if project:
            project.original_video_path = downloaded_file_path # Store relative path from MEDIA_ROOT or absolute? Storing absolute for now.
            if duration:
                project.duracao_video_original_segundos = int(duration)
            project.status = "downloaded"
            db.commit()
        return downloaded_file_path, (int(duration) if duration else None)
    except Exception as e:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if project:
            project.status = "download_failed"
            project.processing_error = str(e)
            db.commit()
        print(f"Error downloading video for project {project_id}: {e}")
        raise
