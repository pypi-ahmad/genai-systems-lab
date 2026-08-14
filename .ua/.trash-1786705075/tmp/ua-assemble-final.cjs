#!/usr/bin/env node
const fs = require('fs');

const [assembledPath, scanPath, layersPath, tourPath, commitHash] = process.argv.slice(2);
const assembled = JSON.parse(fs.readFileSync(assembledPath, 'utf8'));
const scan = JSON.parse(fs.readFileSync(scanPath, 'utf8'));
const layersRaw = JSON.parse(fs.readFileSync(layersPath, 'utf8'));
const tourRaw = JSON.parse(fs.readFileSync(tourPath, 'utf8'));
const layers = Array.isArray(layersRaw) ? layersRaw : layersRaw.layers || [];
const tour = Array.isArray(tourRaw) ? tourRaw : tourRaw.steps || [];

const graph = {
  version: '1.0.0',
  project: {
    name: scan.name,
    languages: scan.languages,
    frameworks: scan.frameworks,
    description: scan.description,
    analyzedAt: new Date().toISOString(),
    gitCommitHash: commitHash,
  },
  nodes: assembled.nodes,
  edges: assembled.edges,
  layers,
  tour: tour.sort((a, b) => a.order - b.order),
};

fs.writeFileSync(assembledPath, JSON.stringify(graph, null, 2) + '\n');
