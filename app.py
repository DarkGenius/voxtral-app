"""Gradio web interface for Voxtral TTS."""

import io
import tempfile

import gradio as gr
import httpx
import soundfile as sf

from voxtral_tts import DEFAULT_MODEL, SAMPLE_RATE, VOICES

DEFAULT_SERVER_URL = "http://localhost:8000"


def synthesize(text: str, voice: str, server_url: str, model: str) -> str | None:
    if not text.strip():
        raise gr.Error("Введите текст для синтеза")

    payload = {
        "input": text,
        "model": model,
        "voice": voice,
        "response_format": "wav",
    }

    try:
        response = httpx.post(
            f"{server_url}/v1/audio/speech",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
    except httpx.ConnectError:
        raise gr.Error(f"Не удалось подключиться к серверу {server_url}. Убедитесь, что vLLM-Omni запущен.")
    except httpx.HTTPStatusError as e:
        raise gr.Error(f"Ошибка сервера: {e.response.status_code} {e.response.text[:200]}")

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(response.content)
    tmp.close()
    return tmp.name


with gr.Blocks(title="Voxtral TTS") as demo:
    gr.Markdown("# Voxtral TTS\nText-to-speech на базе [Voxtral-4B-TTS-2603](https://huggingface.co/mistralai/Voxtral-4B-TTS-2603)")

    with gr.Row():
        with gr.Column(scale=3):
            text_input = gr.Textbox(
                label="Текст",
                placeholder="Введите текст для синтеза речи...",
                lines=4,
            )
            voice_dropdown = gr.Dropdown(
                choices=VOICES,
                value="neutral_female",
                label="Голос",
            )
            generate_btn = gr.Button("Синтезировать", variant="primary")

        with gr.Column(scale=2):
            audio_output = gr.Audio(label="Результат", type="filepath")

    with gr.Accordion("Настройки сервера", open=False):
        server_url_input = gr.Textbox(
            value=DEFAULT_SERVER_URL,
            label="URL сервера vLLM-Omni",
        )
        model_input = gr.Textbox(
            value=DEFAULT_MODEL,
            label="Модель",
        )

    generate_btn.click(
        fn=synthesize,
        inputs=[text_input, voice_dropdown, server_url_input, model_input],
        outputs=audio_output,
    )

    text_input.submit(
        fn=synthesize,
        inputs=[text_input, voice_dropdown, server_url_input, model_input],
        outputs=audio_output,
    )

if __name__ == "__main__":
    demo.launch()
