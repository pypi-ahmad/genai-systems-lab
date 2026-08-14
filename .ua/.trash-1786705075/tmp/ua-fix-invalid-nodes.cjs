#!/usr/bin/env node
const fs = require('fs');

const graphPath = process.argv[2];
const graph = JSON.parse(fs.readFileSync(graphPath, 'utf8'));
const removedIds = new Set(
  graph.nodes
    .filter(node => (node.type === 'function' || node.type === 'class') && !node.name)
    .map(node => node.id),
);

const beforeEdges = graph.edges.length;
graph.nodes = graph.nodes.filter(node => !removedIds.has(node.id));
graph.edges = graph.edges.filter(edge => !removedIds.has(edge.source) && !removedIds.has(edge.target));
fs.writeFileSync(graphPath, JSON.stringify(graph, null, 2) + '\n');
process.stdout.write(JSON.stringify({
  removedNodes: removedIds.size,
  removedEdges: beforeEdges - graph.edges.length,
  removedIds: [...removedIds],
}, null, 2));
