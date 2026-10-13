import unittest

import numpy as np

from silence_detector import EndOfSpeechDetector

RATE = 16000
CHUNK = RATE // 10  # 100 ms, matches the recording loop in app.py


def loud():
    return np.full(CHUNK, 3000, dtype=np.int16)


def quiet():
    return np.full(CHUNK, 10, dtype=np.int16)


def run(detector, chunks):
    """Feed chunks until the detector stops; return (reason, chunks_used)."""
    for n, chunk in enumerate(chunks, start=1):
        reason = detector.update(chunk)
        if reason:
            return reason, n
    return None, len(chunks)


class EndOfSpeechDetectorTests(unittest.TestCase):
    def test_stops_after_silence_following_speech(self):
        d = EndOfSpeechDetector(RATE, silence_duration=1.0)
        reason, used = run(d, [loud()] * 5 + [quiet()] * 20)
        self.assertEqual(reason, "silence")
        self.assertEqual(used, 5 + 10)  # exactly 1.0s of quiet after the speech

    def test_pause_shorter_than_silence_duration_does_not_stop(self):
        d = EndOfSpeechDetector(RATE, silence_duration=1.0)
        chunks = [loud()] * 3 + [quiet()] * 5 + [loud()] * 3  # 0.5s mid-sentence pause
        self.assertEqual(run(d, chunks)[0], None)

    def test_speech_resets_the_silence_counter(self):
        d = EndOfSpeechDetector(RATE, silence_duration=1.0)
        chunks = [loud()] + [quiet()] * 9 + [loud()] + [quiet()] * 9  # never 1.0s in a row
        self.assertEqual(run(d, chunks)[0], None)

    def test_leading_silence_is_not_end_of_speech(self):
        d = EndOfSpeechDetector(RATE, silence_duration=1.0, no_speech_timeout=5)
        reason, _ = run(d, [quiet()] * 20)  # 2s of quiet before anyone speaks
        self.assertIsNone(reason)

    def test_no_speech_timeout(self):
        d = EndOfSpeechDetector(RATE, no_speech_timeout=2, max_duration=10)
        self.assertEqual(run(d, [quiet()] * 30), ("no_speech", 20))

    def test_max_duration_caps_continuous_speech(self):
        d = EndOfSpeechDetector(RATE, silence_duration=1.0, max_duration=3)
        self.assertEqual(run(d, [loud()] * 100), ("timeout", 30))

    def test_threshold_decides_what_counts_as_speech(self):
        low = np.full(CHUNK, 300, dtype=np.int16)
        sensitive = EndOfSpeechDetector(RATE, energy_threshold=200)
        deaf = EndOfSpeechDetector(RATE, energy_threshold=500)
        sensitive.update(low)
        deaf.update(low)
        self.assertTrue(sensitive.speech_started)
        self.assertFalse(deaf.speech_started)

    def test_peak_energy_tracks_loudest_chunk(self):
        d = EndOfSpeechDetector(RATE)
        for chunk in (quiet(), loud(), quiet()):
            d.update(chunk)
        self.assertAlmostEqual(d.peak_energy, 3000.0)

    def test_empty_chunk_is_silence(self):
        self.assertEqual(EndOfSpeechDetector.energy(np.array([], dtype=np.int16)), 0.0)


if __name__ == "__main__":
    unittest.main()
