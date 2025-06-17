import pytest
from app.services.youtube_analyzer import YouTubeAnalyzerService, get_mock_audience_retention

class TestYouTubeAnalyzerService:

    @pytest.fixture
    def analyzer(self):
        return YouTubeAnalyzerService(video_id="test_video", project_id=1)

    def test_get_audience_retention_data_mock(self, analyzer):
        # Testa se a função mock retorna algo no formato esperado
        data = analyzer.get_audience_retention_data() # Usa o mock interno
        assert isinstance(data, list)
        if data:
            assert isinstance(data[0], tuple)
            assert len(data[0]) == 2
            assert isinstance(data[0][0], (int, float)) # timestamp
            assert isinstance(data[0][1], (int, float)) # retention

    def test_detect_retention_peaks_no_data(self, analyzer):
        assert analyzer.detect_retention_peaks([]) == []

    def test_detect_retention_peaks_flat_retention_below_avg(self, analyzer):
        # Média será 10. Nenhum pico.
        flat_data = [(i*5, 10.0) for i in range(10)]
        assert analyzer.detect_retention_peaks(flat_data) == []

    def test_detect_retention_peaks_flat_retention_at_avg(self, analyzer):
        # Média será 10. Nenhum pico. (threshold é > avg)
        flat_data = [(i*5, 10.0) for i in range(10)]
        # A lógica atual é `retention > threshold`. Se for sempre igual, não há pico.
        assert analyzer.detect_retention_peaks(flat_data) == []


    def test_detect_retention_peaks_single_simple_peak(self, analyzer):
        # Média ~ ( (5*20) + (5*80) ) / 10 = (100 + 400)/10 = 50.
        # Picos são > 50.
        # Segmentos de 5s. (0,20), (5,20), (10,20), (15,20), (20,20) -> timestamps 0,5,10,15
        # (25,80), (30,80), (35,80), (40,80), (45,80) -> timestamps 20,25,30,35,40
        # O pico começa em t=20 (valor 80). Último ponto do pico é t=40 (valor 80).
        # O pico termina no (timestamp do último ponto alto + duração do segmento) = 40 + 5 = 45.
        data = [
            (0, 20.0), (5, 20.0), (10, 20.0), (15, 20.0), (20, 20.0), # avg_retention aqui é 20
            (25, 80.0), (30, 80.0), (35, 80.0), (40, 80.0), (45, 80.0)  # avg_retention aqui é 80
        ]
        # Avg total = (5*20 + 5*80) / 10 = (100+400)/10 = 50
        # Pico esperado: (25, 50) (início em 25, fim em 45 + 5 = 50)
        peaks = analyzer.detect_retention_peaks(data)
        assert len(peaks) == 1
        assert peaks[0] == (25, 50) # (start_time, end_time_exclusive_ish)

    def test_detect_retention_peaks_peak_at_start(self, analyzer):
        # Média ( (5*80) + (5*20) ) / 10 = 50
        data = [
            (0, 80.0), (5, 80.0), (10, 80.0), (15, 80.0), (20, 80.0),
            (25, 20.0), (30, 20.0), (35, 20.0), (40, 20.0), (45, 20.0)
        ]
        # Pico esperado: (0, 25)
        peaks = analyzer.detect_retention_peaks(data)
        assert len(peaks) == 1
        assert peaks[0] == (0, 25)

    def test_detect_retention_peaks_peak_at_end(self, analyzer):
        # Média 50
        data = [
            (0, 20.0), (5, 20.0), (10, 20.0), (15, 20.0), (20, 20.0),
            (25, 80.0), (30, 80.0), (35, 80.0), (40, 80.0), (45, 80.0) # Último ponto é t=45
        ]
        # Pico esperado: (25, 50) (fim em 45 + 5 = 50)
        peaks = analyzer.detect_retention_peaks(data)
        assert len(peaks) == 1
        assert peaks[0] == (25, 50)

    def test_detect_retention_peaks_multiple_peaks(self, analyzer):
        # Média (2*20 + 3*80 + 2*20 + 3*90) / 10 = (40 + 240 + 40 + 270) / 10 = 590 / 10 = 59
        data = [
            (0, 20.0), (5, 20.0),                 # Abaixo da média
            (10, 80.0), (15, 80.0), (20, 80.0),   # Pico 1 (10 a 20+5=25)
            (25, 20.0), (30, 20.0),               # Abaixo da média
            (35, 90.0), (40, 90.0), (45, 90.0)    # Pico 2 (35 a 45+5=50)
        ]
        peaks = analyzer.detect_retention_peaks(data)
        assert len(peaks) == 2
        assert peaks[0] == (10, 25)
        assert peaks[1] == (35, 50)

    def test_get_mock_audience_retention_duration(self):
        # Testar a função utilitária diretamente
        data = get_mock_audience_retention(video_duration_seconds=30)
        assert data[-1][0] < 30 # Timestamp é o início do segmento
        # O último timestamp deve ser video_duration_seconds - step_size (5)
        assert data[-1][0] == 25
