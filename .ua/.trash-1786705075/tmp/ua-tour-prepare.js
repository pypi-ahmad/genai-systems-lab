const fs = require('fs');

try {
  const [graphPath, layersPath, outputPath] = process.argv.slice(2);
  if (!graphPath || !layersPath || !outputPath) throw new Error('Usage: node ua-tour-prepare.js <graph> <layers> <output>');
  const graph = JSON.parse(fs.readFileSync(graphPath, 'utf8'));
  const layers = JSON.parse(fs.readFileSync(layersPath, 'utf8'));
  const allowed = new Set(['file', 'config', 'document', 'service', 'pipeline', 'table', 'schema', 'resource', 'endpoint']);
  const input = {
    nodes: graph.nodes.filter((node) => allowed.has(node.type)),
    edges: graph.edges,
    layers: layers.map(({ id, name, description }) => ({ id, name, description })),
  };
  fs.writeFileSync(outputPath, JSON.stringify(input, null, 2));
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
