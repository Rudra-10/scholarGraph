import base64
import requests
from config import SARVAM_API_KEY, USE_SARVAM_TTS


def generate_speech(text: str) -> bytes:
    """
    Generate speech audio (WAV) for the given text.
    Uses Sarvam AI's Bulbul V3 model with speaker 'shubh' for English (en-IN).
    If USE_SARVAM_TTS is False, returns a lightweight mock silent WAV.
    """
    if not USE_SARVAM_TTS:
        # Return a 1-second silent mono 8kHz 16-bit PCM WAV as a developer fallback
        wav_header = (
            b"RIFF\x24\x40\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
            b"\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x40\x00\x00"
        )
        return wav_header + b"\x00" * 16384

    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY is not set in the environment.")

    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "target_language_code": "en-IN",
        "speaker": "shubh",
        "model": "bulbul:v3"
    }

    print(f"[SarvamTTS] Generating speech using bulbul:v3 for: '{text[:50]}...'")
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        audio_b64 = data["audios"][0]
        return base64.b64decode(audio_b64)
    else:
        raise Exception(f"Sarvam TTS API failed ({response.status_code}): {response.text}")
