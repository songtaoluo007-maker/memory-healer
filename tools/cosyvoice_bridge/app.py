"""Minimal authenticated FastAPI bridge for the pinned CosyVoice runtime."""

from __future__ import annotations

import io
import os
import secrets
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response


def load_cosyvoice_runtime(model_dir: str) -> SimpleNamespace:
    repository_dir = Path(
        os.environ.get("COSYVOICE_REPO_DIR", ".local/cosyvoice")
    ).resolve()
    matcha_dir = repository_dir / "third_party" / "Matcha-TTS"
    for import_root in (repository_dir, matcha_dir):
        if str(import_root) not in sys.path:
            sys.path.insert(0, str(import_root))

    import torch
    import torchaudio
    from cosyvoice.cli.cosyvoice import AutoModel
    from cosyvoice.utils.file_utils import load_wav

    return SimpleNamespace(
        model=AutoModel(model_dir=model_dir),
        torch=torch,
        torchaudio=torchaudio,
        load_wav=load_wav,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    bridge_token = os.environ.get("COSYVOICE_BRIDGE_TOKEN", "")
    if not bridge_token:
        raise RuntimeError("COSYVOICE_BRIDGE_TOKEN must be configured")
    model_dir = os.environ.get("COSYVOICE_MODEL_DIR", "")
    if not model_dir:
        raise RuntimeError("COSYVOICE_MODEL_DIR must be configured")

    app.state.bridge_token = bridge_token
    app.state.runtime = load_cosyvoice_runtime(model_dir)
    yield


app = FastAPI(title="CosyVoice Local Bridge", lifespan=lifespan)


def require_bridge_token(request: Request) -> None:
    supplied = request.headers.get("X-Voice-Bridge-Token", "")
    configured = request.app.state.bridge_token
    if not supplied or not secrets.compare_digest(supplied, configured):
        raise HTTPException(status_code=401, detail="Invalid bridge token")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/synthesize")
async def synthesize(
    request: Request,
    tts_text: str = Form(min_length=1, max_length=500),
    instruct_text: str = Form(min_length=1, max_length=1000),
    prompt_wav: UploadFile = File(),
) -> Response:
    require_bridge_token(request)
    runtime = request.app.state.runtime
    prompt_bytes = await prompt_wav.read()
    prompt = runtime.load_wav(io.BytesIO(prompt_bytes), 16000)
    chunks = list(
        runtime.model.inference_instruct2(
            tts_text,
            instruct_text,
            prompt,
            stream=False,
        )
    )
    if not chunks:
        raise HTTPException(status_code=502, detail="CosyVoice returned no audio")
    speech = runtime.torch.cat(
        [chunk["tts_speech"] for chunk in chunks],
        dim=1,
    )
    output = io.BytesIO()
    runtime.torchaudio.save(
        output,
        speech,
        runtime.model.sample_rate,
        format="wav",
    )
    return Response(output.getvalue(), media_type="audio/wav")
