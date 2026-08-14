const fs = require('fs');

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) throw new Error('Usage: node ua-arch-analyze.js <graph.json> <results.json>');
const graph = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const fileTypes = new Set(['file', 'config', 'document', 'service', 'pipeline', 'table', 'schema', 'resource', 'endpoint']);
const files = graph.nodes.filter(n => fileTypes.has(n.type));
const byId = new Map(files.map(n => [n.id, n]));
const paths = files.map(n => (n.filePath || n.name || 'root').replace(/\\/g, '/').split('/'));
const prefix = paths.reduce((acc, parts) => acc.filter((p, i) => parts[i] === p), paths[0] || []);
function group(n) {
  const parts = (n.filePath || n.name || 'root').replace(/\\/g, '/').split('/');
  return parts[prefix.length] || (parts.length > 1 ? parts[0] : 'root');
}
const directoryGroups = {}, nodeTypeGroups = {};
for (const n of files) {
  (directoryGroups[group(n)] ||= []).push(n.id);
  (nodeTypeGroups[n.type] ||= []).push(n.id);
}
const allEdges = graph.edges.filter(e => byId.has(e.source) && byId.has(e.target));
const importEdges = allEdges.filter(e => /import|depend/i.test(e.type));
const fanIn = Object.fromEntries(files.map(n => [n.id, 0]));
const fanOut = Object.fromEntries(files.map(n => [n.id, 0]));
const inter = new Map(), intra = Object.fromEntries(Object.keys(directoryGroups).map(k => [k, { internalEdges: 0, totalEdges: 0 }]));
for (const e of importEdges) {
  fanOut[e.source]++; fanIn[e.target]++;
  const a = group(byId.get(e.source)), b = group(byId.get(e.target));
  intra[a].totalEdges++; intra[b].totalEdges++;
  if (a === b) intra[a].internalEdges++; else inter.set(`${a}\u0000${b}`, (inter.get(`${a}\u0000${b}`) || 0) + 1);
}
const interGroupImports = [...inter].map(([key, count]) => { const [from, to] = key.split('\u0000'); return { from, to, count }; });
const intraGroupDensity = Object.fromEntries(Object.entries(intra).map(([k, v]) => [k, { ...v, density: v.totalEdges ? v.internalEdges / v.totalEdges : 0 }]));
const labels = { routes:'api', api:'api', controllers:'api', endpoints:'api', handlers:'api', services:'service', core:'service', lib:'service', domain:'service', logic:'service', models:'data', db:'data', data:'data', persistence:'data', repository:'data', entities:'data', middleware:'middleware', plugins:'middleware', interceptors:'middleware', guards:'middleware', utils:'utility', helpers:'utility', common:'utility', shared:'utility', tools:'utility', config:'config', constants:'config', env:'config', settings:'config', tests:'test', test:'test', types:'types', schemas:'types', contracts:'types', docs:'documentation', documentation:'documentation', infra:'infrastructure', infrastructure:'infrastructure', docker:'infrastructure', '.github':'ci-cd', 'graphify-out':'generated-artifacts' };
const patternMatches = Object.fromEntries(Object.keys(directoryGroups).map(k => [k, labels[k.toLowerCase()] || 'unclassified']));
const typeOf = id => byId.get(id).type;
const cross = new Map();
for (const e of allEdges) { const k = `${typeOf(e.source)}\u0000${typeOf(e.target)}\u0000${e.type}`; cross.set(k, (cross.get(k)||0)+1); }
const crossCategoryEdges = [...cross].map(([k,count]) => { const [fromType,toType,edgeType] = k.split('\u0000'); return {fromType,toType,edgeType,count}; });
const pathOf = n => n.filePath || n.name || n.id;
const infraFiles = files.filter(n => /docker|compose|\.github\/workflows|\.gitlab-ci|jenkins|makefile/i.test(pathOf(n))).map(pathOf);
const dataPipeline = { schemaFiles: files.filter(n => /\.(sql|graphql|gql|proto|prisma)$/i.test(pathOf(n))).map(pathOf), migrationFiles: files.filter(n => /migration/i.test(pathOf(n))).map(pathOf), dataModelFiles: files.filter(n => /(models?|database|repository|crud)\.(py|ts|js)$/i.test(pathOf(n))).map(pathOf), apiHandlerFiles: files.filter(n => /(routers?|routes?|api|endpoints?|controllers?)\//i.test(pathOf(n))).map(pathOf) };
const docGroups = new Set(files.filter(n => n.type === 'document').map(group));
const docCoverage = { groupsWithDocs: docGroups.size, totalGroups: Object.keys(directoryGroups).length, coverageRatio: Object.keys(directoryGroups).length ? docGroups.size / Object.keys(directoryGroups).length : 0, undocumentedGroups: Object.keys(directoryGroups).filter(k => !docGroups.has(k)) };
const dependencyDirection = interGroupImports.map(({from,to}) => ({dependent:from,dependsOn:to}));
const result = { scriptCompleted:true, directoryGroups, nodeTypeGroups, crossCategoryEdges, interGroupImports, intraGroupDensity, patternMatches, deploymentTopology:{hasDockerfile:files.some(n => /dockerfile/i.test(pathOf(n))),hasCompose:files.some(n => /compose\.(yml|yaml)$/i.test(pathOf(n))),hasK8s:files.some(n => /(^|\/)(k8s|kubernetes|helm)\//i.test(pathOf(n))),hasTerraform:files.some(n => /\.tf(vars)?$/i.test(pathOf(n))),hasCI:files.some(n => /\.github\/workflows|\.gitlab-ci|jenkins/i.test(pathOf(n))),infraFiles}, dataPipeline, docCoverage, dependencyDirection, fileStats:{totalFileNodes:files.length,filesPerGroup:Object.fromEntries(Object.entries(directoryGroups).map(([k,v])=>[k,v.length])),nodeTypeCounts:Object.fromEntries(Object.entries(nodeTypeGroups).map(([k,v])=>[k,v.length]))},fileFanIn:fanIn,fileFanOut:fanOut};
fs.writeFileSync(outputPath, JSON.stringify(result, null, 2));
