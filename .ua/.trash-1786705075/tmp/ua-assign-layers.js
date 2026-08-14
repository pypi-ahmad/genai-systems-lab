const fs = require('fs');

const input = JSON.parse(fs.readFileSync('.ua/tmp/ua-arch-input.json', 'utf8'));
const nodes = input.fileNodes;
const layerDefs = [
  ['layer:shared-runtime', 'Shared Runtime Layer', 'Shared Python runtime services, LLM integrations, security helpers, observability, and reusable UI support used across the AI systems.'],
  ['layer:portfolio-ui', 'Portfolio UI Layer', 'Next.js portfolio pages, client components, and presentation assets for exploring the shared AI systems.'],
  ['layer:genai-systems', 'Generative AI Systems Layer', 'Standalone generative-AI application modules covering research, knowledge, document intelligence, clinical, financial, browser, code, interview, UI, and NL2SQL workflows.'],
  ['layer:langgraph-systems', 'LangGraph Systems Layer', 'LangGraph-based agent workflows, graph nodes, planners, executors, and supporting application code.'],
  ['layer:crewai-systems', 'CrewAI Systems Layer', 'CrewAI multi-agent applications defining agents, tasks, crews, and runnable collaborative workflows.'],
  ['layer:quality-evaluation', 'Quality and Evaluation Layer', 'Pytest coverage and executable benchmark providers used to verify runtime behavior and compare system quality.'],
  ['layer:data', 'Data Layer', 'Database migration assets and extracted tabular data definitions that support persistent system state.'],
  ['layer:documentation', 'Documentation Layer', 'Project guides, module READMEs, architecture references, and generated reports for users and maintainers.'],
  ['layer:infrastructure', 'Infrastructure and CI Layer', 'Container build definitions, Docker support files, repository automation, and continuous-integration workflows.'],
  ['layer:project-support', 'Project Support and Generated Artifacts Layer', 'Project configuration, tooling metadata, generated graph artifacts, and analysis support files that enable development and repository maintenance.'],
];
const buckets = new Map(layerDefs.map(([id]) => [id, []]));
function group(n) { const p=(n.filePath||n.name||'').replace(/\\/g,'/'); return p.includes('/') ? p.split('/')[0] : 'root'; }
function pick(n) {
  const p=(n.filePath||n.name||'').replace(/\\/g,'/'); const g=group(n);
  if (n.type === 'document' || g === 'docs') return 'layer:documentation';
  if (n.type === 'service' || n.type === 'pipeline' || n.type === 'resource' || g === '.github') return 'layer:infrastructure';
  if (n.type === 'table' || n.type === 'schema' || n.type === 'endpoint' || g === 'migrations') return 'layer:data';
  if (g === 'shared') return 'layer:shared-runtime';
  if (g === 'portfolio') return 'layer:portfolio-ui';
  if (g.startsWith('genai-')) return 'layer:genai-systems';
  if (g.startsWith('lg-') || g === 'langgraph-data-analyst') return 'layer:langgraph-systems';
  if (g.startsWith('crew-')) return 'layer:crewai-systems';
  if (g === 'tests' || g === 'benchmarks') return 'layer:quality-evaluation';
  return 'layer:project-support';
}
for (const n of nodes) buckets.get(pick(n)).push(n.id);
const layers = layerDefs.map(([id, name, description]) => ({id, name, description, nodeIds: buckets.get(id)})).filter(x => x.nodeIds.length);
const assigned = layers.flatMap(x => x.nodeIds); const expected = new Set(nodes.map(n => n.id));
const missing = [...expected].filter(id => !assigned.includes(id));
const duplicate = assigned.filter((id, i) => assigned.indexOf(id) !== i);
const invented = assigned.filter(id => !expected.has(id));
if (layers.length < 3 || layers.length > 10 || missing.length || duplicate.length || invented.length || assigned.length !== nodes.length) {
  throw new Error(JSON.stringify({layers:layers.length, expected:nodes.length, assigned:assigned.length, missing, duplicate, invented}));
}
fs.writeFileSync('.ua/intermediate/layers.json', JSON.stringify(layers, null, 2) + '\n');
console.log(JSON.stringify(layers.map(x => ({name:x.name,count:x.nodeIds.length}))));
