import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .core import SynthesisService


class HealthRequest(BaseModel):
    pass


class SynthesizeFileRequest(BaseModel):
    file_name: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    task_types: Optional[List[str]] = None
    include_metrics: bool = False


def _skip_warmup() -> bool:
    return str(os.environ.get("DATA_SYNTHESIS_SKIP_WARMUP", "")).strip().lower() in {"1", "true", "yes", "on"}


def create_app(service: Optional[SynthesisService] = None) -> FastAPI:
    active_service = service or SynthesisService()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if not _skip_warmup():
            active_service.warmup()
        yield

    app = FastAPI(title="data_synthesis_service", version="1.0.0", lifespan=lifespan)

    @app.get("/health")
    def health_get() -> dict:
        return active_service.health()

    @app.post("/health")
    def health(_: HealthRequest) -> dict:
        return active_service.health()

    @app.post("/synthesize-file")
    def synthesize_file(request: SynthesizeFileRequest) -> dict:
        try:
            return active_service.synthesize_text(
                file_name=request.file_name,
                text=request.text,
                task_types=request.task_types,
                include_metrics=request.include_metrics,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()
