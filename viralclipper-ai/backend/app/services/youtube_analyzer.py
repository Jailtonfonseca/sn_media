from typing import List, Tuple, Any
import random
import json # Adicionado para salvar JSON

# Mock data para simular a API do YouTube Analytics
def get_mock_audience_retention(video_duration_seconds: int = 900) -> List[Tuple[int, float]]:
    """
    Generates more realistic mock audience retention data with multiple peaks and valleys.
    """
    data = []
    num_points = video_duration_seconds // 5

    # Define some interesting time points for peaks
    peak_centers = sorted([random.uniform(0.1, 0.9) * video_duration_seconds for _ in range(random.randint(3, 5))])

    for i in range(num_points):
        timestamp = i * 5
        # Base decay curve
        base_retention = 100 * (1 - (timestamp / video_duration_seconds))**1.5

        # Add random noise
        noise = random.uniform(-3, 3)
        retention = base_retention + noise

        # Add simulated peaks
        for peak_center in peak_centers:
            distance_to_peak = abs(timestamp - peak_center)
            if distance_to_peak < 60: # Peaks are about 2 minutes wide
                # Gaussian-like bump
                peak_effect = 25 * (1 - (distance_to_peak / 60))**2
                retention += peak_effect

        # Add a sharp drop-off simulation
        if 200 < timestamp < 230:
            retention *= 0.8

        # Clamp values between 0 and 100
        retention = max(0, min(100, retention))
        data.append((timestamp, round(retention, 2)))

    return data

class YouTubeAnalyzerService:
    def __init__(self, video_id: str = None, project_id: int = None):
        self.video_id = video_id
        self.project_id = project_id

    def get_audience_retention_data(self) -> List[Tuple[int, float]]:
        print(f"Simulating fetching audience retention for YouTube video: {self.video_id} (Project: {self.project_id})")
        # Simulate video duration for more realistic mock data
        mock_data = get_mock_audience_retention(video_duration_seconds=random.randint(600, 1800))
        return mock_data

    def _calculate_moving_average(self, data: List[float], window_size: int) -> List[float]:
        """Calculates the moving average of a list of numbers."""
        moving_averages = []
        for i in range(len(data)):
            start_index = max(0, i - window_size // 2)
            end_index = min(len(data), i + window_size // 2 + 1)
            window = data[start_index:end_index]
            moving_averages.append(sum(window) / len(window))
        return moving_averages

    def _merge_peaks(self, peaks: List[Tuple[int, int]], merge_distance_seconds: int) -> List[Tuple[int, int]]:
        """Merges adjacent peaks that are closer than the specified distance."""
        if not peaks:
            return []

        merged_peaks = []
        current_peak = peaks[0]

        for next_peak in peaks[1:]:
            # If the gap between the end of the current peak and the start of the next is small enough
            if next_peak[0] - current_peak[1] <= merge_distance_seconds:
                # Merge by extending the end time of the current peak
                current_peak = (current_peak[0], next_peak[1])
            else:
                # The gap is too large, so finalize the current peak and start a new one
                merged_peaks.append(current_peak)
                current_peak = next_peak

        merged_peaks.append(current_peak) # Add the last processed peak
        return merged_peaks

    def detect_retention_peaks(
        self,
        retention_data: List[Tuple[int, float]],
        moving_average_window: int = 12, # Window size in data points (12 * 5s = 60s)
        peak_threshold_factor: float = 1.15, # Retention must be 15% above moving average
        merge_distance_seconds: int = 15 # Merge peaks less than 15s apart
    ) -> List[Tuple[int, int]]:
        if not retention_data:
            return []

        timestamps, retention_values = zip(*retention_data)

        moving_average = self._calculate_moving_average(list(retention_values), moving_average_window)

        raw_peaks = []
        in_peak = False
        current_peak_start_time = 0

        segment_duration = 5 # Default segment duration
        if len(timestamps) > 1:
            segment_duration = timestamps[1] - timestamps[0]

        for i, (timestamp, retention) in enumerate(retention_data):
            threshold = moving_average[i] * peak_threshold_factor
            if retention > threshold and not in_peak:
                in_peak = True
                current_peak_start_time = timestamp
            elif retention < moving_average[i] and in_peak: # End peak when it drops below the simple moving average
                in_peak = False
                peak_end_time = retention_data[i-1][0] + segment_duration
                raw_peaks.append((current_peak_start_time, peak_end_time))

        if in_peak: # If still in peak at the end of data
            peak_end_time = retention_data[-1][0] + segment_duration
            raw_peaks.append((current_peak_start_time, peak_end_time))

        print(f"Detected {len(raw_peaks)} raw peaks: {raw_peaks}")

        merged_peaks = self._merge_peaks(raw_peaks, merge_distance_seconds)
        print(f"Detected {len(merged_peaks)} merged peaks: {merged_peaks}")

        return merged_peaks
