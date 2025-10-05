import subprocess
import os
from pathlib import Path
from app.core.config import settings
from app.db import models
from sqlalchemy.orm import Session

def run_ffmpeg_command(command: list[str]):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"FFmpeg error: {stderr.decode('utf-8')}")
        print(f"FFmpeg output: {stdout.decode('utf-8')}")
    except FileNotFoundError:
        raise Exception("FFmpeg not found. Make sure it's installed and in PATH.")
    except Exception as e:
        raise e


def process_clip(clip_id: int, db: Session) -> str:
    clip = db.query(models.SuggestedClip).filter(models.SuggestedClip.id == clip_id).first()
    if not clip:
        raise ValueError(f"SuggestedClip with id {clip_id} not found.")

    try:
        clip.processing_status = "processing"
        db.commit()

        if not clip.project:
            raise ValueError(f"Project not found for clip id {clip_id}.")
        if not clip.project.original_video_path or not Path(clip.project.original_video_path).exists():
            raise ValueError(f"Original video for project {clip.project_id} not found at {clip.project.original_video_path}.")

        original_video_path = Path(clip.project.original_video_path)
        project_media_path = Path(settings.MEDIA_ROOT_PATH) / f"project_{clip.project_id}"
        clips_dir = project_media_path / "clips"
        clips_dir.mkdir(parents=True, exist_ok=True)

        processed_clip_filename = f"clip_{clip.id}.mp4"
        output_path = clips_dir / processed_clip_filename

        # If the processed file already exists, skip the expensive processing step.
        if output_path.exists():
            print(f"Clip {clip_id} output file already exists. Skipping processing.")
            clip.processed_clip_path = str(output_path)
            clip.processing_status = "processed"
            db.commit()
            return str(output_path)

        start_time = clip.timestamp_inicio_segundos
        end_time = clip.timestamp_fim_segundos
        duration = end_time - start_time

        if duration <= 0:
            raise ValueError("Clip duration must be positive.")

        # FFmpeg command for cutting and reformatting to 9:16 (center crop)
        target_w = 720
        target_h = 1280
        vf_opts = f"scale={target_w}:-2,crop={target_w}:{target_h}:(iw-{target_w})/2:(ih-{target_h})/2"

        ffmpeg_command = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', str(original_video_path),
            '-t', str(duration),
            '-vf', vf_opts,
            '-c:a', 'aac',
            '-strict', '-2',
            '-y',
            str(output_path)
        ]

        print(f"Running FFmpeg command: {' '.join(ffmpeg_command)}")
        run_ffmpeg_command(ffmpeg_command)

        clip.processed_clip_path = str(output_path)
        clip.processing_status = "processed"
        db.commit()
        return str(output_path)

    except Exception as e:
        clip.processing_status = "processing_failed"
        clip.processing_error_detail = str(e)
        db.commit()
        print(f"Error processing clip {clip_id}: {e}")
        raise
