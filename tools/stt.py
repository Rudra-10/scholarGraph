import requests
from config import SARVAM_API_KEY, USE_SARVAM_LLM


def transcribe_speech(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Transcribe raw audio bytes using Sarvam AI's Saaras V3 model.
    If USE_SARVAM_LLM is False, returns a mock developer test question.
    """
    if not USE_SARVAM_LLM:
        # Mock developer test question
        print("[SarvamSTT] Mock mode: returning fallback query")
        return "What is the shortest citation path between BERT and Attention Is All You Need?"

    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY is not set in the environment.")

    url = "https://api.sarvam.ai/speech-to-text"
    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }
    files = {
        "file": (filename, audio_bytes, "audio/webm")
    }
    data = {
        "model": "saaras:v3",
        "mode": "transcribe"
    }

    print(f"[SarvamSTT] Sending transcription request to Saaras V3...")
    response = requests.post(url, headers=headers, files=files, data=data)
    if response.status_code == 200:
        res_json = response.json()
        return res_json.get("transcript", "")
    else:
        raise Exception(f"Sarvam STT API failed ({response.status_code}): {response.text}")
