const fs = require('fs');

try {
  const [inputPath, outputPath] = process.argv.slice(2);
  if (!inputPath || !outputPath) throw new Error('Usage: node ua-arch-analyze.js <input> <output>');
  const input = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  const nodes = input.fileNodes;
  const ids = new Set(nodes.map(n => n.id));
  const pathOf = new Map(nodes.map(n => [n.id, (n.filePath || n.name || '').replace(/\\/g, '/')]));
  const typeOf = new Map(nodes.map(n => [n.id, n.type]));
  const parts = nodes.map(n => pathOf.get(n.id).split('/').filter(Boolean));
  let common = parts[0] || [];
  for (const p of parts.slice(1)) { let i = 0; while (i < common.length && i < p.length && common[i] === p[i]) i++; common = common.slice(0, i); }
  const groupOf = new Map();
  for (const n of nodes) {
    const p = pathOf.get(n.id).split('/').filter(Boolean);
    const rest = p.slice(common.length);
    groupOf.set(n.id, rest.length > 1 ? rest[0] : 'root');
  }
  const directoryGroups = {};
  for (const n of nodes) (directoryGroups[groupOf.get(n.id)] ??= []).push(n.id);
  const nodeTypeGroups = {};
  for (const n of nodes) (nodeTypeGroups[n.type] ??= []).push(n.id);
  const imports = input.importEdges.filter(e => ids.has(e.source) && ids.has(e.target));
  const allEdges = input.allEdges.filter(e => ids.has(e.source) && ids.has(e.target));
  const fanIn = Object.fromEntries(nodes.map(n => [n.id, 0]));
  const fanOut = Object.fromEntries(nodes.map(n => [n.id, 0]));
  const inter = new Map(); const groupTotals = {}; const groupInternal = {};
  for (const e of imports) {
    fanOut[e.source]++; fanIn[e.target]++;
    const from = groupOf.get(e.source), to = groupOf.get(e.target), key = `${from}\u0000${to}`;
    inter.set(key, (inter.get(key) || 0) + 1);
    groupTotals[from] = (groupTotals[from] || 0) + 1;
    groupTotals[to] = (groupTotals[to] || 0) + 1;
    if (from === to) groupInternal[from] = (groupInternal[from] || 0) + 1;
  }
  const interGroupImports = [...inter].map(([key, count]) => { const [from, to] = key.split('\u0000'); return {from, to, count}; });
  const intraGroupDensity = Object.fromEntries(Object.keys(directoryGroups).map(g => [g, {internalEdges: groupInternal[g] || 0, totalEdges: groupTotals[g] || 0, density: groupTotals[g] ? (groupInternal[g] || 0) / groupTotals[g] : 0}]));
  const patterns = {api:['routes','api','controllers','endpoints','handlers','routers','blueprints','serializers'],service:['services','core','lib','domain','logic','signals','composables','mailers','jobs','channels','internal'],data:['models','db','data','persistence','repository','entities','migrations','sql','database','schema','entity'],ui:['components','views','pages','ui','layouts','screens'],middleware:['middleware','plugins','interceptors','guards'],utility:['utils','helpers','common','shared','tools','templatetags','pkg'],config:['config','constants','env','settings','management','commands'],test:['__tests__','test','tests','spec','specs'],types:['types','interfaces','schemas','contracts','dtos','dto','request','response'],state:['store','state','reducers','actions','slices'],assets:['assets','static','public'],entry:['cmd','bin'],documentation:['docs','documentation','wiki'],infrastructure:['deploy','deployment','infra','infrastructure','k8s','kubernetes','helm','charts','terraform','tf','docker'],'ci-cd':['.github','.gitlab','.circleci']};
  const patternMatches = {};
  for (const g of Object.keys(directoryGroups)) patternMatches[g] = Object.entries(patterns).find(([, values]) => values.includes(g))?.[0] || null;
  const cross = new Map();
  for (const e of allEdges) { const key = `${typeOf.get(e.source)}\u0000${typeOf.get(e.target)}\u0000${e.type}`; cross.set(key, (cross.get(key) || 0) + 1); }
  const crossCategoryEdges = [...cross].map(([key, count]) => { const [fromType, toType, edgeType] = key.split('\u0000'); return {fromType, toType, edgeType, count}; });
  const pathList = nodes.map(n => pathOf.get(n.id));
  const matches = re => nodes.filter(n => re.test(pathOf.get(n.id))).map(n => pathOf.get(n.id));
  const deploymentTopology = {hasDockerfile:pathList.some(p => /(^|\/)Dockerfile/i.test(p)),hasCompose:pathList.some(p => /docker-compose\.(ya?ml)$/i.test(p)),hasK8s:pathList.some(p => /(^|\/)(k8s|kubernetes)\//i.test(p)),hasTerraform:pathList.some(p => /\.(tf|tfvars)$/i.test(p)),hasCI:pathList.some(p => /(^|\/)(\.github\/workflows|\.gitlab-ci|Jenkinsfile)/i.test(p)),infraFiles:nodes.filter(n => /Dockerfile|docker-compose|(^|\/)(\.github\/workflows|k8s|kubernetes|terraform|infra|docker)\//i.test(pathOf.get(n.id))).map(n => pathOf.get(n.id))};
  const dataPipeline = {schemaFiles:nodes.filter(n => n.type === 'schema' || /\.(sql|graphql|gql|proto|prisma)$/i.test(pathOf.get(n.id))).map(n => pathOf.get(n.id)),migrationFiles:matches(/(^|\/)migrations?\//i),dataModelFiles:nodes.filter(n => /(^|\/)(models?|database|db|repository|crud)\b/i.test(pathOf.get(n.id))).map(n => pathOf.get(n.id)),apiHandlerFiles:nodes.filter(n => /(^|\/)(api|routers?|routes?|endpoints?)\b/i.test(pathOf.get(n.id))).map(n => pathOf.get(n.id))};
  const docGroups = new Set(nodes.filter(n => n.type === 'document' || /(^|\/)README\.md$/i.test(pathOf.get(n.id))).map(n => groupOf.get(n.id)));
  const docCoverage = {groupsWithDocs:docGroups.size,totalGroups:Object.keys(directoryGroups).length,coverageRatio:Object.keys(directoryGroups).length ? docGroups.size / Object.keys(directoryGroups).length : 0,undocumentedGroups:Object.keys(directoryGroups).filter(g => !docGroups.has(g))};
  const dependencyDirection = [];
  for (let i=0;i<interGroupImports.length;i++) { const a=interGroupImports[i]; if (a.from===a.to) continue; const opposite=inter.get(`${a.to}\u0000${a.from}`)||0; if (a.count>opposite) dependencyDirection.push({dependent:a.from,dependsOn:a.to}); }
  const result = {scriptCompleted:true,directoryGroups,nodeTypeGroups,crossCategoryEdges,interGroupImports,intraGroupDensity,patternMatches,deploymentTopology,dataPipeline,docCoverage,dependencyDirection,fileStats:{totalFileNodes:nodes.length,filesPerGroup:Object.fromEntries(Object.entries(directoryGroups).map(([g, v])=>[g,v.length])),nodeTypeCounts:Object.fromEntries(Object.entries(nodeTypeGroups).map(([t,v])=>[t,v.length]))},fileFanIn:fanIn,fileFanOut:fanOut};
  fs.writeFileSync(outputPath, JSON.stringify(result, null, 2));
} catch (error) { console.error(error.stack || error.message); process.exit(1); }
