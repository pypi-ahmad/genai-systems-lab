const fs = require('fs');

try {
  const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  if (!Array.isArray(input.layers)) {
    const layerPath = require('path').join(require('path').dirname(process.argv[2]), 'layers.json');
    input.layers = JSON.parse(fs.readFileSync(layerPath, 'utf8'));
  }
  const nodes = (input.nodes || []).filter(n => new Set(['file', 'config', 'document', 'service', 'pipeline', 'table', 'schema', 'resource', 'endpoint']).has(n.type));
  const nodeById = new Map(nodes.map(n => [n.id, n]));
  const edges = (input.edges || []).filter(e => nodeById.has(e.source) && nodeById.has(e.target));
  const inDegree = new Map(nodes.map(n => [n.id, 0]));
  const outDegree = new Map(nodes.map(n => [n.id, 0]));
  for (const e of edges) { inDegree.set(e.target, inDegree.get(e.target) + 1); outDegree.set(e.source, outDegree.get(e.source) + 1); }
  const ranked = (degree, key) => [...nodes].sort((a,b) => degree.get(b.id) - degree.get(a.id) || a.id.localeCompare(b.id)).slice(0,20).map(n => ({id:n.id, [key]:degree.get(n.id), name:n.name}));
  const maxOut = Math.max(0, ...outDegree.values());
  const lowInCutoff = [...inDegree.values()].sort((a,b)=>a-b)[Math.floor(nodes.length * .25)] ?? 0;
  const nameMatches = /^(index\.(ts|js)|main\.(ts|js|py|rs|go)|app\.(ts|js|py)|server\.(ts|js)|mod\.rs|manage\.py|wsgi\.py|asgi\.py|run\.py|__main__\.py|Application\.java|Main\.java|Program\.cs|config\.ru|index\.php|App\.swift|Application\.kt|main\.(cpp|c))$/;
  const candidates = nodes.map(n => { const p=n.filePath||''; let score=0; if(n.type==='document' && p==='README.md') score+=5; else if(n.type==='document' && !p.includes('/')) score+=2; if(n.type==='file' && nameMatches.test(n.name||'')) score+=3; if(n.type==='file' && p.split('/').length<=2) score++; if(outDegree.get(n.id)>=maxOut*.9 && maxOut>0) score++; if(inDegree.get(n.id)<=lowInCutoff) score++; return {id:n.id,score,name:n.name,summary:n.summary}; }).filter(x=>x.score>0).sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id)).slice(0,5);
  const start = candidates.find(c => nodeById.get(c.id).type==='file')?.id || null;
  const adjacency = new Map(nodes.map(n=>[n.id,[]]));
  for(const e of edges) if(e.type==='imports'||e.type==='calls') adjacency.get(e.source).push(e.target);
  const order=[], depthMap={}, byDepth={};
  if(start){ const q=[start]; depthMap[start]=0; while(q.length){const id=q.shift();order.push(id);const d=depthMap[id];(byDepth[d]??=[]).push(id);for(const next of adjacency.get(id)){if(depthMap[next]===undefined){depthMap[next]=d+1;q.push(next);}}} }
  const categories={documentation:[],infrastructure:[],data:[],config:[]};
  for(const n of nodes){const x={id:n.id,name:n.name,type:n.type,summary:n.summary};if(n.type==='document')categories.documentation.push(x);else if(['service','pipeline','resource'].includes(n.type))categories.infrastructure.push(x);else if(['table','schema','endpoint'].includes(n.type))categories.data.push(x);else if(n.type==='config')categories.config.push(x);}
  const pairCounts=new Map(); for(const e of edges){const k=[e.source,e.target].sort().join('\u0000');pairCounts.set(k,(pairCounts.get(k)||0)+1);} const clusters=[...pairCounts].filter(([,c])=>c>=2).sort((a,b)=>b[1]-a[1]).slice(0,10).map(([k,edgeCount])=>({nodes:k.split('\u0000'),edgeCount}));
  const index=Object.fromEntries(nodes.map(n=>[n.id,{name:n.name,type:n.type,summary:n.summary}]));
  const result={scriptCompleted:true,entryPointCandidates:candidates,fanInRanking:ranked(inDegree,'fanIn'),fanOutRanking:ranked(outDegree,'fanOut'),bfsTraversal:{startNode:start,order,depthMap,byDepth},nonCodeFiles:categories,clusters,layers:{count:(input.layers||[]).length,list:input.layers||[]},nodeSummaryIndex:index,totalNodes:nodes.length,totalEdges:edges.length};
  fs.writeFileSync(process.argv[3], JSON.stringify(result,null,2));
} catch(err) { console.error(err.stack || err.message); process.exit(1); }
