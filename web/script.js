const svg = document.getElementById("graphSvg");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

const controls = {
  topology: document.getElementById("topology"),
  nodes: document.getElementById("nodes"),
  edgeProb: document.getElementById("edgeProb"),
  trials: document.getElementById("trials"),
  nodeA: document.getElementById("nodeA"),
  nodeB: document.getElementById("nodeB"),
};

const state = {
  n: 8,
  p: 0.9,
  topology: "ring",
  edges: [],
  active: [],
  selectedNodes: [],
};

function clamp(x, lo, hi) {
  return Math.max(lo, Math.min(hi, x));
}

function edgeKey(u, v) {
  const a = Math.min(u, v);
  const b = Math.max(u, v);
  return `${a}-${b}`;
}

function buildEdges(topology, n, p) {
  const edges = [];
  if (n <= 1) return edges;

  if (topology === "star") {
    for (let v = 1; v < n; v++) edges.push({ u: 0, v, p });
  } else if (topology === "ring") {
    for (let u = 0; u < n; u++) {
      const v = (u + 1) % n;
      const a = Math.min(u, v);
      const b = Math.max(u, v);
      if (!edges.some((e) => e.u === a && e.v === b)) edges.push({ u: a, v: b, p });
    }
  } else if (topology === "mesh") {
    for (let u = 0; u < n; u++) {
      for (let v = u + 1; v < n; v++) edges.push({ u, v, p });
    }
  } else if (topology === "tree") {
    for (let v = 1; v < n; v++) edges.push({ u: Math.floor((v - 1) / 2), v, p });
  }
  return edges;
}

function randomActive(edges) {
  return edges.map((e) => Math.random() < e.p);
}

function isConnected(n, edges, active) {
  if (n <= 1) return true;
  const adj = Array.from({ length: n }, () => []);
  edges.forEach((e, i) => {
    if (!active[i]) return;
    adj[e.u].push(e.v);
    adj[e.v].push(e.u);
  });
  const q = [0];
  const seen = Array(n).fill(false);
  seen[0] = true;
  let idx = 0;
  while (idx < q.length) {
    const cur = q[idx++];
    adj[cur].forEach((nx) => {
      if (!seen[nx]) {
        seen[nx] = true;
        q.push(nx);
      }
    });
  }
  return seen.every(Boolean);
}

function monteCarlo(n, edges, trials) {
  let success = 0;
  for (let t = 0; t < trials; t++) {
    const active = randomActive(edges);
    if (isConnected(n, edges, active)) success++;
  }
  const r = success / trials;
  const margin = 1.96 * Math.sqrt((r * (1 - r)) / trials);
  return { reliability: r, low: clamp(r - margin, 0, 1), high: clamp(r + margin, 0, 1) };
}

function layoutByTopology(topology, n, width, height) {
  if (n <= 0) return [];
  if (topology === "star") {
    const coords = [{ x: width / 2, y: height / 2 }];
    const radius = Math.min(width, height) * 0.35;
    for (let i = 1; i < n; i++) {
      const theta = (2 * Math.PI * (i - 1)) / Math.max(1, n - 1) - Math.PI / 2;
      coords.push({ x: width / 2 + radius * Math.cos(theta), y: height / 2 + radius * Math.sin(theta) });
    }
    return coords;
  }
  if (topology === "tree") {
    const coords = new Array(n);
    const levels = [];
    for (let i = 0; i < n; i++) {
      const lvl = Math.floor(Math.log2(i + 1));
      if (!levels[lvl]) levels[lvl] = [];
      levels[lvl].push(i);
    }
    const topPad = 70;
    const bottomPad = 60;
    const usableHeight = Math.max(80, height - topPad - bottomPad);
    levels.forEach((nodesAtLevel, level) => {
      const y = topPad + (level * usableHeight) / Math.max(1, levels.length - 1);
      nodesAtLevel.forEach((nodeId, idx) => {
        const x = ((idx + 1) * width) / (nodesAtLevel.length + 1);
        coords[nodeId] = { x, y };
      });
    });
    return coords;
  }

  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) * (topology === "mesh" ? 0.33 : 0.36);
  const coords = [];
  for (let i = 0; i < n; i++) {
    const theta = (2 * Math.PI * i) / n - Math.PI / 2;
    coords.push({ x: cx + radius * Math.cos(theta), y: cy + radius * Math.sin(theta) });
  }
  return coords;
}

function clearSvg() {
  while (svg.firstChild) svg.removeChild(svg.firstChild);
}

function drawEdgeLabel(x, y, text) {
  const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
  label.setAttribute("x", x);
  label.setAttribute("y", y);
  label.setAttribute("text-anchor", "middle");
  label.setAttribute("font-size", "10");
  label.setAttribute("font-family", "Space Grotesk, sans-serif");
  label.setAttribute("font-weight", "600");
  label.setAttribute("fill", "#374151");
  label.textContent = text;
  svg.appendChild(label);
}

function drawGraph() {
  clearSvg();
  const width = 900;
  const height = 520;
  const coords = layoutByTopology(state.topology, state.n, width, height);

  const activeCount = state.active.filter(Boolean).length;

  state.edges.forEach((e, i) => {
    const x1 = coords[e.u].x;
    const y1 = coords[e.u].y;
    const x2 = coords[e.v].x;
    const y2 = coords[e.v].y;

    const lineGlow = document.createElementNS("http://www.w3.org/2000/svg", "line");
    lineGlow.setAttribute("x1", x1);
    lineGlow.setAttribute("y1", y1);
    lineGlow.setAttribute("x2", x2);
    lineGlow.setAttribute("y2", y2);
    lineGlow.setAttribute("stroke-width", state.active[i] ? "7" : "5");
    lineGlow.setAttribute("stroke", state.active[i] ? "rgba(15,118,110,0.16)" : "rgba(220,38,38,0.14)");
    lineGlow.setAttribute("stroke-linecap", "round");
    svg.appendChild(lineGlow);

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", x1);
    line.setAttribute("y1", y1);
    line.setAttribute("x2", x2);
    line.setAttribute("y2", y2);
    line.setAttribute("stroke-width", state.active[i] ? "3.4" : "2.4");
    line.setAttribute("stroke", state.active[i] ? "#0f766e" : "#dc2626");
    line.setAttribute("stroke-linecap", "round");
    line.setAttribute("stroke-dasharray", state.active[i] ? "0" : "7 5");
    line.setAttribute("opacity", "0.95");
    svg.appendChild(line);

    drawEdgeLabel((x1 + x2) / 2, (y1 + y2) / 2 - 4, e.p.toFixed(2));
  });

  for (let i = 0; i < state.n; i++) {
    const isSelected = state.selectedNodes.includes(i);
    if (isSelected) {
      const halo = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      halo.setAttribute("cx", coords[i].x);
      halo.setAttribute("cy", coords[i].y);
      halo.setAttribute("r", "24");
      halo.setAttribute("fill", "rgba(245, 158, 11, 0.22)");
      svg.appendChild(halo);
    }

    const node = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    node.setAttribute("cx", coords[i].x);
    node.setAttribute("cy", coords[i].y);
    node.setAttribute("r", "17");
    node.setAttribute("fill", isSelected ? "#fde68a" : "#f9f7ee");
    node.setAttribute("stroke", isSelected ? "#d97706" : "#1f2937");
    node.setAttribute("stroke-width", isSelected ? "2.6" : "1.8");
    node.style.cursor = "pointer";
    node.addEventListener("click", () => selectNodeFromGraph(i));
    svg.appendChild(node);

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", coords[i].x);
    label.setAttribute("y", coords[i].y + 4);
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("font-size", "12");
    label.setAttribute("font-family", "Space Grotesk, sans-serif");
    label.setAttribute("font-weight", "700");
    label.style.cursor = "pointer";
    label.textContent = String(i);
    label.addEventListener("click", () => selectNodeFromGraph(i));
    svg.appendChild(label);
  }

  const connectedNow = isConnected(state.n, state.edges, state.active);
  statusEl.textContent =
    `Topology: ${state.topology.toUpperCase()} | Nodes=${state.n} | Edges=${state.edges.length} | ` +
    `Active=${activeCount}/${state.edges.length} | ${connectedNow ? "CONNECTED" : "DISCONNECTED"}`;
}

function rebuildNodeSelectors() {
  controls.nodeA.innerHTML = "";
  controls.nodeB.innerHTML = "";
  for (let i = 0; i < state.n; i++) {
    const optionA = document.createElement("option");
    optionA.value = String(i);
    optionA.textContent = String(i);
    controls.nodeA.appendChild(optionA);

    const optionB = document.createElement("option");
    optionB.value = String(i);
    optionB.textContent = String(i);
    controls.nodeB.appendChild(optionB);
  }
  if (state.n > 1) {
    controls.nodeA.value = "0";
    controls.nodeB.value = "1";
  }
}

function syncSelectedWithDropdowns() {
  const a = parseInt(controls.nodeA.value, 10);
  const b = parseInt(controls.nodeB.value, 10);
  if (Number.isInteger(a) && Number.isInteger(b) && a !== b) {
    state.selectedNodes = [a, b];
  } else if (Number.isInteger(a)) {
    state.selectedNodes = [a];
  } else {
    state.selectedNodes = [];
  }
  drawGraph();
}

function findEdgeIndex(u, v) {
  return state.edges.findIndex((e) => (e.u === u && e.v === v) || (e.u === v && e.v === u));
}

function setAllActive() {
  state.active = state.edges.map(() => true);
}

function selectNodeFromGraph(nodeId) {
  if (state.selectedNodes.length === 0) {
    state.selectedNodes = [nodeId];
  } else if (state.selectedNodes.length === 1) {
    if (state.selectedNodes[0] === nodeId) {
      state.selectedNodes = [];
    } else {
      state.selectedNodes.push(nodeId);
    }
  } else {
    state.selectedNodes = [nodeId];
  }

  if (state.selectedNodes.length >= 1) controls.nodeA.value = String(state.selectedNodes[0]);
  if (state.selectedNodes.length >= 2) controls.nodeB.value = String(state.selectedNodes[1]);
  drawGraph();
}

function editEdge(addMode) {
  const a = parseInt(controls.nodeA.value, 10);
  const b = parseInt(controls.nodeB.value, 10);
  if (!Number.isInteger(a) || !Number.isInteger(b) || a < 0 || b < 0 || a >= state.n || b >= state.n) {
    statusEl.textContent = "Invalid node selection.";
    return;
  }
  if (a === b) {
    statusEl.textContent = "Choose two different nodes.";
    return;
  }

  const u = Math.min(a, b);
  const v = Math.max(a, b);
  const idx = findEdgeIndex(u, v);

  if (addMode) {
    if (idx >= 0) {
      state.edges[idx].p = state.p;
      statusEl.textContent = `Updated link (${u}, ${v}) probability to ${state.p.toFixed(2)}.`;
    } else {
      state.edges.push({ u, v, p: state.p });
      statusEl.textContent = `Added link (${u}, ${v}) with p=${state.p.toFixed(2)}.`;
    }
  } else if (idx >= 0) {
    state.edges.splice(idx, 1);
    statusEl.textContent = `Removed link (${u}, ${v}).`;
  } else {
    statusEl.textContent = `Link (${u}, ${v}) does not exist.`;
  }

  setAllActive();
  state.selectedNodes = [u, v];
  drawGraph();
}

function refreshFromControls() {
  state.topology = controls.topology.value;
  state.n = clamp(parseInt(controls.nodes.value, 10) || 1, 1, 30);
  state.p = clamp(parseFloat(controls.edgeProb.value) || 0, 0, 1);
  state.edges = buildEdges(state.topology, state.n, state.p);
  setAllActive();
  state.selectedNodes = [];
  rebuildNodeSelectors();
  drawGraph();
}

function runFailureStep() {
  state.active = randomActive(state.edges);
  const connected = isConnected(state.n, state.edges, state.active);
  drawGraph();
  const up = state.active.filter(Boolean).length;
  resultsEl.textContent = [
    "Single-trial simulation",
    `Topology: ${state.topology}`,
    `Nodes: ${state.n}`,
    `Connected: ${connected}`,
    `Active edges: ${up}/${state.edges.length}`,
    "",
    "Tip: select Node A and Node B to add/remove links and test reliability changes quickly.",
  ].join("\n");
}

function runMonteCarloEstimate() {
  const trials = clamp(parseInt(controls.trials.value, 10) || 1000, 100, 200000);
  const estimate = monteCarlo(state.n, state.edges, trials);
  resultsEl.textContent = [
    "Monte Carlo estimate",
    `Topology: ${state.topology}`,
    `Nodes: ${state.n}, Edges: ${state.edges.length}`,
    `Trials: ${trials}`,
    `Reliability: ${estimate.reliability.toFixed(6)}`,
    `95% CI: [${estimate.low.toFixed(6)}, ${estimate.high.toFixed(6)}]`,
  ].join("\n");
}

function compareTopologies() {
  const n = clamp(parseInt(controls.nodes.value, 10) || 1, 1, 30);
  const p = clamp(parseFloat(controls.edgeProb.value) || 0, 0, 1);
  const trials = clamp(parseInt(controls.trials.value, 10) || 1000, 100, 200000);

  const names = ["star", "ring", "mesh", "tree"];
  const rows = names.map((name) => {
    const edges = buildEdges(name, n, p);
    const est = monteCarlo(n, edges, trials);
    return {
      topology: name,
      edges: edges.length,
      reliability: est.reliability,
    };
  });

  rows.sort((a, b) => b.reliability - a.reliability);
  resultsEl.textContent = [
    "Topology comparison (Monte Carlo)",
    `Nodes=${n}, p=${p.toFixed(2)}, trials=${trials}`,
    "",
    ...rows.map((r) => `${r.topology.padEnd(6)} | edges=${String(r.edges).padStart(3)} | R=${r.reliability.toFixed(6)}`),
    "",
    `Best: ${rows[0].topology.toUpperCase()}`,
    `Worst: ${rows[rows.length - 1].topology.toUpperCase()}`,
  ].join("\n");
}

document.getElementById("buildBtn").addEventListener("click", refreshFromControls);
document.getElementById("simulateBtn").addEventListener("click", runFailureStep);
document.getElementById("monteBtn").addEventListener("click", runMonteCarloEstimate);
document.getElementById("compareBtn").addEventListener("click", compareTopologies);
document.getElementById("addEdgeBtn").addEventListener("click", () => editEdge(true));
document.getElementById("removeEdgeBtn").addEventListener("click", () => editEdge(false));
controls.nodeA.addEventListener("change", syncSelectedWithDropdowns);
controls.nodeB.addEventListener("change", syncSelectedWithDropdowns);

refreshFromControls();
