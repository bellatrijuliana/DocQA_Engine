# ============================================================
# ollama_client.py — DocQA Case Engine v2.0
# Wrapper bersih untuk komunikasi ke Ollama local API.
# Model-agnostic: ganti model di config.py tanpa ubah file ini.
# ============================================================

import requests
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT


def check_ollama_connection() -> bool:
    """Cek apakah Ollama service berjalan di local."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return resp.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def list_available_models() -> list[str]:
    """Ambil daftar model yang sudah di-pull di Ollama."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception as e:
        print(f"[OllamaClient] Gagal ambil daftar model: {e}")
        return []


def generate(
    prompt: str,
    system_prompt: str = "",
    model: str = None,
    temperature: float = 0.3,
    expect_json: bool = False,
) -> str:
    """
    Kirim prompt ke Ollama dan return response text.

    Args:
        prompt:        User prompt / instruksi utama.
        system_prompt: Konteks sistem untuk model.
        model:         Override model (default dari config.py).
        temperature:   0.0 = deterministik, 1.0 = kreatif.
        expect_json:   Jika True, paksa response dalam format JSON.

    Returns:
        String response dari model, atau string kosong jika error.
    """
    model = model or OLLAMA_MODEL

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 4096,
        },
    }

    if system_prompt:
        payload["system"] = system_prompt

    if expect_json:
        payload["format"] = "json"

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()

    except requests.exceptions.ConnectionError:
        print(
            f"\n[OllamaClient] ❌ Tidak bisa konek ke Ollama di {OLLAMA_BASE_URL}\n"
            f"   Pastikan Ollama sudah berjalan: jalankan `ollama serve`\n"
        )
        return ""
    except requests.exceptions.Timeout:
        print(
            f"\n[OllamaClient] ⏱️ Timeout setelah {OLLAMA_TIMEOUT}s.\n"
            f"   Coba naikkan OLLAMA_TIMEOUT di config.py, atau gunakan model yang lebih kecil.\n"
        )
        return ""
    except Exception as e:
        print(f"[OllamaClient] Error: {e}")
        return ""


def generate_json(prompt: str, system_prompt: str = "", model: str = None) -> dict | list | None:
    """
    Shortcut: kirim prompt dan parse response sebagai JSON.
    Return None jika parsing gagal.
    """
    raw = generate(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        temperature=0.2,
        expect_json=True,
    )

    if not raw:
        return None

    # Bersihkan fence markdown jika ada (```json ... ```)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"[OllamaClient] ⚠️ Gagal parse JSON: {e}")
        print(f"[OllamaClient] Raw response:\n{raw[:500]}...")
        return None


# ── Quick test ──────────────────────────────────────────────
if __name__ == "__main__":
    print("Mengecek koneksi Ollama...")
    if check_ollama_connection():
        models = list_available_models()
        print(f"✅ Ollama aktif. Model tersedia: {models}")
        print(f"\nTesting generate dengan model '{OLLAMA_MODEL}'...")
        result = generate("Jawab singkat: apa itu risk-based testing?")
        print(f"Response: {result}")
    else:
        print(f"❌ Ollama tidak ditemukan di {OLLAMA_BASE_URL}")
        print("   Jalankan: ollama serve")