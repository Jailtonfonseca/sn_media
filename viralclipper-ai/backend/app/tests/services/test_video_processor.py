import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess # Import subprocess here
from app.services.video_processor import process_clip, run_ffmpeg_command
from app.db.models import SuggestedClip, Project # Importar modelos
from sqlalchemy.orm import Session # Para type hinting

# Mock para a sessão do banco de dados e configurações
@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_settings_fixture(tmp_path): # tmp_path é uma fixture do pytest para criar dirs temporários
    media_root = tmp_path / "media"
    media_root.mkdir()
    settings_mock = MagicMock()
    settings_mock.MEDIA_ROOT_PATH = str(media_root)
    return settings_mock


@pytest.fixture
def mock_project(tmp_path):
    original_video_dir = tmp_path / "media" / "project_1" # Consistent with mock_settings_fixture
    original_video_dir.mkdir(parents=True, exist_ok=True)
    original_video_file = original_video_dir / "original_video.mp4"
    original_video_file.touch()

    project = Project(id=1, original_video_path=str(original_video_file))
    return project

@pytest.fixture
def mock_clip(mock_project): # Depends on mock_project
    clip = SuggestedClip(
        id=101,
        project_id=mock_project.id, # Use mock_project's id
        project=mock_project,
        timestamp_inicio_segundos=10,
        timestamp_fim_segundos=20,
        status_aprovacao="approved"
    )
    return clip

class TestVideoProcessor:

    @patch('app.services.video_processor.subprocess.Popen')
    @patch('app.services.video_processor.settings')
    def test_process_clip_success(self, mock_settings_import, mock_popen, mock_db_session, mock_clip, mock_project, tmp_path, mock_settings_fixture):
        # Configure the imported settings mock
        mock_settings_import.MEDIA_ROOT_PATH = mock_settings_fixture.MEDIA_ROOT_PATH

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'stdout', b'stderr')
        mock_popen.return_value = mock_process

        mock_db_session.query(SuggestedClip).filter(SuggestedClip.id == mock_clip.id).first.return_value = mock_clip

        output_path_str = process_clip(mock_clip.id, mock_db_session)

        mock_popen.assert_called_once()
        args, _ = mock_popen.call_args
        ffmpeg_command_args = args[0]

        assert 'ffmpeg' in ffmpeg_command_args
        assert str(mock_clip.project.original_video_path) in ffmpeg_command_args
        assert '-ss' in ffmpeg_command_args
        assert str(mock_clip.timestamp_inicio_segundos) in ffmpeg_command_args
        assert '-t' in ffmpeg_command_args
        assert str(mock_clip.timestamp_fim_segundos - mock_clip.timestamp_inicio_segundos) in ffmpeg_command_args

        expected_output_dir = Path(mock_settings_import.MEDIA_ROOT_PATH) / f"project_{mock_clip.project_id}" / "clips"
        expected_output_filename = f"clip_{mock_clip.id}.mp4"
        expected_output_path = expected_output_dir / expected_output_filename
        assert str(expected_output_path) in ffmpeg_command_args
        assert output_path_str == str(expected_output_path)

        assert mock_clip.processing_status == "processed"
        assert mock_clip.processed_clip_path == str(expected_output_path)
        assert mock_db_session.commit.call_count >= 2 # Initial 'processing', then 'processed'

    @patch('app.services.video_processor.subprocess.Popen')
    @patch('app.services.video_processor.settings')
    def test_process_clip_ffmpeg_error(self, mock_settings_import, mock_popen, mock_db_session, mock_clip, mock_settings_fixture):
        mock_settings_import.MEDIA_ROOT_PATH = mock_settings_fixture.MEDIA_ROOT_PATH

        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b'', b'ffmpeg error output')
        mock_popen.return_value = mock_process

        mock_db_session.query(SuggestedClip).filter(SuggestedClip.id == mock_clip.id).first.return_value = mock_clip

        with pytest.raises(Exception, match="FFmpeg error: ffmpeg error output"):
            process_clip(mock_clip.id, mock_db_session)

        assert mock_clip.processing_status == "processing_failed"
        assert "ffmpeg error output" in mock_clip.processing_error_detail
        assert mock_db_session.commit.call_count >= 2

    @patch('app.services.video_processor.settings')
    def test_process_clip_original_video_not_found(self, mock_settings_import, mock_db_session, mock_clip, tmp_path, mock_settings_fixture):
        mock_settings_import.MEDIA_ROOT_PATH = mock_settings_fixture.MEDIA_ROOT_PATH

        mock_clip.project.original_video_path = str(tmp_path / "non_existent_video.mp4")
        mock_db_session.query(SuggestedClip).filter(SuggestedClip.id == mock_clip.id).first.return_value = mock_clip

        with pytest.raises(ValueError, match="Original video for project"):
            process_clip(mock_clip.id, mock_db_session)

        # Status should be updated within process_clip before the error is re-raised
        assert mock_clip.processing_status == "processing_failed"
        assert mock_db_session.commit.call_count >= 1 # At least the 'processing' status update

    @patch('app.services.video_processor.subprocess.Popen')
    def test_run_ffmpeg_command_success(self, mock_popen):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'stdout', b'stderr')
        mock_popen.return_value = mock_process

        run_ffmpeg_command(['ffmpeg', '-i', 'input.mp4', 'output.mp4'])
        mock_popen.assert_called_once_with(['ffmpeg', '-i', 'input.mp4', 'output.mp4'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @patch('app.services.video_processor.subprocess.Popen')
    def test_run_ffmpeg_command_error(self, mock_popen):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b'', b'ffmpeg error')
        mock_popen.return_value = mock_process

        with pytest.raises(Exception, match="FFmpeg error: ffmpeg error"):
            run_ffmpeg_command(['ffmpeg', '-i', 'input.mp4', 'output.mp4'])
