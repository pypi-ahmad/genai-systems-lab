const fs = require('fs');

function countBy(nodes, edges, key) {
  const counts = new Map(nodes.map((node) => [node.id, 0]));
  for (const edge of edges) {
    const id = edge[key];
    if (counts.has(id)) counts.set(id, counts.get(id) + 1);
  }
  return counts;
}

function rank(nodes, counts, label) {
  return nodes.map((node) => ({ id: node.id, [label]: counts.get(node.id) || 0, name: node.name }))
    .sort((a, b) => b[label] - a[label] || a.id.localeCompare(b.id)).slice(0, 20);
}

function filePath(node) { return node.filePath || node.name || node.id.split(':').slice(1).join(':'); }

try {
  const [inputPath, outputPath] = process.argv.slice(2);
  if (!inputPath || !outputPath) throw new Error('Usage: node ua-tour-analyze.js <input> <output>');
  const { nodes, edges, layers } = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));
  const fanIn = countBy(nodes, edges, 'target');
  const fanOut = countBy(nodes, edges, 'source');
  const fanOutValues = [...fanOut.values()].sort((a, b) => a - b);
  const fanInValues = [...fanIn.values()].sort((a, b) => a - b);
  const highFanOut = fanOutValues[Math.max(0, Math.ceil(fanOutValues.length * 0.9) - 1)] || 0;
  const lowFanIn = fanInValues[Math.max(0, Math.floor((fanInValues.length - 1) * 0.25))] || 0;
  const entryNames = new Set(['index.ts','index.js','main.ts','main.js','app.ts','app.js','server.ts','server.js','mod.rs','main.go','main.py','main.rs','manage.py','app.py','wsgi.py','asgi.py','run.py','__main__.py','Application.java','Main.java','Program.cs','config.ru','index.php','App.swift','Application.kt','main.cpp','main.c']);
  const entryPointCandidates = nodes.map((node) => {
    const path = filePath(node).replaceAll('\\\\', '/');
    const base = path.split('/').pop();
    const depth = path.split('/').length;
    let score = 0;
    if (node.type === 'document') {
      if (path === 'README.md') score += 5;
      else if (path.endsWith('.md') && depth === 1) score += 2;
    } else if (node.type === 'file') {
      if (entryNames.has(base)) score += 3;
      if (depth <= 2) score += 1;
      if ((fanOut.get(node.id) || 0) >= highFanOut) score += 1;
      if ((fanIn.get(node.id) || 0) <= lowFanIn) score += 1;
    }
    return { id: node.id, score, name: node.name, summary: node.summary };
  }).filter((node) => node.score > 0).sort((a, b) => b.score - a.score || a.id.localeCompare(b.id)).slice(0, 5);
  const start = entryPointCandidates.find((candidate) => nodeMap.get(candidate.id)?.type === 'file')?.id || null;
  const adjacent = new Map(nodes.map((node) => [node.id, []]));
  for (const edge of edges) {
    if ((edge.type === 'imports' || edge.type === 'calls') && adjacent.has(edge.source) && adjacent.has(edge.target)) adjacent.get(edge.source).push(edge.target);
  }
  const order = [], depthMap = {}, byDepth = {};
  if (start) {
    const queue = [start]; depthMap[start] = 0;
    for (let i = 0; i < queue.length; i++) {
      const id = queue[i], depth = depthMap[id]; order.push(id);
      (byDepth[depth] ||= []).push(id);
      for (const target of adjacent.get(id) || []) if (!(target in depthMap)) { depthMap[target] = depth + 1; queue.push(target); }
    }
  }
  const pick = (types) => nodes.filter((node) => types.includes(node.type)).map(({ id, name, type, summary }) => ({ id, name, type, summary }));
  const directed = new Set(edges.filter((edge) => nodeMap.has(edge.source) && nodeMap.has(edge.target)).map((edge) => `${edge.source}\u0000${edge.target}\u0000${edge.type}`));
  const clusters = [];
  const seen = new Set();
  for (const edge of edges) {
    if (!nodeMap.has(edge.source) || !nodeMap.has(edge.target) || !['imports', 'calls'].includes(edge.type)) continue;
    const reverse = `${edge.target}\u0000${edge.source}\u0000${edge.type}`;
    if (!directed.has(reverse)) continue;
    const members = [edge.source, edge.target].sort(); const key = members.join('|');
    if (seen.has(key)) continue; seen.add(key);
    clusters.push({ nodes: members, edgeCount: edges.filter((e) => members.includes(e.source) && members.includes(e.target)).length });
  }
  const result = {
    scriptCompleted: true,
    entryPointCandidates,
    fanInRanking: rank(nodes, fanIn, 'fanIn'),
    fanOutRanking: rank(nodes, fanOut, 'fanOut'),
    bfsTraversal: { startNode: start, order, depthMap, byDepth },
    nonCodeFiles: { documentation: pick(['document']), infrastructure: pick(['service', 'pipeline', 'resource']), data: pick(['table', 'schema', 'endpoint']), config: pick(['config']) },
    clusters: clusters.sort((a, b) => b.edgeCount - a.edgeCount).slice(0, 10),
    layers: { count: layers.length, list: layers.map(({ id, name, description }) => ({ id, name, description })) },
    nodeSummaryIndex: Object.fromEntries(nodes.map(({ id, name, type, summary }) => [id, { name, type, summary }])),
    totalNodes: nodes.length,
    totalEdges: edges.length,
  };
  fs.writeFileSync(outputPath, JSON.stringify(result, null, 2));
} catch (error) {
  console.error(error.stack || error.message);
  process.exit(1);
}
