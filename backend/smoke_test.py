from __future__ import annotations

from ai.train import train_and_save
from backend.services.ai_bridge import build_events_from_network, predict_edge_risks, suggest_network_optimization
from backend.services.network_engine import compare_topologies, evaluate_reliability, normalize_network, sample_failure_state
from backend.models.schemas import NetworkSpec


def main() -> None:
    print("Running backend smoke test...")

    network = NetworkSpec(nodes=8, topology="ring", default_probability=0.90, edges=[])
    nodes, edges = normalize_network(network)

    reliability = evaluate_reliability(nodes, edges, trials=5000)
    print(f"[OK] Reliability: {reliability['reliability']:.6f} via {reliability['method']}")

    sim = sample_failure_state(nodes, edges, seed=123)
    print(f"[OK] Simulation connected={sim['connected']} active={sim['active_edges']} failed={sim['failed_edges']}")

    rows = compare_topologies(nodes=8, p=0.90, trials=3000)
    print(f"[OK] Compare best={rows[0]['topology']} worst={rows[-1]['topology']}")

    train_and_save(samples=1200, epochs=160, seed=42)
    events = build_events_from_network(nodes, edges, seed=4)
    risks = predict_edge_risks(events)
    top = max(risks, key=lambda item: item["failure_risk"])
    print(f"[OK] AI top risk edge=({top['edge_u']},{top['edge_v']}) score={top['failure_risk']:.3f}")

    suggestion = suggest_network_optimization(nodes, edges, p_new=0.90, trials=3000)
    print(f"[OK] Suggestion: {suggestion['message']}")

    print("Smoke test completed.")


if __name__ == "__main__":
    main()
