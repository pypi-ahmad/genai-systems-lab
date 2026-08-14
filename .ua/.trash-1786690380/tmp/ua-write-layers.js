const fs = require('fs');
const [graphPath, outputPath] = process.argv.slice(2);
if (!graphPath || !outputPath) throw new Error('Usage: node ua-write-layers.js <graph.json> <layers.json>');
const graph = JSON.parse(fs.readFileSync(graphPath, 'utf8'));
const fileTypes = new Set(['file', 'config', 'document', 'service', 'pipeline', 'table', 'schema', 'resource', 'endpoint']);
const layers = [
  ['layer:applications', 'AI Application Modules', 'Independent GenAI, LangGraph, and CrewAI application modules that implement the repository’s reusable system examples.'],
  ['layer:foundation', 'Shared Foundation', 'Shared configuration, LLM integration, and reusable utilities consumed by the application modules.'],
  ['layer:portfolio', 'Portfolio Experience', 'The portfolio application and its static assets, styles, and scripts for presenting the project collection.'],
  ['layer:benchmarks', 'Benchmarking', 'Promptfoo providers and related benchmark integration code used to evaluate project capabilities.'],
  ['layer:test', 'Test Suite', 'Repository test code validating shared utilities, application behavior, and container contracts.'],
  ['layer:documentation', 'Documentation', 'Project guides, architecture material, changelogs, and other written reference content.'],
  ['layer:infrastructure', 'Infrastructure & CI/CD', 'Container build stages, orchestration, and the GitHub Actions workflow that build and verify the repository.'],
  ['layer:project-support', 'Project Support & Generated Artifacts', 'Project configuration, development metadata, generated graph-analysis artifacts, and tool support files.']
].map(([id, name, description]) => ({ id, name, description, nodeIds: [] }));
const byLayer = new Map(layers.map(layer => [layer.id, layer]));
function assign(n) {
  const p = n.filePath || n.name || '';
  if (n.type === 'document') return 'layer:documentation';
  if (n.type === 'service' || n.type === 'pipeline' || n.type === 'resource') return 'layer:infrastructure';
  if (n.type !== 'file') return 'layer:project-support';
  if (p.startsWith('shared/')) return 'layer:foundation';
  if (p.startsWith('portfolio/')) return 'layer:portfolio';
  if (p.startsWith('benchmarks/')) return 'layer:benchmarks';
  if (p === 'tests' || p.startsWith('tests/')) return 'layer:test';
  if (p.startsWith('graphify-out/') || p.startsWith('.ua/') || p.startsWith('.codex/') || p.startsWith('.')) return 'layer:project-support';
  if (p.includes('/tests/') || /(^|\/)test_[^/]+\.py$/i.test(p) || /_test\.[^.]+$/i.test(p)) return 'layer:test';
  return p.includes('/') ? 'layer:applications' : 'layer:project-support';
}
for (const n of graph.nodes) if (fileTypes.has(n.type)) byLayer.get(assign(n)).nodeIds.push(n.id);
const result = layers.filter(layer => layer.nodeIds.length);
const ids = result.flatMap(layer => layer.nodeIds);
if (new Set(ids).size !== ids.length || ids.length !== graph.nodes.filter(n => fileTypes.has(n.type)).length) throw new Error('Layer assignment is incomplete or duplicates node IDs');
fs.writeFileSync(outputPath, JSON.stringify(result, null, 2) + '\n');
