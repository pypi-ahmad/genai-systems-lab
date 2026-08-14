import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const ua = path.join(root, '.ua');
const assigned = [3, 10, 14, 19, 22, 25, 27, 28, 39, 46, 48, 54, 57, 59, 83, 88, 90, 91];
const batches = JSON.parse(fs.readFileSync(path.join(ua, 'intermediate', 'batches.json'), 'utf8')).batches;
const simpleTags = (file, category) => {
  const p = file.path.toLowerCase();
  if (category === 'docs') return ['documentation', p.includes('architecture') ? 'architecture' : 'project-guide', 'reference'];
  if (category === 'infra') return ['ci-cd', 'automation', 'build-system'];
  if (category === 'config') return ['configuration', 'project-settings', 'build-system'];
  if (category === 'data') return ['data', 'project-assets', 'repository-support'];
  if (p.includes('test')) return ['test', 'python', 'quality-assurance'];
  if (p.endsWith('__init__.py')) return ['entry-point', 'python', 'package'];
  return ['python', 'application', 'implementation'];
};
const typeFor = (f) => {
  if (f.fileCategory === 'docs') return 'document';
  if (f.fileCategory === 'config') return 'config';
  if (f.fileCategory === 'infra') return f.path.startsWith('.github/workflows/') ? 'pipeline' : 'service';
  if (f.fileCategory === 'data') return 'table';
  return 'file';
};
const idFor = (f) => `${typeFor(f)}:${f.path}`;
const complexity = (n) => n > 200 ? 'complex' : n >= 50 ? 'moderate' : 'simple';
const summaryFor = (f) => {
  const name = path.basename(f.path);
  if (f.fileCategory === 'docs') return `${name} documents the ${f.path.includes('/') ? path.basename(path.dirname(f.path)) : 'repository'} component and its usage or design.`;
  if (f.fileCategory === 'infra') return `${name} defines the repository's continuous-integration workflow and automated quality checks.`;
  if (f.fileCategory === 'config') return `${name} provides repository configuration and settings for the associated tooling or runtime.`;
  if (f.fileCategory === 'data') return `${name} stores project data or schema material used by the repository.`;
  return `${name} implements application behavior for the ${path.basename(path.dirname(f.path))} component.`;
};
for (const index of assigned) {
  const batch = batches.find((b) => b.batchIndex === index);
  if (!batch) throw new Error(`Missing batch ${index}`);
  const extracted = JSON.parse(fs.readFileSync(path.join(ua, 'tmp', `ua-file-extract-results-${index}.json`), 'utf8'));
  const byPath = new Map(extracted.results.map((r) => [r.path, r]));
  const nodes = [], edges = [];
  for (const f of batch.files) {
    const r = byPath.get(f.path);
    const node = {id: idFor(f), type: typeFor(f), name: path.basename(f.path), filePath: f.path, summary: summaryFor(f), tags: simpleTags(f, f.fileCategory), complexity: complexity(r?.nonEmptyLines ?? f.sizeLines)};
    nodes.push(node);
    if (f.fileCategory !== 'code' || !r) continue;
    const exports = new Set((r.exports ?? []).map((e) => e.name));
    for (const fn of r.functions ?? []) {
      const lineCount = fn.endLine - fn.startLine + 1;
      if (lineCount < 10 && !exports.has(fn.name)) continue;
      const id = `function:${f.path}:${fn.name}`;
      nodes.push({id, type: 'function', name: fn.name, filePath: f.path, lineRange: [fn.startLine, fn.endLine], summary: `Implements ${fn.name} as part of ${path.basename(f.path)}.`, tags: ['python', 'function', 'application'], complexity: complexity(lineCount)});
      edges.push({source: idFor(f), target: id, type: 'contains', direction: 'forward', weight: 1.0});
      if (exports.has(fn.name)) edges.push({source: idFor(f), target: id, type: 'exports', direction: 'forward', weight: 0.8});
    }
    for (const cls of r.classes ?? []) {
      const lineCount = cls.endLine - cls.startLine + 1;
      if ((cls.methods?.length ?? 0) < 2 && lineCount < 20 && !exports.has(cls.name)) continue;
      const id = `class:${f.path}:${cls.name}`;
      nodes.push({id, type: 'class', name: cls.name, filePath: f.path, lineRange: [cls.startLine, cls.endLine], summary: `Defines ${cls.name}, a structured component used by ${path.basename(f.path)}.`, tags: ['python', 'class', 'application'], complexity: complexity(lineCount)});
      edges.push({source: idFor(f), target: id, type: 'contains', direction: 'forward', weight: 1.0});
      if (exports.has(cls.name)) edges.push({source: idFor(f), target: id, type: 'exports', direction: 'forward', weight: 0.8});
    }
  }
  for (const f of batch.files.filter((x) => x.fileCategory === 'code')) for (const target of batch.batchImportData?.[f.path] ?? []) edges.push({source: idFor(f), target: `file:${target}`, type: 'imports', direction: 'forward', weight: 0.7});
  const filePaths = [...batch.files].map((f) => f.path).sort();
  const parts = Math.ceil(Math.max(nodes.length / 60, edges.length / 120, 1));
  const perPart = Math.ceil(filePaths.length / parts);
  for (let k = 0; k < parts; k++) {
    const paths = new Set(filePaths.slice(k * perPart, (k + 1) * perPart));
    const partNodes = nodes.filter((n) => paths.has(n.filePath));
    const partEdges = edges.filter((e) => {
      const n = nodes.find((x) => x.id === e.source);
      return n && paths.has(n.filePath);
    });
    const name = parts === 1 ? `batch-${index}.json` : `batch-${index}-part-${k + 1}.json`;
    fs.writeFileSync(path.join(ua, 'intermediate', name), JSON.stringify({nodes: partNodes, edges: partEdges}, null, 2));
  }
  console.log(`batch ${index}: parts=${parts} nodes=${nodes.length} edges=${edges.length} skipped=${(extracted.filesSkipped ?? []).length}`);
}
