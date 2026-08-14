const fs = require("fs");

const uaDir = process.argv[2];
const scan = JSON.parse(fs.readFileSync(`${uaDir}/tmp/ua-scan-files.json`, "utf8"));
const imports = JSON.parse(fs.readFileSync(`${uaDir}/tmp/ua-import-map-output.json`, "utf8"));
const languages = Object.keys(scan.stats.byLanguage).sort((a, b) => a.localeCompare(b));
const paths = new Set(scan.files.map((file) => file.path));
const frameworks = ["FastAPI", "Pydantic", "Pytest", "SQLAlchemy", "Starlette"];

if ([...paths].some((path) => /^Dockerfile(?:\.|$)/.test(path))) frameworks.push("Docker");
if ([...paths].some((path) => /^\.github\/workflows\/.+\.ya?ml$/.test(path))) {
  frameworks.push("GitHub Actions");
}

const output = {
  name: "genai-systems-lab",
  description:
    "A shared execution platform for 20 AI systems, combining generative AI pipelines, LangGraph state machines, and CrewAI teams behind a common API, frontend, and runtime. Note: this project has over 100 source files; consider scoping analysis to a subdirectory for faster results.",
  languages,
  frameworks,
  files: scan.files,
  totalFiles: scan.totalFiles,
  filteredByIgnore: scan.filteredByIgnore,
  estimatedComplexity: scan.estimatedComplexity,
  importMap: imports.importMap,
};

if (output.totalFiles !== output.files.length) throw new Error("totalFiles mismatch");
fs.writeFileSync(`${uaDir}/intermediate/scan-result.json`, `${JSON.stringify(output, null, 2)}\n`);
console.log(JSON.stringify({
  totalFiles: output.totalFiles,
  byCategory: scan.stats.byCategory,
  languages: output.languages,
  frameworks: output.frameworks,
  complexity: output.estimatedComplexity,
  importEntries: Object.keys(output.importMap).length,
}));
