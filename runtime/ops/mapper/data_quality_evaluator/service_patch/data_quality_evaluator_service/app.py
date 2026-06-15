import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .core import DataQualityEvaluatorService


class HealthRequest(BaseModel):
    pass


class EvaluateFileRequest(BaseModel):
    file_name: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    target_dimensions: Optional[List[str]] = None
    include_summary: bool = True
    model_path: Optional[str] = None
    backend: Optional[str] = None


def _skip_warmup() -> bool:
    return str(os.environ.get("DATA_QUALITY_EVALUATOR_SKIP_WARMUP", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def create_app(service: Optional[DataQualityEvaluatorService] = None) -> FastAPI:
    active_service = service or DataQualityEvaluatorService()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if not _skip_warmup():
            active_service.warmup()
        yield

    app = FastAPI(title="data_quality_evaluator_service", version="1.0.0", lifespan=lifespan)

    @app.get("/health")
    def health_get() -> dict:
        return active_service.health()

    @app.post("/health")
    def health(_: HealthRequest) -> dict:
        return active_service.health()

    @app.post("/evaluate-file")
    def evaluate_file(request: EvaluateFileRequest) -> dict:
        try:
            return active_service.evaluate_text(
                file_name=request.file_name,
                text=request.text,
                target_dimensions=request.target_dimensions,
                include_summary=request.include_summary,
                model_path=request.model_path,
                backend=request.backend,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()
