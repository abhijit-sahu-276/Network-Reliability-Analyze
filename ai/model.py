from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


MODEL_PATH = Path(__file__).resolve().parent / "model_store.json"


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


@dataclass
class LogisticModel:
    weights: List[float]
    bias: float
    feature_names: List[str]
    learning_rate: float = 0.08

    def predict_proba(self, features: Sequence[float]) -> float:
        z = self.bias + sum(w * x for w, x in zip(self.weights, features))
        return sigmoid(z)

    def fit(self, x_data: Sequence[Sequence[float]], y_data: Sequence[int], epochs: int = 350) -> None:
        if not x_data:
            return
        n_features = len(x_data[0])
        if len(self.weights) != n_features:
            self.weights = [0.0] * n_features
        for _ in range(epochs):
            grad_w = [0.0] * n_features
            grad_b = 0.0
            for features, target in zip(x_data, y_data):
                pred = self.predict_proba(features)
                err = pred - float(target)
                grad_b += err
                for j in range(n_features):
                    grad_w[j] += err * features[j]
            scale = 1.0 / max(1, len(x_data))
            self.bias -= self.learning_rate * grad_b * scale
            for j in range(n_features):
                self.weights[j] -= self.learning_rate * grad_w[j] * scale

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, object]) -> "LogisticModel":
        return LogisticModel(
            weights=list(data.get("weights", [])),
            bias=float(data.get("bias", 0.0)),
            feature_names=list(data.get("feature_names", [])),
            learning_rate=float(data.get("learning_rate", 0.08)),
        )


DEFAULT_FEATURES = [
    "time_since_last_failure_min",
    "utilization",
    "latency_ms",
    "packet_loss",
    "historical_fail_rate",
    "edge_probability",
    "bridge_score",
]


def feature_vector(event: Dict[str, float]) -> List[float]:
    vals = [
        float(event["time_since_last_failure_min"]) / 60.0,
        float(event["utilization"]),
        float(event["latency_ms"]) / 150.0,
        float(event["packet_loss"]),
        float(event["historical_fail_rate"]),
        1.0 - float(event["edge_probability"]),
        float(event["bridge_score"]),
    ]
    return vals


def create_default_model() -> LogisticModel:
    # Sensible priors before training. Positive weights indicate higher failure risk.
    return LogisticModel(
        weights=[-0.25, 1.6, 1.15, 1.9, 1.45, 1.7, 0.8],
        bias=-1.2,
        feature_names=DEFAULT_FEATURES,
    )


def save_model(model: LogisticModel, path: Path = MODEL_PATH) -> None:
    path.write_text(json.dumps(model.to_dict(), indent=2), encoding="utf-8")


def load_model(path: Path = MODEL_PATH) -> LogisticModel:
    if not path.exists():
        model = create_default_model()
        save_model(model, path)
        return model
    payload = json.loads(path.read_text(encoding="utf-8"))
    return LogisticModel.from_dict(payload)


def risk_bucket(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def predict_failure_scores(events: Iterable[Dict[str, float]]) -> List[Dict[str, object]]:
    model = load_model()
    out: List[Dict[str, object]] = []
    for event in events:
        features = feature_vector(event)
        prob = model.predict_proba(features)
        out.append(
            {
                "edge_u": int(event["edge_u"]),
                "edge_v": int(event["edge_v"]),
                "failure_risk": prob,
                "risk_level": risk_bucket(prob),
                "importance_score": max(0.0, min(1.0, event["bridge_score"] * 0.65 + event["historical_fail_rate"] * 0.35)),
            }
        )
    return out
