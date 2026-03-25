# AI-Powered Network Reliability Analyzer

Full-stack project that combines:

- Graph theory + probability-based reliability analysis
- Real-time failure simulation
- AI-based edge failure risk prediction
- Optimization suggestions for improving reliability
- Interactive frontend visualization

## Architecture

```text
frontend (React + D3 + Tailwind)
        ->
backend API (FastAPI)
        ->
reliability engine (Python services + existing C++ core in src/core)
        ->
AI module (logistic model)
        ->
database (SQLite runtime + PostgreSQL schema)
```

## Folder Structure

```text
/project
  /frontend
    /src
      /components
      /pages
      App.js
    index.html
  /backend
    main.py
    /routes
    /services
    /models
  /core
    graph.cpp
    reliability.cpp
  /ai
    model.py
    train.py
  /database
    schema.sql
    network_history.db (auto-created)
  /docs
    report.md
  /src
    ...existing C++ console implementation...
```

## API Endpoints

### Network APIs

- `POST /create-network`
- `POST /calculate-reliability`
- `POST /simulate-failure`
- `GET /compare-topologies`

### AI APIs

- `POST /predict-failure`
- `POST /suggest-optimization`
- `POST /train-model`

### Utility APIs

- `GET /health`
- `GET /history`
- `GET /docs` (Swagger UI)

## Quick Start

## 1) Install Python dependencies

```powershell
pip install -r requirements.txt
```

## 2) Train AI model (optional but recommended)

```powershell
python ai/train.py
```

## 3) Run backend

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

## 4) Run frontend (simple static server)

```powershell
python -m http.server 5600 -d frontend
```

Open:

- Frontend: `http://127.0.0.1:5600`
- Backend docs: `http://127.0.0.1:8000/docs`

## Frontend Features

- Topology builder (`Star`, `Ring`, `Mesh`, `Tree`)
- D3 force-directed graph with drag interactions
- Real-time simulation mode
- Reliability computation (exact/Monte Carlo auto-switch)
- Topology comparison table
- AI risk scoring heatmap (edge coloring by risk)
- Optimization recommendation panel
- Dark/light mode toggle

## Core Algorithms

- Exact reliability: `O(2^m * (n + m))`
- Monte Carlo reliability: `O(N * (n + m))`
- Connectivity check (BFS): `O(n + m)`

## Existing C++ Console Version

The original C++ console project remains available in `src/` and can still be compiled:

```powershell
g++ -std=c++17 -Wall -Wextra -pedantic src\*.cpp -o build\network_reliability.exe
.\build\network_reliability.exe
```

## Smoke Test

Run:

```powershell
python backend/smoke_test.py
```

This checks:

- Reliability computation
- Failure simulation
- Topology comparison
- AI prediction
- Optimization suggestion

## Notes

- For large graphs, Monte Carlo is automatically used.
- API analysis results are persisted to `database/network_history.db`.
- `database/schema.sql` provides an optional PostgreSQL schema for production deployment.
