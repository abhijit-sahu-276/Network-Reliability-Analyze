from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.models.schemas import (
    NetworkSpec,
    ReliabilityRequest,
    SimulationRequest,
    TopologyCompareRequest,
)
from backend.services.network_engine import (
    compare_topologies,
    critical_edges,
    evaluate_reliability,
    normalize_network,
    sample_failure_state,
)
from backend.services.repository import save_analysis


router = APIRouter(tags=["network"])


@router.post("/create-network")
def create_network(payload: NetworkSpec):
    try:
        nodes, edges = normalize_network(payload)
        network = {
            "nodes": nodes,
            "edges": [{"u": e.u, "v": e.v, "probability": e.p} for e in edges],
            "edge_count": len(edges),
            "topology": payload.topology,
        }
        record_id = save_analysis("create_network", network)
        network["record_id"] = record_id
        return network
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/calculate-reliability")
def calculate_reliability(payload: ReliabilityRequest):
    try:
        nodes, edges = normalize_network(payload.network)
        result = evaluate_reliability(nodes, edges, payload.monte_carlo_trials, payload.exact_state_limit)
        critical = critical_edges(nodes, edges, max(1000, payload.monte_carlo_trials // 2))
        response = {
            "nodes": nodes,
            "edges": len(edges),
            "reliability": result["reliability"],
            "method": result["method"],
            "ci_low": result["ci_low"],
            "ci_high": result["ci_high"],
            "time_ms": result["time_ms"],
            "critical_edges": critical[:5],
        }
        response["record_id"] = save_analysis("reliability", response)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/simulate-failure")
def simulate_failure(payload: SimulationRequest):
    try:
        nodes, edges = normalize_network(payload.network)
        if payload.trials == 1:
            sampled = sample_failure_state(nodes, edges, seed=payload.seed)
            sampled["record_id"] = save_analysis("simulation_single", sampled)
            return sampled

        connected_count = 0
        last = None
        for i in range(payload.trials):
            sampled = sample_failure_state(nodes, edges, seed=None if payload.seed is None else payload.seed + i)
            connected_count += 1 if sampled["connected"] else 0
            last = sampled
        reliability_empirical = connected_count / float(payload.trials)
        response = {
            "trials": payload.trials,
            "connected_trials": connected_count,
            "empirical_reliability": reliability_empirical,
            "last_sample": last,
        }
        response["record_id"] = save_analysis("simulation_batch", response)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/compare-topologies")
def compare_topologies_route(nodes: int = 8, probability: float = 0.9, monte_carlo_trials: int = 20_000):
    request = TopologyCompareRequest(nodes=nodes, probability=probability, monte_carlo_trials=monte_carlo_trials)
    rows = compare_topologies(request.nodes, request.probability, request.monte_carlo_trials)
    payload = {
        "rows": rows,
        "best_topology": rows[0]["topology"] if rows else None,
        "worst_topology": rows[-1]["topology"] if rows else None,
    }
    payload["record_id"] = save_analysis("compare_topologies", payload)
    return payload
