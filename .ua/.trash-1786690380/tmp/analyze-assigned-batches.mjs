import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const root = process.cwd();
const ua = path.join(root, '.ua');
const all = JSON.parse(fs.readFileSync(path.join(ua, 'intermediate', 'batches.json'), 'utf8'));
const extractor = 'C:/Users/ahmad/.understand-anything/repo/understand-anything-plugin/skills/understand/extract-structure.mjs';
const batches = all.batches.filter((b) => b.batchIndex >= 57 && b.batchIndex <= 74);

function fileType(f) {
  if (f.fileCategory === 'config') return 'config';
  if (f.fileCategory === 'docs') return 'document';
  if (f.fileCategory === 'infra') return /(^|\/)(Dockerfile|docker-compose)/i.test(f.path) ? 'service' : /\.github\/workflows|gitlab-ci|Jenkinsfile|circleci/i.test(f.path) ? 'pipeline' : 'resource';
  if (f.fileCategory === 'data') return /\.(graphql|proto|prisma)$/i.test(f.path) ? 'schema' : /openapi|swagger/i.test(f.path) ? 'endpoint' : /\.sql$/i.test(f.path) ? 'table' : 'file';
  return 'file';
}
function fileTags(f) {
  if (/test|spec/i.test(f.path)) return ['test', 'verification', 'python'];
  if (f.fileCategory === 'config') return ['configuration', f.language || 'data', 'project-settings'];
  if (f.fileCategory === 'docs') return ['documentation', 'project-reference', 'guidance'];
  if (f.fileCategory === 'data') return ['data', 'dataset', f.language || 'structured-data'];
  if (f.fileCategory === 'infra') return ['infrastructure', 'deployment', 'configuration'];
  if (f.fileCategory === 'markup') return ['frontend', 'styling', 'ui'];
  if (/__init__\.py$/.test(f.path)) return ['python', 'package', 'entry-point'];
  if (/config|\.config\./i.test(f.path)) return ['configuration', 'build-system', f.language || 'code'];
  return ['code', f.language || 'unknown', 'implementation'];
}
function complexity(lines) { return lines > 200 ? 'complex' : lines >= 50 ? 'moderate' : 'simple'; }
function fileSummary(f, r) {
  const names = [...(r.functions || []).map(x => x.name), ...(r.classes || []).map(x => x.name)].slice(0, 4);
  if (f.fileCategory === 'config') return `Defines project configuration stored in ${f.path}.`;
  if (f.fileCategory === 'docs') return `Documents the project material contained in ${f.path}.`;
  if (f.fileCategory === 'data') return `Stores structured ${f.language || 'data'} used by the project.`;
  if (f.fileCategory === 'markup') return `Provides frontend markup or styling rules for the application interface.`;
  if (/__init__\.py$/.test(f.path)) return `Marks ${path.dirname(f.path)} as a Python package${names.length ? ` and exposes package-level definitions` : ''}.`;
  return names.length ? `Implements ${names.join(', ')} for this project component.` : `Provides the ${f.language || 'source'} implementation for this project component.`;
}
function functionNode(f, x) {
  return { id: `function:${f.path}:${x.name}`, type: 'function', name: x.name, filePath: f.path, lineRange: [x.startLine, x.endLine], summary: `Implements ${x.name} for the ${path.basename(f.path)} component.`, tags: [/test|spec/i.test(f.path) ? 'test' : 'function', 'python', 'implementation'], complexity: complexity((x.endLine || x.startLine) - x.startLine + 1) };
}
function classNode(f, x) {
  const end = x.endLine || x.startLine;
  return { id: `class:${f.path}:${x.name}`, type: 'class', name: x.name, filePath: f.path, lineRange: [x.startLine, end], summary: `Encapsulates ${x.name} behavior for the ${path.basename(f.path)} component.`, tags: ['class', 'python', 'implementation'], complexity: complexity(end - x.startLine + 1) };
}
for (const b of batches) {
  const input = { projectRoot: root, batchFiles: b.files, batchImportData: b.batchImportData };
  const inputPath = path.join(ua, 'tmp', `ua-file-analyzer-input-${b.batchIndex}.json`);
  const resultPath = path.join(ua, 'tmp', `ua-file-extract-results-${b.batchIndex}.json`);
  fs.writeFileSync(inputPath, JSON.stringify(input));
  execFileSync('node', [extractor, inputPath, resultPath], { stdio: 'inherit' });
  if (!fs.existsSync(resultPath) || !fs.statSync(resultPath).size) throw new Error(`Missing extraction result for ${b.batchIndex}`);
  const extracted = JSON.parse(fs.readFileSync(resultPath, 'utf8'));
  if (!extracted.scriptCompleted) throw new Error(`Extractor did not complete batch ${b.batchIndex}`);
  const resultByPath = new Map(extracted.results.map((r) => [r.path, r]));
  const nodes = [], edges = [];
  for (const f of b.files) {
    const r = resultByPath.get(f.path) || { functions: [], classes: [], exports: [], totalLines: f.sizeLines };
    const type = fileType(f), id = `${type}:${f.path}`;
    nodes.push({ id, type, name: path.basename(f.path), filePath: f.path, summary: fileSummary(f, r), tags: fileTags(f), complexity: complexity(r.nonEmptyLines ?? r.totalLines ?? f.sizeLines) });
    if (f.fileCategory === 'code') {
      const exported = new Set((r.exports || []).map(x => x.name));
      for (const fn of r.functions || []) {
        if ((fn.endLine - fn.startLine + 1 >= 10) || exported.has(fn.name)) {
          const n = functionNode(f, fn); nodes.push(n);
          edges.push({ source: id, target: n.id, type: 'contains', direction: 'forward', weight: 1.0 });
          if (exported.has(fn.name)) edges.push({ source: id, target: n.id, type: 'exports', direction: 'forward', weight: 0.8 });
        }
      }
      for (const cl of r.classes || []) {
        const end = cl.endLine || cl.startLine;
        if ((end - cl.startLine + 1 >= 20) || (cl.methods || []).length >= 2 || exported.has(cl.name)) {
          const n = classNode(f, cl); nodes.push(n);
          edges.push({ source: id, target: n.id, type: 'contains', direction: 'forward', weight: 1.0 });
          if (exported.has(cl.name)) edges.push({ source: id, target: n.id, type: 'exports', direction: 'forward', weight: 0.8 });
        }
      }
      for (const targetPath of b.batchImportData[f.path] || []) edges.push({ source: id, target: `file:${targetPath}`, type: 'imports', direction: 'forward', weight: 0.7 });
    }
  }
  const parts = Math.ceil(Math.max(nodes.length / 60, edges.length / 120, 1));
  const groups = [];
  const paths = [...b.files].map(f => f.path).sort();
  const chunk = Math.ceil(paths.length / parts);
  for (let i = 0; i < parts; i++) groups.push(new Set(paths.slice(i * chunk, (i + 1) * chunk)));
  for (let i = 0; i < parts; i++) {
    const group = groups[i];
    const partNodes = nodes.filter(n => group.has(n.filePath));
    const ids = new Set(partNodes.map(n => n.id));
    const partEdges = edges.filter(e => ids.has(e.source));
    const out = path.join(ua, 'intermediate', parts === 1 ? `batch-${b.batchIndex}.json` : `batch-${b.batchIndex}-part-${i + 1}.json`);
    fs.writeFileSync(out, JSON.stringify({ nodes: partNodes, edges: partEdges }, null, 2) + '\n');
    JSON.parse(fs.readFileSync(out, 'utf8'));
  }
  console.log(`batch ${b.batchIndex}: ${nodes.length} nodes, ${edges.length} edges, ${parts} part(s)`);
}
