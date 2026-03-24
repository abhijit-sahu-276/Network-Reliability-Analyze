from __future__ import annotations

import random
from typing import Dict, List, Sequence

from ai.model import predict_failure_scores
from backend.services.network_engine import Edge, best_edge_addition, edge_bridge_scores


def build_events_from_network(nodes: int, edges: Sequence[Edge], seed: int = 7) -> List[Dict[str, float]]:
    rng = random.Random(seed)
    bridges = edge_bridge_scores(nodes, edges)
    events: List[Dict[str, float]] = []
    for idx, edge in enumerate(edges):
        # Synthetic telemetry profile used when real telemetry is not supplied.
        events.append(
            {
                "edge_u": edge.u,
                "edge_v": edge.v,
                "time_since_last_failure_min": rng.uniform(10.0, 300.0),
                "utilization": min(1.0, max(0.0, rng.gauss(0.58, 0.18))),
                "latency_ms": max(1.0, rng.gauss(38.0 + bridges[idx] * 20.0, 14.0)),
                "packet_loss": min(1.0, max(0.0, rng.gauss(0.02 + bridges[idx] * 0.04, 0.015))),
                "historical_fail_rate": min(1.0, max(0.0, (1.0 - edge.p) * 0.6 + bridges[idx] * 0.25)),
                "edge_probability": edge.p,
                "bridge_score": bridges[idx],
            }
        )
    return events


def predict_edge_risks(events: List[Dict[str, float]]) -> List[Dict[str, object]]:
    return predict_failure_scores(events)


def suggest_network_optimization(
    nodes: int, edges: Sequence[Edge], p_new: float, trials: int
) -> Dict[str, float | int | bool | str]:
    best = best_edge_addition(nodes, edges, p_new, trials)
    if not best["found"]:
        return {
            "found": False,
            "message": "No missing edge available to add. The graph may already be complete.",
        }
    return {
        "found": True,
        "u": best["u"],
        "v": best["v"],
        "new_reliability": best["new_reliability"],
        "improvement": best["improvement"],
        "message": f"Add edge ({best['u']}, {best['v']}) to increase reliability.",
    }
