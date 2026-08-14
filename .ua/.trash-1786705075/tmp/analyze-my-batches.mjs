import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const root = process.cwd();
const ua = path.join(root, '.ua');
const indices = new Set([2,12,16,18,24,29,31,32,33,42,43,45,47,52,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,92,93]);
const batchData = JSON.parse(fs.readFileSync(path.join(ua, 'intermediate', 'batches.json'), 'utf8'));
const batches = batchData.batches.filter(b => indices.has(b.batchIndex));
const extractor = 'C:/Users/ahmad/.understand-anything/repo/understand-anything-plugin/skills/understand/extract-structure.mjs';
const isCode = f => f.fileCategory === 'code' || f.fileCategory === 'script' || f.fileCategory === 'markup';
const fileType = f => {
  if (f.fileCategory === 'config') return 'config';
  if (f.fileCategory === 'docs') return 'document';
  if (f.fileCategory === 'infra') return /(?:workflow|gitlab-ci|jenkins|circleci)/i.test(f.path) ? 'pipeline' : /\.(?:tf|tfvars)$/i.test(f.path) ? 'resource' : 'service';
  if (f.fileCategory === 'data') return /(?:graphql|proto|prisma)/i.test(f.path) ? 'schema' : /(?:openapi|swagger)/i.test(f.path) ? 'endpoint' : 'file';
  return 'file';
};
const idFor = (f, type=fileType(f)) => `${type}:${f.path}`;
const complexity = r => r.nonEmptyLines > 200 ? 'complex' : r.nonEmptyLines >= 50 ? 'moderate' : 'simple';
const baseTags = f => {
  const p=f.path.toLowerCase();
  if (f.fileCategory==='docs') return ['documentation','project-guide','reference'];
  if (f.fileCategory==='config') return ['configuration',f.language==='json'?'json':'project-settings','build-system'];
  if (f.fileCategory==='infra') return ['infrastructure','deployment','automation'];
  if (f.fileCategory==='data') return ['data','dataset','project-resource'];
  if (p.includes('test')) return ['test','verification','project-module'];
  if (p.endsWith('__init__.py')) return ['python-package','entry-point','module-boundary'];
  if (p.includes('main.') || p.includes('app.')) return ['application','entry-point','project-module'];
  if (p.endsWith('.css') || p.endsWith('.html')) return ['frontend','styling','presentation'];
  return ['project-module', f.language || 'source', 'implementation'];
};
const summary = (f,r) => {
  const name=path.basename(f.path), p=f.path.toLowerCase();
  if (f.fileCategory==='docs') return `Documents ${name}'s project-facing guidance and reference material.`;
  if (f.fileCategory==='config') return `Defines ${name} configuration used by this project.`;
  if (f.fileCategory==='infra') return `Defines infrastructure or automation settings in ${name}.`;
  if (f.fileCategory==='data') return `Provides project data stored in ${name}.`;
  if (p.endsWith('__init__.py')) return `Marks ${path.dirname(f.path)} as a Python package and establishes its package boundary.`;
  if (p.includes('test')) return `Contains automated checks for behavior associated with ${name.replace(/^test_/, '').replace(/\.[^.]+$/, '')}.`;
  const funcs=(r.functions||[]).map(x=>x.name).filter(Boolean);
  return funcs.length ? `Implements ${funcs.slice(0,3).join(', ')}${funcs.length>3?' and related helpers':''} for this project module.` : `Provides the ${name} source module for this project.`;
};
function node(id,type,name,filePath,sum,tags,comp,lineRange) {
  const n={id,type,name,filePath,summary:sum,tags,complexity:comp}; if(lineRange) n.lineRange=lineRange; return n;
}
function qualifiedFunctions(r) { return (r.functions||[]).filter(x => (x.endLine-x.startLine+1)>=10 || (r.exports||[]).some(e=>e.name===x.name)); }
function qualifiedClasses(r) { return (r.classes||[]).filter(x => (x.endLine-x.startLine+1)>=20 || (x.methods||[]).length>=2 || (r.exports||[]).some(e=>e.name===x.name)); }
function makeSubnodes(f,r) {
  const out=[]; const exported=new Set((r.exports||[]).map(e=>e.name));
  for(const x of qualifiedFunctions(r)) out.push(node(`function:${f.path}:${x.name}`,'function',x.name,f.path,`Implements the ${x.name} routine in ${path.basename(f.path)}.`,['function','implementation','project-logic'],complexity({nonEmptyLines:x.endLine-x.startLine+1}),[x.startLine,x.endLine]));
  for(const x of qualifiedClasses(r)) out.push(node(`class:${f.path}:${x.name}`,'class',x.name,f.path,`Defines the ${x.name} type and its project behavior.`,['class','data-model','project-logic'],complexity({nonEmptyLines:x.endLine-x.startLine+1}),[x.startLine,x.endLine]));
  for(const s of r.services||[]) if(s.name) out.push(node(`service:${f.path}:${s.name}`,'service',s.name,f.path,`Defines the ${s.name} service within ${path.basename(f.path)}.`,['infrastructure','service','deployment'],complexity(r)));
  for(const e of r.endpoints||[]) { const name=e.name||`${e.method||'endpoint'}-${e.path||''}`; out.push(node(`endpoint:${f.path}:${name}`,'endpoint',name,f.path,`Defines the ${name} API endpoint.`,['api-schema','endpoint','interface'],complexity(r))); }
  for(const s of r.steps||[]) if(s.name) out.push(node(`pipeline:${f.path}:${s.name}`,'pipeline',s.name,f.path,`Defines the ${s.name} automation step.`,['ci-cd','automation','pipeline'],complexity(r)));
  for(const d of r.definitions||[]) if(d.name && /(?:graphql|proto)/i.test(f.path)) out.push(node(`schema:${f.path}:${d.name}`,'schema',d.name,f.path,`Defines the ${d.name} schema declaration.`,['schema-definition','api-schema','data-contract'],complexity(r)));
  for(const x of r.resources||[]) if(x.name) out.push(node(`resource:${f.path}:${x.name}`,'resource',x.name,f.path,`Defines the ${x.name} infrastructure resource.`,['infrastructure','resource','deployment'],complexity(r)));
  return {nodes:out,exported};
}
for (const batch of batches) {
  const input={projectRoot:root,batchFiles:batch.files.map(({path,language,sizeLines,fileCategory})=>({path,language,sizeLines,fileCategory})),batchImportData:batch.batchImportData};
  const inputPath=path.join(ua,'tmp',`ua-file-analyzer-input-${batch.batchIndex}.json`);
  const extractPath=path.join(ua,'tmp',`ua-file-extract-results-${batch.batchIndex}.json`);
  fs.writeFileSync(inputPath,JSON.stringify(input,null,2));
  execFileSync('node',[extractor,inputPath,extractPath],{stdio:'inherit'});
  if(!fs.existsSync(extractPath)||fs.statSync(extractPath).size===0) throw new Error(`Missing extraction output for ${batch.batchIndex}`);
  const extract=JSON.parse(fs.readFileSync(extractPath,'utf8'));
  const results=new Map((extract.results||[]).map(r=>[r.path,r]));
  const nodes=[], edges=[];
  for(const f of batch.files) {
    const r=results.get(f.path)||{path:f.path,nonEmptyLines:f.sizeLines,functions:[],classes:[],exports:[]};
    const fid=idFor(f); nodes.push(node(fid,fileType(f),path.basename(f.path),f.path,summary(f,r),baseTags(f),complexity(r)));
    if(isCode(f)) for(const target of batch.batchImportData[f.path]||[]) edges.push({source:fid,target:`file:${target}`,type:'imports',direction:'forward',weight:0.7});
    const subs=makeSubnodes(f,r); nodes.push(...subs.nodes);
    for(const sn of subs.nodes) { edges.push({source:fid,target:sn.id,type:'contains',direction:'forward',weight:1.0}); if(subs.exported.has(sn.name)) edges.push({source:fid,target:sn.id,type:'exports',direction:'forward',weight:0.8}); }
  }
  const expected=batch.files.filter(isCode).reduce((n,f)=>n+(batch.batchImportData[f.path]||[]).length,0);
  if(edges.filter(e=>e.type==='imports').length!==expected) throw new Error(`Import count mismatch ${batch.batchIndex}`);
  const parts=Math.ceil(Math.max(nodes.length/60,edges.length/120,1));
  const sorted=[...batch.files].sort((a,b)=>a.path.localeCompare(b.path)); const per=Math.ceil(sorted.length/parts);
  for(let k=0;k<parts;k++) { const files=new Set(sorted.slice(k*per,(k+1)*per).map(f=>f.path)); const pn=nodes.filter(n=>files.has(n.filePath)); const ids=new Set(pn.map(n=>n.id)); const pe=edges.filter(e=>ids.has(e.source)); const out={nodes:pn,edges:pe}; const suffix=parts===1?`batch-${batch.batchIndex}.json`:`batch-${batch.batchIndex}-part-${k+1}.json`; fs.writeFileSync(path.join(ua,'intermediate',suffix),JSON.stringify(out,null,2)); }
  console.log(`batch ${batch.batchIndex}: ${nodes.length} nodes, ${edges.length} edges, ${parts} part(s), skipped ${(extract.filesSkipped||[]).length}`);
}
