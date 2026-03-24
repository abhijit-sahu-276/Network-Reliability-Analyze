from __future__ import annotations

import random
from typing import List, Tuple

from ai.model import LogisticModel, create_default_model, feature_vector, save_model


def synthetic_dataset(samples: int = 3000, seed: int = 42) -> Tuple[List[List[float]], List[int]]:
    rng = random.Random(seed)
    x_data: List[List[float]] = []
    y_data: List[int] = []

    for _ in range(samples):
        event = {
            "time_since_last_failure_min": rng.uniform(0.0, 360.0),
            "utilization": rng.uniform(0.05, 1.0),
            "latency_ms": rng.uniform(2.0, 220.0),
            "packet_loss": rng.uniform(0.0, 0.25),
            "historical_fail_rate": rng.uniform(0.0, 0.65),
            "edge_probability": rng.uniform(0.4, 0.995),
            "bridge_score": rng.uniform(0.0, 1.0),
        }
        features = feature_vector(event)

        # Non-linear synthetic rule used to generate labels.
        score = (
            0.9 * features[1]
            + 0.65 * features[2]
            + 1.1 * features[3]
            + 0.75 * features[4]
            + 0.9 * features[5]
            + 0.5 * features[6]
            - 0.3 * features[0]
            - 1.1
        )
        prob = 1.0 / (1.0 + pow(2.718281828, -score))
        label = 1 if rng.random() < prob else 0
        x_data.append(features)
        y_data.append(label)
    return x_data, y_data


def train_and_save(samples: int = 3000, epochs: int = 350, seed: int = 42) -> LogisticModel:
    model = create_default_model()
    x_data, y_data = synthetic_dataset(samples=samples, seed=seed)
    model.fit(x_data, y_data, epochs=epochs)
    save_model(model)
    return model


if __name__ == "__main__":
    trained = train_and_save()
    print("Model trained and saved.")
    print("Weights:", [round(w, 4) for w in trained.weights])
    print("Bias:", round(trained.bias, 4))
