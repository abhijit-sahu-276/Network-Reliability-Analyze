-- Database schema for AI-Powered Network Reliability Analyzer

CREATE TABLE IF NOT EXISTS networks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120),
    topology VARCHAR(24) NOT NULL,
    nodes INTEGER NOT NULL CHECK (nodes > 0),
    edges_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS simulations (
    id SERIAL PRIMARY KEY,
    network_id INTEGER REFERENCES networks(id) ON DELETE CASCADE,
    mode VARCHAR(24) NOT NULL, -- exact / monte_carlo / realtime
    trials INTEGER NOT NULL,
    reliability NUMERIC(8,6),
    ci_low NUMERIC(8,6),
    ci_high NUMERIC(8,6),
    result_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_predictions (
    id SERIAL PRIMARY KEY,
    network_id INTEGER REFERENCES networks(id) ON DELETE CASCADE,
    edge_u INTEGER NOT NULL,
    edge_v INTEGER NOT NULL,
    failure_risk NUMERIC(8,6) NOT NULL,
    risk_level VARCHAR(16) NOT NULL,
    importance_score NUMERIC(8,6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS optimization_suggestions (
    id SERIAL PRIMARY KEY,
    network_id INTEGER REFERENCES networks(id) ON DELETE CASCADE,
    suggested_u INTEGER,
    suggested_v INTEGER,
    improvement NUMERIC(8,6),
    new_reliability NUMERIC(8,6),
    details_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
