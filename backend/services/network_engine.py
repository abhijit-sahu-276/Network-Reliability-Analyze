from __future__ import annotations

import itertools
import math
import random
import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from backend.models.schemas import EdgeInput, NetworkSpec


@dataclass(frozen=True)
class Edge:
    u: int
    v: int
    p: float


def canonical(u: int, v: int) -> Tuple[int, int]:
    return (u, v) if u < v else (v, u)


def dedupe_and_validate_edges(nodes: int, edges: Iterable[EdgeInput]) -> List[Edge]:
    seen = set()
    normalized: List[Edge] = []
    for edge in edges:
        if edge.u < 0 or edge.u >= nodes or edge.v < 0 or edge.v >= nodes:
            raise ValueError(f"Edge ({edge.u},{edge.v}) out of node range [0, {nodes - 1}]")
        key = canonical(edge.u, edge.v)
        if key in seen:
            raise ValueError(f"Duplicate edge detected: {key}")
        seen.add(key)
        normalized.append(Edge(key[0], key[1], edge.probability))
    return normalized


def build_topology(name: str, nodes: int, p: float) -> List[Edge]:
    if nodes <= 1:
        return []
    edges: List[Edge] = []
    if name == "star":
        edges = [Edge(0, v, p) for v in range(1, nodes)]
    elif name == "ring":
        for u in range(nodes):
            v = (u + 1) % nodes
            key = canonical(u, v)
            if key[0] != key[1] and all(not (e.u == key[0] and e.v == key[1]) for e in edges):
                edges.append(Edge(key[0], key[1], p))
    elif name == "mesh":
        edges = [Edge(u, v, p) for u in range(nodes) for v in range(u + 1, nodes)]
    elif name == "tree":
        edges = [Edge((v - 1) // 2, v, p) for v in range(1, nodes)]
    elif name == "custom":
        edges = []
    else:
        raise ValueError(f"Unsupported topology: {name}")
    return edges


def normalize_network(spec: NetworkSpec) -> Tuple[int, List[Edge]]:
    if spec.topology != "custom" and not spec.edges:
        edges = build_topology(spec.topology, spec.nodes, spec.default_probability)
    else:
        edges = dedupe_and_validate_edges(spec.nodes, spec.edges)
    return spec.nodes, edges


def connected(nodes: int, edges: Sequence[Edge], active_mask: Sequence[bool]) -> bool:
    if nodes <= 1:
        return True
    adj = [[] for _ in range(nodes)]
    for edge, active in zip(edges, active_mask):
        if not active:
            continue
        adj[edge.u].append(edge.v)
        adj[edge.v].append(edge.u)

    q = deque([0])
    seen = [False] * nodes
    seen[0] = True
    while q:
        cur = q.popleft()
        for nxt in adj[cur]:
            if not seen[nxt]:
                seen[nxt] = True
                q.append(nxt)
    return all(seen)


def exact_reliability(nodes: int, edges: Sequence[Edge], state_limit: int = 1 << 22) -> float:
    m = len(edges)
    if m == 0:
        return 1.0 if nodes <= 1 else 0.0
    states = 1 << m
    if states > state_limit:
        raise ValueError("State space too large for exact reliability.")
    total = 0.0
    for mask in range(states):
        active = [(mask >> i) & 1 == 1 for i in range(m)]
        if not connected(nodes, edges, active):
            continue
        prob = 1.0
        for i, edge in enumerate(edges):
            prob *= edge.p if active[i] else (1.0 - edge.p)
            if prob == 0.0:
                break
        total += prob
    return max(0.0, min(1.0, total))


def monte_carlo_reliability(
    nodes: int, edges: Sequence[Edge], trials: int, seed: int | None = None
) -> Dict[str, float]:
    rng = random.Random(seed)
    success = 0
    for _ in range(trials):
        active = [rng.random() < edge.p for edge in edges]
        if connected(nodes, edges, active):
            success += 1

    r = success / float(trials)
    margin = 1.96 * math.sqrt(max(0.0, r * (1.0 - r)) / trials)
    return {
        "reliability": r,
        "ci_low": max(0.0, r - margin),
        "ci_high": min(1.0, r + margin),
    }


def evaluate_reliability(
    nodes: int, edges: Sequence[Edge], trials: int = 20_000, exact_state_limit: int = 1 << 22
) -> Dict[str, float | int | str]:
    start = time.perf_counter()
    m = len(edges)
    if m < 63 and (1 << m) <= exact_state_limit:
        r = exact_reliability(nodes, edges, exact_state_limit)
        elapsed = (time.perf_counter() - start) * 1000.0
        return {
            "method": "exact",
            "reliability": r,
            "ci_low": r,
            "ci_high": r,
            "states": 1 << m,
            "time_ms": elapsed,
        }
    mc = monte_carlo_reliability(nodes, edges, trials)
    elapsed = (time.perf_counter() - start) * 1000.0
    return {
        "method": "monte_carlo",
        "reliability": mc["reliability"],
        "ci_low": mc["ci_low"],
        "ci_high": mc["ci_high"],
        "states": trials,
        "time_ms": elapsed,
    }


def sample_failure_state(nodes: int, edges: Sequence[Edge], seed: int | None = None) -> Dict[str, object]:
    rng = random.Random(seed)
    active = [rng.random() < edge.p for edge in edges]
    is_ok = connected(nodes, edges, active)
    edge_states = [
        {"u": edge.u, "v": edge.v, "probability": edge.p, "active": bool(active_i)}
        for edge, active_i in zip(edges, active)
    ]
    return {
        "connected": is_ok,
        "edge_states": edge_states,
        "active_edges": sum(1 for x in active if x),
        "failed_edges": sum(1 for x in active if not x),
    }


def compare_topologies(nodes: int, p: float, trials: int) -> List[Dict[str, float | int | str]]:
    rows: List[Dict[str, float | int | str]] = []
    for name in ("star", "ring", "mesh", "tree"):
        edges = build_topology(name, nodes, p)
        result = evaluate_reliability(nodes, edges, trials)
        rows.append(
            {
                "topology": name,
                "edges": len(edges),
                "reliability": float(result["reliability"]),
                "method": str(result["method"]),
                "time_ms": float(result["time_ms"]),
            }
        )
    rows.sort(key=lambda row: row["reliability"], reverse=True)
    return rows


def edge_bridge_scores(nodes: int, edges: Sequence[Edge]) -> List[float]:
    m = len(edges)
    if m == 0:
        return []
    base_mask = [True] * m
    base_connected = connected(nodes, edges, base_mask)
    scores: List[float] = []
    for i in range(m):
        active = base_mask.copy()
        active[i] = False
        if base_connected and not connected(nodes, edges, active):
            scores.append(1.0)
        else:
            scores.append(0.0)
    return scores


def critical_edges(nodes: int, edges: Sequence[Edge], trials: int) -> List[Dict[str, float | int]]:
    baseline = evaluate_reliability(nodes, edges, trials)["reliability"]
    out: List[Dict[str, float | int]] = []
    for i, edge in enumerate(edges):
        reduced = [e for j, e in enumerate(edges) if j != i]
        new_r = evaluate_reliability(nodes, reduced, trials)["reliability"]
        out.append(
            {
                "index": i,
                "u": edge.u,
                "v": edge.v,
                "probability": edge.p,
                "reliability_without_edge": float(new_r),
                "drop": float(baseline - new_r),
            }
        )
    out.sort(key=lambda x: x["drop"], reverse=True)
    return out


def best_edge_addition(nodes: int, edges: Sequence[Edge], p_new: float, trials: int) -> Dict[str, float | int | bool]:
    existing = {canonical(edge.u, edge.v) for edge in edges}
    baseline = evaluate_reliability(nodes, edges, trials)["reliability"]
    best = {
        "found": False,
        "u": -1,
        "v": -1,
        "improvement": 0.0,
        "new_reliability": float(baseline),
    }
    candidates = [(u, v) for u in range(nodes) for v in range(u + 1, nodes) if (u, v) not in existing]
    # Cap candidates to keep response latency bounded for dense large networks.
    for u, v in itertools.islice(candidates, 0, 500):
        candidate_edges = list(edges) + [Edge(u, v, p_new)]
        result = evaluate_reliability(nodes, candidate_edges, trials)
        improvement = float(result["reliability"]) - float(baseline)
        if improvement > best["improvement"]:
            best = {
                "found": True,
                "u": u,
                "v": v,
                "improvement": improvement,
                "new_reliability": float(result["reliability"]),
            }
    return best
