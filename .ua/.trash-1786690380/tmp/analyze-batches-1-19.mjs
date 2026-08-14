import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const root = process.cwd();
const ua = path.join(root, '.ua');
const batches = JSON.parse(fs.readFileSync(path.join(ua, 'intermediate', 'batches.json'), 'utf8')).batches
  .filter((batch) => batch.batchIndex >= 1 && batch.batchIndex <= 19);
const extractor = 'C:/Users/ahmad/.understand-anything/repo/understand-anything-plugin/skills/understand/extract-structure.mjs';

function complexity(lines, count = 0) {
  return lines > 200 || count > 12 ? 'complex' : lines >= 50 || count > 4 ? 'moderate' : 'simple';
}
function typeFor(file) {
  const p = file.path.toLowerCase();
  if (file.fileCategory === 'config') return 'config';
  if (file.fileCategory === 'docs') return 'document';
  if (file.fileCategory === 'infra') return p.includes('.github/workflows') || p.includes('gitlab-ci') || p.includes('jenkins') ? 'pipeline' : p.endsWith('.tf') ? 'resource' : 'service';
  if (file.fileCategory === 'data') return p.endsWith('.sql') ? 'table' : p.includes('openapi') || p.includes('swagger') ? 'endpoint' : 'schema';
  return 'file';
}
function idFor(file) { return `${typeFor(file)}:${file.path}`; }
function baseTags(file, result) {
  const p = file.path.toLowerCase(), category = file.fileCategory;
  if (category === 'docs') return ['documentation','project-guide','reference'];
  if (category === 'config') return ['configuration','project-settings','build-system'];
  if (category === 'infra') return p.includes('workflow') ? ['ci-cd','automation','deployment'] : ['infrastructure','deployment','configuration'];
  if (category === 'data') return ['schema-definition','data-model','api-schema'];
  if (p.includes('test')) return ['test','verification','automation'];
  if (p.includes('/nodes/')) return ['langgraph','workflow-node','agent'];
  if (p.endsWith('/main.py') || p.endsWith('/main.ts') || p.endsWith('/page.tsx')) return ['entry-point','application','interface'];
  if (p.includes('state')) return ['state-management','type-definition','workflow'];
  if (p.includes('agent')) return ['agent','llm','service'];
  if (p.endsWith('__init__.py')) return ['entry-point','package','barrel'];
  if (p.endsWith('.tsx')) return ['component','react','interface'];
  return ['application','utility','service'];
}
function fileSummary(file, result) {
  const p = file.path, name = path.basename(p), cat = file.fileCategory;
  if (cat === 'docs') return `Documents the ${name} content and its role within the project.`;
  if (cat === 'config') return `Configures project behavior defined by ${name}.`;
  if (cat === 'infra') return `Defines infrastructure or automation declared in ${name}.`;
  if (cat === 'data') return `Defines the data structure or schema represented by ${name}.`;
  if (p.includes('/nodes/')) return `Implements the ${name.replace(/\.[^.]+$/, '')} workflow node for its LangGraph-based agent.`;
  if (p.includes('/tests/') || p.includes('/test_') || p.includes('test_')) return `Tests behavior exposed by the corresponding application modules.`;
  if (name === 'main.py') return `Provides the runnable entry point for this example application.`;
  if (name === 'graph.py') return `Builds the application workflow graph and connects its processing nodes.`;
  if (name === 'state.py') return `Defines shared workflow state and typed data exchanged between nodes.`;
  if (name === 'agents.py') return `Creates the specialized AI agents used by this application.`;
  if (name === 'tasks.py') return `Defines task prompts and task objects coordinated by the application crew.`;
  if (name === 'crew.py') return `Composes agents and tasks into the application crew workflow.`;
  return `Implements ${name} as part of the ${p.split('/')[0]} application.`;
}
function fnSummary(name, file) {
  if (name === 'run' || name === 'main') return 'Runs the application workflow and returns its result.';
  if (/build|create|make/i.test(name)) return `Builds the ${name.replace(/^(build|create|make)/i, '').replace(/([A-Z])/g, ' $1').trim() || 'application'} structure.`;
  if (/load|read|parse/i.test(name)) return `Loads or parses input required by this module.`;
  if (/test/i.test(name)) return `Verifies the expected behavior of the related application component.`;
  return `Implements the ${name} operation for this module.`;
}
function nodeForFunction(file, f) { return { id:`function:${file.path}:${f.name}`, type:'function', name:f.name, filePath:file.path, lineRange:[f.startLine, f.endLine], summary:fnSummary(f.name,file), tags:['function','application','workflow'], complexity:complexity((f.endLine||f.startLine)-(f.startLine||0)+1) }; }
function nodeForClass(file, c) { return { id:`class:${file.path}:${c.name}`, type:'class', name:c.name, filePath:file.path, lineRange:[c.startLine,c.endLine], summary:`Represents the ${c.name} abstraction used by this module.`, tags:['class','application','service'], complexity:complexity((c.endLine||c.startLine)-(c.startLine||0)+1, (c.methods||[]).length) }; }
function edge(source,target,type,weight) { return {source,target,type,direction:'forward',weight}; }

for (const batch of batches) {
  const input = { projectRoot: root, batchFiles: batch.files, batchImportData: batch.batchImportData };
  const inputPath = path.join(ua, 'tmp', `ua-file-analyzer-input-${batch.batchIndex}.json`);
  const resultPath = path.join(ua, 'tmp', `ua-file-extract-results-${batch.batchIndex}.json`);
  fs.writeFileSync(inputPath, JSON.stringify(input));
  execFileSync('node', [extractor, inputPath, resultPath], {stdio:'inherit'});
  if (!fs.existsSync(resultPath) || fs.statSync(resultPath).size === 0) throw new Error(`Missing extraction output for ${batch.batchIndex}`);
  const extracted = JSON.parse(fs.readFileSync(resultPath, 'utf8'));
  if (!extracted.scriptCompleted) throw new Error(`Extractor did not complete batch ${batch.batchIndex}`);
  const results = new Map(extracted.results.map((r) => [r.path, r]));
  const nodes = [], edges = [];
  for (const file of batch.files) {
    const result = results.get(file.path) || {totalLines:file.sizeLines,nonEmptyLines:file.sizeLines,functions:[],classes:[],exports:[],metrics:{}};
    const fileId = idFor(file);
    nodes.push({id:fileId,type:typeFor(file),name:path.basename(file.path),filePath:file.path,summary:fileSummary(file,result),tags:baseTags(file,result),complexity:complexity(result.nonEmptyLines ?? file.sizeLines, (result.functions||[]).length+(result.classes||[]).length)});
    if (file.fileCategory === 'code' || file.fileCategory === 'script' || file.fileCategory === 'markup') {
      const exported = new Set((result.exports||[]).map((x)=>x.name));
      for (const f of result.functions||[]) if (exported.has(f.name) || (f.endLine-f.startLine+1)>=10) {
        const n=nodeForFunction(file,f); nodes.push(n); edges.push(edge(fileId,n.id,'contains',1)); if(exported.has(f.name)) edges.push(edge(fileId,n.id,'exports',.8));
      }
      for (const c of result.classes||[]) if (exported.has(c.name) || (c.methods||[]).length>=2 || (c.endLine-c.startLine+1)>=20) {
        const n=nodeForClass(file,c); nodes.push(n); edges.push(edge(fileId,n.id,'contains',1)); if(exported.has(c.name)) edges.push(edge(fileId,n.id,'exports',.8));
      }
      for (const target of batch.batchImportData[file.path] || []) edges.push(edge(fileId,`file:${target}`,'imports',.7));
    }
  }
  const fileNodes = new Set(nodes.map(n=>n.id));
  const parts = Math.ceil(Math.max(nodes.length/60, edges.length/120, 1));
  const sorted = [...batch.files].sort((a,b)=>a.path.localeCompare(b.path));
  const groupSize = Math.ceil(sorted.length/parts);
  for(let i=0;i<parts;i++) {
    const paths = new Set(sorted.slice(i*groupSize,(i+1)*groupSize).map(f=>f.path));
    const partNodes = nodes.filter(n=>paths.has(n.filePath));
    const partIDs = new Set(partNodes.map(n=>n.id));
    const partEdges = edges.filter(e=>partIDs.has(e.source));
    const name = parts===1 ? `batch-${batch.batchIndex}.json` : `batch-${batch.batchIndex}-part-${i+1}.json`;
    fs.writeFileSync(path.join(ua,'intermediate',name), JSON.stringify({nodes:partNodes,edges:partEdges},null,2)+'\n');
  }
}
