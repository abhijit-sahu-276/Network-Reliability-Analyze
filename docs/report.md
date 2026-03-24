# AI-Powered Network Reliability Analyzer

## Overview

This project combines graph-theoretic reliability analysis, Monte Carlo simulation,
AI-based edge failure prediction, and optimization recommendations in a full-stack architecture.

## Stack

- Frontend: React + D3 + Tailwind (no-build CDN mode)
- Backend: FastAPI
- Core engine: C++ (existing) + Python services for API orchestration
- AI module: lightweight logistic regression in pure Python
- Database: SQLite runtime store + PostgreSQL schema reference

## Key APIs

- `POST /create-network`
- `POST /calculate-reliability`
- `POST /simulate-failure`
- `GET /compare-topologies`
- `POST /predict-failure`
- `POST /suggest-optimization`
- `POST /train-model`

## AI Features

- Edge failure risk prediction
- Risk level classification
- Edge importance score
- Reliability improvement recommendation through edge addition

## Notes

- Exact reliability auto-selects for tractable state sizes.
- Monte Carlo path is used for large graphs.
- Analysis results are persisted in `database/network_history.db`.
