"""Voice I/O for the AI Interviewer using Gemini TTS/STT.

Requires optional dependency: sounddevice (pip install sounddevice)
Uses the google-genai SDK for both text-to-speech and speech-to-text.
"""

from __future__ import annotations

import io
import logging
import struct
import tempfile
import wave
from functools import lru_cache

from google.genai import types

from shared.llm.gemini import _get_client

LOG = logging.getLogger("ai_interviewer.voice")

TTS_MODEL = "gemini-3-flash-preview"
STT_MODEL = "gemini-3-flash-preview"
VOICE_NAME = "Kore"
RECORD_SAMPLE_RATE = 24000
RECORD_CHANNELS = 1
RECORD_DTYPE = "int16"
SILENCE_THRESHOLD = 500
SILENCE_DURATION_S = 2.0


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def _require_sounddevice():
    """Import and return sounddevice, raising a clear error if missing."""
    try:
        import sounddevice  # noqa: F811
        return sounddevice
    except ImportError:
        raise RuntimeError(
            "Voice mode requires the 'sounddevice' package. "
            "Install it with: pip install sounddevice"
        )


# ---------------------------------------------------------------------------
# Text-to-Speech (Gemini)
# ---------------------------------------------------------------------------

def speak(text: str) -> None:
    """Convert text to speech using Gemini and play it through speakers."""
    if not text or not text.strip():
        return

    sd = _require_sounddevice()
    LOG.info("TTS: generating audio (%d chars)...", len(text))

    response = _get_client().models.generate_content(
        model=TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=VOICE_NAME,
                    )
                )
            ),
        ),
    )

    audio_data = _extract_audio_bytes(response)
    if audio_data is None:
        LOG.warning("TTS: no audio returned, falling back to text.")
        return

    _play_wav_bytes(sd, audio_data)


def _extract_audio_bytes(response) -> bytes | None:
    """Pull raw audio bytes from a Gemini response."""
    if not response.candidates:
        return None
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
            return part.inline_data.data
    return None


def _play_wav_bytes(sd, data: bytes) -> None:
    """Play WAV/PCM audio bytes through the default output device."""
    try:
        with io.BytesIO(data) as buf:
            with wave.open(buf, "rb") as wf:
                rate = wf.getframerate()
                channels = wf.getnchannels()
                frames = wf.readframes(wf.getnframes())
    except wave.Error:
        # Raw PCM (16-bit LE mono at 24kHz) — common Gemini output
        rate = RECORD_SAMPLE_RATE
        channels = RECORD_CHANNELS
        frames = data

    import numpy as np
    samples = np.frombuffer(frames, dtype=np.int16).reshape(-1, channels)
    sd.play(samples, samplerate=rate)
    sd.wait()
    LOG.info("TTS: playback complete.")


# ---------------------------------------------------------------------------
# Speech-to-Text (Gemini)
# ---------------------------------------------------------------------------

def listen(prompt_text: str = "Listening...") -> str:
    """Record from microphone until silence, then transcribe with Gemini."""
    sd = _require_sounddevice()
    import numpy as np

    LOG.info("STT: %s", prompt_text)

    audio_frames = _record_until_silence(sd, np)
    if len(audio_frames) == 0:
        return ""

    wav_bytes = _frames_to_wav(audio_frames, np)
    transcript = _transcribe(wav_bytes)
    LOG.info("STT: transcribed %d chars.", len(transcript))
    return transcript


def _record_until_silence(sd, np) -> list:
    """Record audio chunks until sustained silence is detected."""
    chunk_duration = 0.5  # seconds per chunk
    chunk_samples = int(RECORD_SAMPLE_RATE * chunk_duration)
    silence_chunks_needed = int(SILENCE_DURATION_S / chunk_duration)

    frames: list = []
    silent_chunks = 0
    recording = False

    print("🎤 Speak now (silence to stop)...")

    while True:
        chunk = sd.rec(
            chunk_samples,
            samplerate=RECORD_SAMPLE_RATE,
            channels=RECORD_CHANNELS,
            dtype=RECORD_DTYPE,
        )
        sd.wait()

        amplitude = np.abs(chunk).mean()

        if amplitude > SILENCE_THRESHOLD:
            recording = True
            silent_chunks = 0
            frames.append(chunk.copy())
        elif recording:
            silent_chunks += 1
            frames.append(chunk.copy())
            if silent_chunks >= silence_chunks_needed:
                break
        # Not yet recording and still silent — keep waiting

    print("🎤 Processing...")
    return frames


def _frames_to_wav(frames: list, np) -> bytes:
    """Convert recorded numpy frames to WAV bytes."""
    import numpy as _np
    audio = _np.concatenate(frames, axis=0)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(RECORD_CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(RECORD_SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()


def _transcribe(wav_bytes: bytes) -> str:
    """Send audio to Gemini for transcription."""
    audio_part = types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav")

    response = _get_client().models.generate_content(
        model=STT_MODEL,
        contents=[
            "Transcribe the following audio exactly. Return ONLY the transcribed text, "
            "no commentary or formatting.",
            audio_part,
        ],
    )

    return (response.text or "").strip()
