import numpy as np


class EndOfSpeechDetector:
    """Decides when a recording should stop, one audio chunk at a time.

    Time is counted from the number of samples fed in rather than the wall
    clock, so the decision depends only on the audio and can be tested
    without a microphone.

    update() returns None to keep recording, or the reason to stop:
      "silence"   - speech was heard, then `silence_duration` seconds of quiet
      "no_speech" - nothing above the threshold within `no_speech_timeout`
      "timeout"   - `max_duration` seconds recorded in total
    """

    def __init__(self, sample_rate=16000, energy_threshold=200,
                 silence_duration=1.5, no_speech_timeout=5, max_duration=10):
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.silence_duration = silence_duration
        self.no_speech_timeout = no_speech_timeout
        self.max_duration = max_duration

        # Counted in samples (integers) rather than accumulated seconds, so
        # ten 0.1s chunks are exactly 1.0s and not 0.9999999999999999.
        self._elapsed = 0
        self._silent = 0
        self.speech_started = False
        self.peak_energy = 0.0  # loudest chunk so far, for tuning the threshold

    @staticmethod
    def energy(samples):
        """RMS amplitude of an int16 chunk (0 = silent, 32768 = full scale)."""
        if len(samples) == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(samples.astype(np.float64)))))

    def update(self, samples):
        self._elapsed += len(samples)

        energy = self.energy(samples)
        self.peak_energy = max(self.peak_energy, energy)

        if energy >= self.energy_threshold:
            self.speech_started = True
            self._silent = 0
        else:
            self._silent += len(samples)

        rate = self.sample_rate
        if self.speech_started and self._silent >= self.silence_duration * rate:
            return "silence"
        if not self.speech_started and self._elapsed >= self.no_speech_timeout * rate:
            return "no_speech"
        if self._elapsed >= self.max_duration * rate:
            return "timeout"
        return None
