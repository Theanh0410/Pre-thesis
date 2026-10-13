# Silence Detection (auto-stop recording)

`speech_to_text()` in `app.py` stops recording on its own once the speaker has finished, instead of
always recording a fixed number of seconds.

## How it works

Audio is read from the microphone in 100 ms chunks. Each chunk is fed to Vosk immediately and also
passed to `EndOfSpeechDetector` (`silence_detector.py`), which computes its RMS energy and decides
whether to keep going:

| Stop reason | When | Result |
|---|---|---|
| `silence` | speech was heard, then `silence_duration` seconds of quiet | transcribe and return |
| `no_speech` | nothing louder than `silence_threshold` within `no_speech_timeout` | stop, then still transcribe (a quiet mic may be below the threshold but understandable); empty text gives "No speech detected" |
| `timeout` | `timeout` seconds recorded in total | transcribe and return |

Leading silence never triggers a stop: the silence timer only starts once speech has been detected. A
pause shorter than `silence_duration` in the middle of a sentence does not stop recording.

## Parameters

```python
speech_to_text(
    timeout=10,            # max total recording time (seconds)
    sample_rate=16000,     # Hz; must match the Vosk model
    silence_duration=1.5,  # seconds of quiet after speech before stopping
    silence_threshold=200, # RMS energy (int16 scale, 0-32768) that counts as speech
    no_speech_timeout=5,   # give up if nobody speaks within this many seconds
)
```

## Tuning

| Symptom | Fix |
|---|---|
| Cuts off in the middle of a sentence (long pauses) | raise `silence_duration` |
| Feels slow after finishing a command | lower `silence_duration` |
| Never stops / always runs to `timeout` (background noise) | raise `silence_threshold` |
| Ignores quiet speakers (`no_speech` although they spoke) | lower `silence_threshold` |

To find a good `silence_threshold` for your microphone, print `EndOfSpeechDetector.energy(chunk)` for a
few seconds of silence and a few seconds of normal speech, and pick a value between the two.

## Tests

`test_silence_detector.py` feeds synthetic loud/quiet chunks to the detector, so the stop logic is tested
without a microphone. The actual microphone path in `speech_to_text` needs a manual check:
`POST /start_voice`, say a command, and confirm it returns about `silence_duration` seconds after you stop.
