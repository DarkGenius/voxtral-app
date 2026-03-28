"""Voxtral TTS — text-to-speech using mistralai/Voxtral-4B-TTS-2603.

Supports two modes:
  server  — sends request to a running vLLM server (lightweight, default)
  offline — loads the model directly via vllm-omni (requires GPU)

Usage:
  # Server mode (start vllm serve first):
  uv run voxtral_tts.py -t "Hello world" -o hello.wav

  # Play audio immediately without saving:
  uv run voxtral_tts.py -t "Hello world" --play

  # Offline mode:
  uv run voxtral_tts.py -m offline -t "Hello world" -o hello.wav
"""

import argparse
import io
import sys
from pathlib import Path

SAMPLE_RATE = 24000
DEFAULT_MODEL = "mistralai/Voxtral-4B-TTS-2603"

VOICES = [
    "casual_female", "casual_male", "cheerful_female",
    "neutral_female", "neutral_male",
    "fr_female", "fr_male",
    "es_female", "es_male",
    "de_female", "de_male",
    "it_female", "it_male",
    "pt_female", "pt_male",
    "nl_female", "nl_male",
    "ar_male",
    "hi_female", "hi_male",
]


def play_audio(audio_bytes: bytes) -> None:
    """Play WAV audio bytes using sounddevice."""
    import soundfile as sf
    import sounddevice as sd

    data, samplerate = sf.read(io.BytesIO(audio_bytes))
    print(f"Playing {len(data) / samplerate:.2f}s of audio ...")
    sd.play(data, samplerate)
    sd.wait()


def generate_server(text: str, voice: str, model: str, server_url: str,
                    output_path: str | None, play: bool) -> None:
    import httpx
    import soundfile as sf

    payload = {
        "input": text,
        "model": model,
        "voice": voice,
        "response_format": "wav",
    }

    print(f"Sending request to {server_url}/v1/audio/speech ...")
    response = httpx.post(
        f"{server_url}/v1/audio/speech",
        json=payload,
        timeout=120.0,
    )
    response.raise_for_status()

    if output_path:
        Path(output_path).write_bytes(response.content)
        info = sf.info(output_path)
        print(f"Saved {info.duration:.2f}s of audio to {output_path}")

    if play:
        play_audio(response.content)


def generate_offline(text: str, voice: str, model: str,
                     output_path: str | None, play: bool) -> None:
    import gc

    import soundfile as sf
    import torch
    from mistral_common.protocol.speech.request import SpeechRequest
    from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
    from vllm import SamplingParams
    from vllm_omni.entrypoints.omni import Omni

    print("Loading tokenizer ...")
    if Path(model).is_dir():
        tokenizer = MistralTokenizer.from_file(str(Path(model) / "tekken.json"))
    else:
        tokenizer = MistralTokenizer.from_hf_hub(model)
    instruct_tokenizer = tokenizer.instruct_tokenizer

    print("Encoding speech request ...")
    tokenized = instruct_tokenizer.encode_speech_request(
        SpeechRequest(input=text, voice=voice)
    )
    inputs = {
        "prompt_token_ids": tokenized.tokens,
        "additional_information": {"voice": [voice]},
    }

    sampling_params = SamplingParams(max_tokens=4096)

    print("Loading model (this may take a while) ...")
    llm = Omni(model=model)

    print("Generating audio ...")
    outputs = llm.generate(inputs, [sampling_params, sampling_params])

    audio_tensor = torch.cat(outputs[0].multimodal_output["audio"])
    audio_np = audio_tensor.cpu().float().numpy()

    if output_path:
        sf.write(output_path, audio_np, SAMPLE_RATE)
        info = sf.info(output_path)
        print(f"Saved {info.duration:.2f}s of audio to {output_path}")

    if play:
        buf = io.BytesIO()
        sf.write(buf, audio_np, SAMPLE_RATE, format="WAV")
        play_audio(buf.getvalue())

    del llm
    torch.cuda.empty_cache()
    gc.collect()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Text-to-speech with Voxtral-4B-TTS-2603"
    )
    parser.add_argument("-t", "--text", required=True, help="Text to synthesize")
    parser.add_argument("-v", "--voice", default="neutral_female",
                        help=f"Voice preset (default: neutral_female). Options: {', '.join(VOICES)}")
    parser.add_argument("-o", "--output", default=None, help="Output WAV file path")
    parser.add_argument("-p", "--play", action="store_true", help="Play audio immediately")
    parser.add_argument("-m", "--mode", choices=["server", "offline"], default="server",
                        help="Generation mode (default: server)")
    parser.add_argument("--server-url", default="http://localhost:8000",
                        help="vLLM server URL (server mode only, default: http://localhost:8000)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name or path (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    if not args.output and not args.play:
        args.output = "output.wav"

    if args.voice not in VOICES:
        print(f"Warning: '{args.voice}' is not a known preset voice. Known voices: {', '.join(VOICES)}",
              file=sys.stderr)

    if args.mode == "server":
        generate_server(args.text, args.voice, args.model, args.server_url, args.output, args.play)
    else:
        generate_offline(args.text, args.voice, args.model, args.output, args.play)


if __name__ == "__main__":
    main()
