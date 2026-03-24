const { useEffect, useMemo, useRef, useState } = React;

function createTopology(topology, nodes, p) {
  const edges = [];
  if (nodes <= 1) return edges;

  if (topology === "star") {
    for (let v = 1; v < nodes; v++) edges.push({ u: 0, v, probability: p });
  } else if (topology === "ring") {
    for (let u = 0; u < nodes; u++) {
      const v = (u + 1) % nodes;
      const a = Math.min(u, v);
      const b = Math.max(u, v);
      if (!edges.some((e) => e.u === a && e.v === b)) {
        edges.push({ u: a, v: b, probability: p });
      }
    }
  } else if (topology === "mesh") {
    for (let u = 0; u < nodes; u++) {
      for (let v = u + 1; v < nodes; v++) edges.push({ u, v, probability: p });
    }
  } else if (topology === "tree") {
    for (let v = 1; v < nodes; v++) edges.push({ u: Math.floor((v - 1) / 2), v, probability: p });
  }
  return edges;
}

function GraphCanvas({ nodes, edges, edgeRiskMap, simulatedFailed }) {
  const svgRef = useRef(null);

  useEffect(() => {
    const width = 980;
    const height = 550;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const nodeData = Array.from({ length: nodes }, (_, id) => ({ id }));
    const linkData = edges.map((e) => ({ source: e.u, target: e.v }));

    const simulation = d3
      .forceSimulation(nodeData)
      .force("link", d3.forceLink(linkData).id((d) => d.id).distance(115).strength(0.7))
      .force("charge", d3.forceManyBody().strength(-430))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide(26));

    const link = svg
      .append("g")
      .selectAll("line")
      .data(linkData)
      .join("line")
      .attr("stroke-width", 3)
      .attr("stroke", (d) => {
        const a = Math.min(d.source.id ?? d.source, d.target.id ?? d.target);
        const b = Math.max(d.source.id ?? d.source, d.target.id ?? d.target);
        const key = `${a}-${b}`;
        if (simulatedFailed.has(key)) return "#dc2626";
        const risk = edgeRiskMap[key];
        if (risk == null) return "#0f766e";
        if (risk >= 0.75) return "#b91c1c";
        if (risk >= 0.45) return "#d97706";
        return "#0f766e";
      })
      .attr("stroke-dasharray", (d) => {
        const a = Math.min(d.source.id ?? d.source, d.target.id ?? d.target);
        const b = Math.max(d.source.id ?? d.source, d.target.id ?? d.target);
        return simulatedFailed.has(`${a}-${b}`) ? "8 6" : "0";
      })
      .attr("opacity", 0.9);

    const node = svg
      .append("g")
      .selectAll("circle")
      .data(nodeData)
      .join("circle")
      .attr("r", 18)
      .attr("fill", "#f8fafc")
      .attr("stroke", "#1f2937")
      .attr("stroke-width", 1.7)
      .call(
        d3
          .drag()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.25).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    const labels = svg
      .append("g")
      .selectAll("text")
      .data(nodeData)
      .join("text")
      .text((d) => d.id)
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("font-size", 12)
      .attr("font-weight", 700)
      .attr("fill", "#111827");

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);
      node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);
      labels.attr("x", (d) => d.x).attr("y", (d) => d.y);
    });

    return () => simulation.stop();
  }, [nodes, edges, edgeRiskMap, simulatedFailed]);

  return <svg ref={svgRef} className="w-full h-[550px] rounded-2xl bg-white/70 dark:bg-slate-900/70 border border-slate-300/60 dark:border-slate-700/80 shadow-inner" />;
}

function App() {
  const [apiBase, setApiBase] = useState("http://127.0.0.1:8000");
  const [topology, setTopology] = useState("ring");
  const [nodes, setNodes] = useState(8);
  const [edgeProbability, setEdgeProbability] = useState(0.9);
  const [trials, setTrials] = useState(20000);
  const [networkEdges, setNetworkEdges] = useState(() => createTopology("ring", 8, 0.9));
  const [result, setResult] = useState(null);
  const [comparison, setComparison] = useState([]);
  const [aiPredictions, setAiPredictions] = useState([]);
  const [suggestion, setSuggestion] = useState(null);
  const [simFailed, setSimFailed] = useState(new Set());
  const [status, setStatus] = useState("Ready");
  const [isDark, setIsDark] = useState(false);
  const [liveMode, setLiveMode] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  const networkPayload = useMemo(
    () => ({
      network: {
        nodes,
        topology: "custom",
        edges: networkEdges,
        default_probability: edgeProbability,
      },
      monte_carlo_trials: Number(trials),
    }),
    [nodes, networkEdges, edgeProbability, trials]
  );

  const edgeRiskMap = useMemo(() => {
    const map = {};
    aiPredictions.forEach((item) => {
      const a = Math.min(item.edge_u, item.edge_v);
      const b = Math.max(item.edge_u, item.edge_v);
      map[`${a}-${b}`] = item.failure_risk;
    });
    return map;
  }, [aiPredictions]);

  function rebuildTopology() {
    const edges = createTopology(topology, Number(nodes), Number(edgeProbability));
    setNetworkEdges(edges);
    setSimFailed(new Set());
    setResult(null);
    setAiPredictions([]);
    setSuggestion(null);
    setStatus(`Topology rebuilt: ${topology.toUpperCase()} with ${edges.length} edges`);
  }

  async function apiCall(path, method = "GET", payload = null) {
    const init = {
      method,
      headers: { "Content-Type": "application/json" },
    };
    if (payload) init.body = JSON.stringify(payload);
    const response = await fetch(`${apiBase}${path}`, init);
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(err.detail || "Request failed");
    }
    return response.json();
  }

  async function runReliability() {
    try {
      setStatus("Computing reliability...");
      const data = await apiCall("/calculate-reliability", "POST", networkPayload);
      setResult(data);
      setStatus(`Reliability computed using ${data.method}`);
    } catch (err) {
      setStatus(`Reliability error: ${err.message}`);
    }
  }

  async function runSimulation() {
    try {
      setStatus("Running single failure simulation...");
      const data = await apiCall("/simulate-failure", "POST", {
        network: networkPayload.network,
        trials: 1,
      });
      const failed = new Set();
      (data.edge_states || []).forEach((edge) => {
        if (!edge.active) {
          const a = Math.min(edge.u, edge.v);
          const b = Math.max(edge.u, edge.v);
          failed.add(`${a}-${b}`);
        }
      });
      setSimFailed(failed);
      setStatus(data.connected ? "Simulation: network stayed connected" : "Simulation: network disconnected");
    } catch (err) {
      setStatus(`Simulation error: ${err.message}`);
    }
  }

  async function runCompare() {
    try {
      setStatus("Comparing topologies...");
      const query = `?nodes=${nodes}&probability=${edgeProbability}&monte_carlo_trials=${trials}`;
      const data = await apiCall(`/compare-topologies${query}`);
      setComparison(data.rows || []);
      setStatus("Topology comparison complete");
    } catch (err) {
      setStatus(`Compare error: ${err.message}`);
    }
  }

  async function runPrediction() {
    try {
      setStatus("Predicting edge failures...");
      const data = await apiCall("/predict-failure", "POST", { network: networkPayload.network, events: [] });
      setAiPredictions(data.predictions || []);
      setStatus("AI risk scoring complete");
    } catch (err) {
      setStatus(`AI prediction error: ${err.message}`);
    }
  }

  async function runSuggestion() {
    try {
      setStatus("Searching best optimization...");
      const data = await apiCall("/suggest-optimization", "POST", {
        network: networkPayload.network,
        edge_probability_for_new_link: edgeProbability,
        monte_carlo_trials: Math.max(1000, Math.floor(trials / 2)),
      });
      setSuggestion(data.suggestion || null);
      setStatus("Optimization suggestion ready");
    } catch (err) {
      setStatus(`Suggestion error: ${err.message}`);
    }
  }

  useEffect(() => {
    if (!liveMode) return undefined;
    const id = setInterval(() => {
      runSimulation();
    }, 1400);
    return () => clearInterval(id);
  }, [liveMode, nodes, networkEdges, edgeProbability]);

  return (
    <div className="max-w-[1400px] mx-auto px-4 py-6 text-slate-800 dark:text-slate-100">
      <header className="glass border border-slate-200/70 dark:border-slate-700 rounded-2xl p-5 shadow-lg">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <p className="uppercase tracking-[0.14em] text-xs text-emerald-700 dark:text-emerald-400">AI + Graph Theory + Networks</p>
            <h1 className="text-3xl font-black mt-1">AI-Powered Network Reliability Analyzer</h1>
            <p className="text-sm mt-1 text-slate-600 dark:text-slate-300">Real-time simulation, reliability analysis, failure prediction, and optimization</p>
          </div>
          <button onClick={() => setIsDark((s) => !s)} className="px-4 py-2 rounded-xl bg-slate-900 text-white dark:bg-amber-400 dark:text-slate-900 font-semibold">
            {isDark ? "Light Mode" : "Dark Mode"}
          </button>
        </div>
      </header>

      <section className="grid grid-cols-1 xl:grid-cols-3 gap-4 mt-4">
        <div className="xl:col-span-2 glass border border-slate-200/70 dark:border-slate-700 rounded-2xl p-4 shadow-md">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <label className="text-xs font-semibold">API Base
              <input value={apiBase} onChange={(e) => setApiBase(e.target.value)} className="mt-1 w-full rounded-lg px-2 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-sm" />
            </label>
            <label className="text-xs font-semibold">Topology
              <select value={topology} onChange={(e) => setTopology(e.target.value)} className="mt-1 w-full rounded-lg px-2 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-sm">
                <option value="star">Star</option>
                <option value="ring">Ring</option>
                <option value="mesh">Mesh</option>
                <option value="tree">Tree</option>
              </select>
            </label>
            <label className="text-xs font-semibold">Nodes
              <input type="number" min="1" max="30" value={nodes} onChange={(e) => setNodes(Number(e.target.value))} className="mt-1 w-full rounded-lg px-2 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-sm" />
            </label>
            <label className="text-xs font-semibold">Edge p
              <input type="number" min="0" max="1" step="0.01" value={edgeProbability} onChange={(e) => setEdgeProbability(Number(e.target.value))} className="mt-1 w-full rounded-lg px-2 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-sm" />
            </label>
            <label className="text-xs font-semibold">Trials
              <input type="number" min="100" max="200000" step="100" value={trials} onChange={(e) => setTrials(Number(e.target.value))} className="mt-1 w-full rounded-lg px-2 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-sm" />
            </label>
            <div className="text-xs font-semibold flex items-end">
              <button onClick={() => setLiveMode((s) => !s)} className={`w-full px-3 py-2 rounded-lg font-bold ${liveMode ? "bg-red-600 text-white" : "bg-emerald-600 text-white"}`}>
                {liveMode ? "Stop Live Sim" : "Start Live Sim"}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 mt-3">
            <button onClick={rebuildTopology} className="px-3 py-2 rounded-lg bg-slate-700 text-white font-semibold">Build</button>
            <button onClick={runReliability} className="px-3 py-2 rounded-lg bg-blue-700 text-white font-semibold">Reliability</button>
            <button onClick={runSimulation} className="px-3 py-2 rounded-lg bg-orange-600 text-white font-semibold">Simulate</button>
            <button onClick={runCompare} className="px-3 py-2 rounded-lg bg-violet-700 text-white font-semibold">Compare</button>
            <button onClick={runPrediction} className="px-3 py-2 rounded-lg bg-emerald-700 text-white font-semibold">Predict</button>
            <button onClick={runSuggestion} className="px-3 py-2 rounded-lg bg-rose-700 text-white font-semibold">Optimize</button>
          </div>

          <p className="mt-3 text-sm font-medium text-slate-600 dark:text-slate-300">{status}</p>
          <div className="mt-4">
            <GraphCanvas nodes={nodes} edges={networkEdges} edgeRiskMap={edgeRiskMap} simulatedFailed={simFailed} />
          </div>
        </div>

        <aside className="space-y-4">
          <div className="glass border border-slate-200/70 dark:border-slate-700 rounded-2xl p-4 shadow-md">
            <h2 className="font-bold text-lg">Reliability Dashboard</h2>
            {result ? (
              <div className="text-sm mt-2 space-y-1">
                <p>Method: <strong>{result.method}</strong></p>
                <p>Reliability: <strong>{Number(result.reliability).toFixed(6)}</strong></p>
                <p>95% CI: <strong>[{Number(result.ci_low).toFixed(6)}, {Number(result.ci_high).toFixed(6)}]</strong></p>
                <p>Execution: <strong>{Number(result.time_ms).toFixed(2)} ms</strong></p>
              </div>
            ) : <p className="text-sm mt-2 text-slate-600 dark:text-slate-300">Run reliability analysis to populate this panel.</p>}
          </div>

          <div className="glass border border-slate-200/70 dark:border-slate-700 rounded-2xl p-4 shadow-md">
            <h2 className="font-bold text-lg">AI Insight</h2>
            {aiPredictions.length > 0 ? (
              <div className="text-sm mt-2">
                <p>Edges scored: <strong>{aiPredictions.length}</strong></p>
                <ul className="mt-2 space-y-1 max-h-48 overflow-auto">
                  {aiPredictions.slice(0, 6).map((p, idx) => (
                    <li key={idx} className="flex justify-between">
                      <span>({p.edge_u},{p.edge_v})</span>
                      <span className="font-semibold">{(p.failure_risk * 100).toFixed(1)}%</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : <p className="text-sm mt-2 text-slate-600 dark:text-slate-300">Run AI prediction for risk heatmapping.</p>}
          </div>

          <div className="glass border border-slate-200/70 dark:border-slate-700 rounded-2xl p-4 shadow-md">
            <h2 className="font-bold text-lg">Optimization</h2>
            {suggestion ? (
              suggestion.found ? (
                <div className="text-sm mt-2 space-y-1">
                  <p>Recommended Edge: <strong>({suggestion.u}, {suggestion.v})</strong></p>
                  <p>New Reliability: <strong>{Number(suggestion.new_reliability).toFixed(6)}</strong></p>
                  <p>Improvement: <strong>{(Number(suggestion.improvement) * 100).toFixed(2)}%</strong></p>
                </div>
              ) : <p className="text-sm mt-2">{suggestion.message}</p>
            ) : <p className="text-sm mt-2 text-slate-600 dark:text-slate-300">Run optimization to get the best edge-add suggestion.</p>}
          </div>
        </aside>
      </section>

      <section className="glass border border-slate-200/70 dark:border-slate-700 rounded-2xl p-4 shadow-md mt-4">
        <h2 className="font-bold text-lg">Multi-Topology Comparison</h2>
        {comparison.length ? (
          <div className="overflow-x-auto mt-2">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left border-b border-slate-300/70 dark:border-slate-700">
                  <th className="py-2">Topology</th>
                  <th className="py-2">Edges</th>
                  <th className="py-2">Reliability</th>
                  <th className="py-2">Method</th>
                  <th className="py-2">Time (ms)</th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((row) => (
                  <tr key={row.topology} className="border-b border-slate-200/60 dark:border-slate-800">
                    <td className="py-2 font-semibold uppercase">{row.topology}</td>
                    <td className="py-2">{row.edges}</td>
                    <td className="py-2">{Number(row.reliability).toFixed(6)}</td>
                    <td className="py-2">{row.method}</td>
                    <td className="py-2">{Number(row.time_ms).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="text-sm mt-2 text-slate-600 dark:text-slate-300">Run comparison to see topology ranking.</p>}
      </section>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
