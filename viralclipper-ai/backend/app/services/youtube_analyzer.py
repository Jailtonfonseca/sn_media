from typing import List, Tuple, Any
import random
import json # Adicionado para salvar JSON

# Mock data para simular a API do YouTube Analytics
def get_mock_audience_retention(video_duration_seconds: int = 600) -> List[Tuple[int, float]]:
    data = []
    for i in range(0, video_duration_seconds, 5): # Assume 5 second intervals
        base_retention = 100 - (i / video_duration_seconds) * 70
        noise = random.uniform(-10, 10)
        retention = max(0, min(100, base_retention + noise))
        # Simulate some peaks
        if 100 < i < 150 or 300 < i < 380: # Example peak intervals
            retention = min(100, retention + random.uniform(10, 30))
        data.append((i, round(retention, 2)))
    return data

class YouTubeAnalyzerService:
    def __init__(self, video_id: str = None, project_id: int = None):
        self.video_id = video_id
        self.project_id = project_id

    def get_audience_retention_data(self) -> List[Tuple[int, float]]:
        print(f"Simulating fetching audience retention for YouTube video: {self.video_id} (Project: {self.project_id})")
        # Simulate video duration based on project_id or a random duration
        mock_data = get_mock_audience_retention(video_duration_seconds=random.randint(300, 1200))
        return mock_data

    def detect_retention_peaks(self, retention_data: List[Tuple[int, float]]) -> List[Tuple[int, int]]:
        if not retention_data:
            return []

        total_retention_sum = sum(point[1] for point in retention_data)
        if not retention_data: # Should be caught by the first check, but good for safety
             average_retention = 0
        else:
             average_retention = total_retention_sum / len(retention_data)

        print(f"Average retention: {average_retention:.2f}%")

        threshold = average_retention
        peaks = []
        in_peak = False
        current_peak_start_time = 0

        # Determine segment_duration from data if possible, otherwise default
        segment_duration = 5 # Default segment duration
        if len(retention_data) > 1:
             first_timestamp = retention_data[0][0]
             second_timestamp = retention_data[1][0]
             if second_timestamp > first_timestamp: # Make sure timestamps are increasing and valid
                  segment_duration = second_timestamp - first_timestamp

        for i, (timestamp, retention) in enumerate(retention_data):
            if retention > threshold and not in_peak:
                in_peak = True
                current_peak_start_time = timestamp
            elif retention <= threshold and in_peak:
                in_peak = False
                # Peak ended at the previous timestamp's segment end
                # If retention_data[i-1] exists, use its timestamp + segment_duration
                peak_end_time = (retention_data[i-1][0] + segment_duration) if i > 0 else (timestamp + segment_duration)
                peaks.append((current_peak_start_time, peak_end_time))

        if in_peak: # If still in peak at the end of data
            # End of last segment is its start_time + segment_duration
            peak_end_time = retention_data[-1][0] + segment_duration
            peaks.append((current_peak_start_time, peak_end_time))

        print(f"Detected peaks (raw): {peaks}")
        return peaks
