import { readdirSync, readFileSync, statSync } from 'node:fs';
import { resolve, relative } from 'node:path';
const root = process.cwd();
const ignored = new Set([
  'node_modules',
  '.git',
  'test-results',
  'playwright-report',
  '.venv',
  '.runtime',
  '__pycache__',
  '.pytest_cache',
  '.ruff_cache',
]);
const patterns = [
  /sk-(?:proj-)?[A-Za-z0-9_-]{24,}/,
  /gh[pousr]_[A-Za-z0-9]{30,}/,
  /github_pat_[A-Za-z0-9_]{40,}/,
  /\b(?:AKIA|ASIA)[A-Z0-9]{16}\b/,
  /-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----/,
];
const findings = [];
let scanned = 0;
function scan(dir) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    if (ignored.has(e.name) || e.isSymbolicLink()) continue;
    const p = resolve(dir, e.name);
    if (e.isDirectory()) {
      scan(p);
      continue;
    }
    if (e.name.startsWith('.env') && e.name !== '.env.example') continue;
    if (
      !/\.(ts|tsx|js|mjs|py|toml|json|md|yaml|yml|html|example|log|css|sh|txt|sql)$/.test(e.name) ||
      statSync(p).size > 2e6
    )
      continue;
    scanned++;
    const text = readFileSync(p, 'utf8');
    if (patterns.some((pattern) => pattern.test(text))) findings.push(relative(root, p));
  }
}
scan(root);
if (findings.length) {
  console.error('Potential credentials in:', findings.join(', '));
  process.exitCode = 1;
} else
  console.log(
    `No credential-shaped strings found in ${scanned} source/document files. Pattern scan only; excludes local environment/runtime files.`,
  );
