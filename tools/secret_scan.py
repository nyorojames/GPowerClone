import os, re, subprocess

secret_patterns = [
    re.compile(r'(?i)api[_-]?key\s*[:=]\s*["\'][a-zA-Z0-9_\-]{16,}["\']'),
    re.compile(r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}'),
    re.compile(r'-----BEGIN (?:RSA|OPENSSH|DSA|EC|PGP)?\s*PRIVATE KEY-----'),
]

tree_hits = []
for root, dirs, files in os.walk('.'):
    if any(x in root for x in ['.git', '.venv', 'ClassTranscript']):
        continue
    for f in files:
        if f.endswith(('.py', '.md', '.json', '.txt', '.ps1', '.bat', '.cmd', '.csv')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
                for pat in secret_patterns:
                    if pat.search(content):
                        tree_hits.append((p, pat.pattern))

print(f"Working tree secrets: {len(tree_hits)}")
for p, pat in tree_hits:
    print(f"  {p}: {pat}")

# Git log diff check
p = subprocess.run(['git', 'log', '-p', '--all'], capture_output=True, text=True, errors='ignore')
history_hits = []
for pat in secret_patterns:
    if pat.search(p.stdout):
        history_hits.append(pat.pattern)
print(f"Git history secrets: {len(history_hits)}")
