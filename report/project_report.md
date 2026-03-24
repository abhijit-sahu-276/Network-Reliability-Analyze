# Project Report: Advanced Network Reliability Analyzer

## 1. Introduction

Computer networks face random link failures due to hardware faults, congestion, and maintenance events. Reliability analysis quantifies fault tolerance by estimating the probability that the network remains connected.

## 2. Problem Statement

Build a system that models a network as a graph and computes the probability of end-to-end connectivity under independent link failures.

## 3. Objectives

1. Model network as graph `G(V, E)`
2. Compute reliability exactly (when feasible)
3. Estimate reliability via Monte Carlo
4. Compare topology reliability
5. Detect critical links
6. Suggest improvements by adding links
7. Provide visual exploration

## 4. Literature and Concepts

- Graph Theory: connectivity, subgraphs
- Probability: independent Bernoulli link states
- Combinatorics: `2^m` edge-state space
- Network topologies: star, ring, mesh, tree

## 5. Methodology

### 5.1 Graph Model

- Nodes represent routers/switches/hosts
- Edges represent links with success probability `p_e`

### 5.2 Exact Reliability

- Enumerate all binary edge states
- Build active-edge subgraph
- Check connectivity with BFS
- Sum probabilities of connected states

### 5.3 Monte Carlo

- Randomly activate/deactivate edges according to `p_e`
- Check connectivity
- Reliability estimate: `connected_trials / total_trials`
- Compute 95% confidence interval

### 5.4 Critical Edge Analysis

- Remove one edge at a time
- Recompute reliability
- Rank edges by reliability drop

### 5.5 Optimization Suggestion

- Evaluate missing edges `(u, v)`
- Add candidate edge with assumed probability
- Select edge with maximum reliability improvement

## 6. Algorithms

### 6.1 Exact

```text
R = 0
for state in [0, 2^m - 1]:
    P(state) = product over edges:
               p_e if active else (1-p_e)
    if connected(state):
        R += P(state)
```

### 6.2 Monte Carlo

```text
success = 0
repeat N times:
    sample each edge as Bernoulli(p_e)
    if connected:
        success += 1
R_hat = success / N
```

## 7. Implementation

- Language: C++17 (`src/`)
- Visualization:
  - Python (`python/visualize.py`)
  - Browser app (`web/`)

Key modules:

- `graph.*`: storage + connectivity
- `reliability.*`: exact + Monte Carlo + analysis
- `simulation.*`: random failure simulation
- `topology.*`: topology generation
- `main.cpp`: user interaction

## 8. Results and Analysis

Expected patterns:

- Mesh reliability > Ring reliability > Star/Tree (typically for equal `p`)
- Critical links in tree/star cause large reliability drop
- Monte Carlo converges to exact values as trial count increases

## 9. Topology Comparison

Compare topologies for fixed `n` and `p`:

- Best: usually mesh due to path redundancy
- Worst: often tree/star due to bridge-like links

## 10. Conclusion

The analyzer demonstrates practical reliability modeling using discrete mathematics and computer networks. It supports both exact and scalable approximate methods with decision-support outputs.

## 11. Future Scope

- Correlated link failures
- Node failures
- Real network trace integration
- Parallelized reliability computation
- ML-based failure probability prediction

## 12. Viva Preparation (Short)

- Network reliability: probability network remains connected
- DFS/BFS use: connectivity testing
- Mesh reliability: high redundancy
- Exact vs Monte Carlo: exact exponential vs approximate linear-in-trials
