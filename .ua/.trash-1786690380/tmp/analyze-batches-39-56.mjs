import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const root = 'D:/AI/Github/genai-systems-lab';
const ua = path.join(root, '.ua');
const extractor = 'C:/Users/ahmad/.understand-anything/repo/understand-anything-plugin/skills/understand/extract-structure.mjs';
const batches = JSON.parse(fs.readFileSync(path.join(ua, 'intermediate', 'batches.json'), 'utf8')).batches
  .filter(({ batchIndex }) => batchIndex >= 39 && batchIndex <= 56);

function complexity(result, file) {
  const n = result?.nonEmptyLines ?? file.sizeLines;
  return n > 200 ? 'complex' : n >= 50 ? 'moderate' : 'simple';
}
function typeFor(file) {
  if (file.fileCategory === 'docs') return 'document';
  if (file.fileCategory === 'config') return 'config';
  if (file.fileCategory === 'data') return 'schema';
  return 'file';
}
function tagsFor(file) {
  const p = file.path.toLowerCase();
  if (file.fileCategory === 'docs') return p.endsWith('readme.md') ? ['documentation', 'entry-point', 'project-guide'] : ['documentation', 'project-guide', 'reference'];
  if (p.includes('graphify-out/cache/ast')) return ['configuration', 'cache', 'analysis-artifact'];
  if (p.includes('graphify-out')) return ['configuration', 'graph-analysis', 'generated-artifact'];
  return ['configuration', 'project-settings', 'metadata'];
}
function summaryFor(file, result) {
  const p = file.path, name = path.basename(p);
  const sections = result?.sections?.map((s) => s.name || s.title || s.key).filter(Boolean) || [];
  const sectionText = sections.length ? ` It covers ${sections.slice(0, 3).join(', ')}${sections.length > 3 ? ', and related topics' : ''}.` : '';
  if (p.endsWith('README.md')) return `Provides the overview and setup guide for the ${p.split('/')[0]} example application.${sectionText}`;
  if (p.endsWith('architecture.md')) return `Describes the architecture, component responsibilities, and execution flow for the ${p.split('/')[0]} application.${sectionText}`;
  if (p.endsWith('tasks.md')) return `Lists the implementation tasks and delivery scope for the ${p.split('/')[0]} application.${sectionText}`;
  if (p.includes('/data/notes/')) return `Stores a knowledge-base note used as source material by the GenAI knowledge OS: ${name.replace(/\.[^.]+$/, '').replaceAll('-', ' ')}.${sectionText}`;
  if (p.endsWith('GRAPH_REPORT.md')) return `Generated Graphify report summarizing repository structure, graph metrics, and analysis findings.${sectionText}`;
  if (p.endsWith('graph.html')) return 'Generated interactive HTML visualization for the repository dependency graph.';
  if (p.endsWith('graph.json')) return 'Generated serialized repository graph containing the analysis nodes, edges, and metadata.';
  if (p.endsWith('manifest.json')) return 'Generated Graphify manifest indexing analyzed repository files and graph artifacts.';
  if (p.endsWith('cost.json')) return 'Records Graphify analysis cost and usage metadata for the generated graph.';
  if (p.endsWith('.graphify_labels.json')) return 'Stores Graphify label metadata used to classify or display generated graph elements.';
  if (p.includes('graphify-out/cache/ast')) return 'Cached Graphify AST extraction artifact used to avoid recomputing source-file structural analysis.';
  return `Defines configuration or generated metadata in ${name}.`;
}
function nodeFor(file, result) {
  const type = typeFor(file);
  return { id: `${type}:${file.path}`, type, name: path.basename(file.path), filePath: file.path,
    summary: summaryFor(file, result), tags: tagsFor(file), complexity: complexity(result, file) };
}
for (const batch of batches) {
  const input = { projectRoot: root, batchFiles: batch.files, batchImportData: batch.batchImportData };
  const inputPath = path.join(ua, 'tmp', `ua-file-analyzer-input-${batch.batchIndex}.json`);
  const resultPath = path.join(ua, 'tmp', `ua-file-extract-results-${batch.batchIndex}.json`);
  fs.writeFileSync(inputPath, JSON.stringify(input));
  execFileSync('node', [extractor, inputPath, resultPath], { stdio: 'inherit' });
  if (!fs.existsSync(resultPath) || fs.statSync(resultPath).size === 0) throw new Error(`missing extraction output for ${batch.batchIndex}`);
  const extracted = JSON.parse(fs.readFileSync(resultPath, 'utf8'));
  if (!extracted.scriptCompleted) throw new Error(`extractor did not complete batch ${batch.batchIndex}`);
  const resultMap = new Map(extracted.results.map((result) => [result.path, result]));
  const nodes = batch.files.map((file) => nodeFor(file, resultMap.get(file.path)));
  const edges = [];
  const output = { nodes, edges };
  const name = `batch-${batch.batchIndex}.json`;
  fs.writeFileSync(path.join(ua, 'intermediate', name), JSON.stringify(output, null, 2) + '\n');
  JSON.parse(fs.readFileSync(path.join(ua, 'intermediate', name), 'utf8'));
}
