from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ai.train import train_and_save
from backend.models.schemas import PredictFailureRequest, SuggestOptimizationRequest
from backend.services.ai_bridge import build_events_from_network, predict_edge_risks, suggest_network_optimization
from backend.services.network_engine import normalize_network
from backend.services.repository import save_analysis


router = APIRouter(tags=["ai"])


@router.post("/predict-failure")
def predict_failure(payload: PredictFailureRequest):
    try:
        nodes, edges = normalize_network(payload.network)
        events = [event.model_dump() for event in payload.events]
        if not events:
            events = build_events_from_network(nodes, edges)
        predictions = predict_edge_risks(events)
        response = {
            "count": len(predictions),
            "predictions": predictions,
            "highest_risk_edge": max(predictions, key=lambda item: item["failure_risk"]) if predictions else None,
        }
        response["record_id"] = save_analysis("predict_failure", response)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/suggest-optimization")
def suggest_optimization(payload: SuggestOptimizationRequest):
    try:
        nodes, edges = normalize_network(payload.network)
        suggestion = suggest_network_optimization(
            nodes, edges, payload.edge_probability_for_new_link, payload.monte_carlo_trials
        )
        response = {"suggestion": suggestion}
        response["record_id"] = save_analysis("suggest_optimization", response)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/train-model")
def train_model(samples: int = 3000, epochs: int = 350, seed: int = 42):
    model = train_and_save(samples=samples, epochs=epochs, seed=seed)
    payload = {
        "samples": samples,
        "epochs": epochs,
        "seed": seed,
        "weights": model.weights,
        "bias": model.bias,
    }
    payload["record_id"] = save_analysis("train_model", payload)
    return payload
