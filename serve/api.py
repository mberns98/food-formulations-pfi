import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

from serve.predictor import predict, load_models

app = FastAPI(
    title="Food Formulation Quality Predictor",
    description="Predicts aceptabilidad, dureza, elasticidad and color for a given ingredient mix.",
    version="1.0.0",
)


@app.on_event("startup")
def startup():
    load_models()  # pre-warm model cache on startup


class FormulationInput(BaseModel):
    ingredients: Dict[str, float]

    class Config:
        json_schema_extra = {
            "example": {
                "ingredients": {
                    "Agua": 0.631,
                    "Aceite_coco": 0.04,
                    "Sal": 0.013,
                }
            }
        }


class TargetResult(BaseModel):
    prediction: int
    probability: float


class PredictionOutput(BaseModel):
    aceptabilidad: TargetResult
    dureza: TargetResult
    elasticidad: TargetResult
    color: TargetResult


@app.post("/predict", response_model=PredictionOutput)
def predict_quality(payload: FormulationInput):
    try:
        result = predict(payload.ingredients)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
