from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


TopologyName = Literal["star", "ring", "mesh", "tree", "custom"]


class EdgeInput(BaseModel):
    u: int = Field(ge=0)
    v: int = Field(ge=0)
    probability: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_distinct_nodes(self) -> "EdgeInput":
        if self.u == self.v:
            raise ValueError("Self-loops are not allowed.")
        return self


class NetworkSpec(BaseModel):
    nodes: int = Field(ge=1, le=300)
    edges: List[EdgeInput] = Field(default_factory=list)
    topology: TopologyName = "custom"
    default_probability: float = Field(default=0.90, ge=0.0, le=1.0)


class ReliabilityRequest(BaseModel):
    network: NetworkSpec
    monte_carlo_trials: int = Field(default=20_000, ge=100, le=2_000_000)
    exact_state_limit: int = Field(default=1 << 22, ge=1024, le=1 << 28)


class SimulationRequest(BaseModel):
    network: NetworkSpec
    trials: int = Field(default=1_000, ge=1, le=2_000_000)
    seed: Optional[int] = None


class TopologyCompareRequest(BaseModel):
    nodes: int = Field(ge=1, le=300)
    probability: float = Field(ge=0.0, le=1.0)
    monte_carlo_trials: int = Field(default=20_000, ge=100, le=2_000_000)


class FailureEvent(BaseModel):
    edge_u: int = Field(ge=0)
    edge_v: int = Field(ge=0)
    time_since_last_failure_min: float = Field(ge=0.0)
    utilization: float = Field(ge=0.0, le=1.0)
    latency_ms: float = Field(ge=0.0)
    packet_loss: float = Field(ge=0.0, le=1.0)
    historical_fail_rate: float = Field(ge=0.0, le=1.0)
    edge_probability: float = Field(ge=0.0, le=1.0)
    bridge_score: float = Field(ge=0.0, le=1.0)


class PredictFailureRequest(BaseModel):
    network: NetworkSpec
    events: List[FailureEvent] = Field(default_factory=list)


class SuggestOptimizationRequest(BaseModel):
    network: NetworkSpec
    edge_probability_for_new_link: float = Field(default=0.90, ge=0.0, le=1.0)
    monte_carlo_trials: int = Field(default=10_000, ge=500, le=1_000_000)
