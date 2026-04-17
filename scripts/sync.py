#!/usr/bin/env python3
"""Sync all installed items from their sources — /library sync."""
import yaml
import os
import shutil
import subprocess
import tempfile
import re
import sys

LIBRARY_YAML = os.path.expanduser('~/.claude/skills/library/library.yaml')
LIBRARY_DIR = os.path.expanduser('~/.claude/skills/library')


def git_pull_library():
    """Step 1 — pull latest catalog."""
    print("Step 1 — git pull on library repo...")
    result = subprocess.run(
        ['git', '-C', LIBRARY_DIR, 'pull'],
        capture_output=True, text=True,
    )
    print(f"  {result.stdout.strip() or result.stderr.strip()}")
    print()


def load_catalog():
    with open(LIBRARY_YAML) as f:
        return yaml.safe_load(f)


def is_installed(entry, kind, default_dirs):
    """Step 3 — check if entry is installed (default or global)."""
    dirs = default_dirs[kind]
    default = os.path.expanduser(dirs[0]['default'])
    global_ = os.path.expanduser(dirs[1]['global'])
    name = entry['name']
    if kind == 'prompts':
        if os.path.isfile(os.path.join(default, f'{name}.md')):
            return ('default', os.path.join(default, f'{name}.md'))
        if os.path.isfile(os.path.join(global_, f'{name}.md')):
            return ('global', os.path.join(global_, f'{name}.md'))
    else:
        if os.path.isdir(os.path.join(default, name)):
            return ('default', os.path.join(default, name))
        if os.path.isdir(os.path.join(global_, name)):
            return ('global', os.path.join(global_, name))
        if kind == 'agents' and os.path.isfile(os.path.join(global_, f'{name}.md')):
            return ('global', os.path.join(global_, f'{name}.md'))
    return (None, None)


def refresh_from_source(entry, kind, target_path):
    """Step 4 — re-pull from source into target."""
    source = entry['source']
    name = entry['name']

    # Local path handling
    if source.startswith('~') or source.startswith('/') or (len(source) > 1 and source[1] == ':'):
        abs_source = os.path.expanduser(source)

        # For skills: source points to SKILL.md; copy the parent dir
        # For agents: source points to the .md file; copy just the file
        # For prompts: same as agents
        if kind == 'skills':
            src_dir = os.path.dirname(abs_source)
            # If source == target (self-reference), nothing to do
            if os.path.abspath(src_dir) == os.path.abspath(target_path):
                return 'up-to-date (in-place source)'
            shutil.rmtree(target_path, ignore_errors=True)
            shutil.copytree(src_dir, target_path)
            return 'refreshed from local source'
        else:
            # Single file (agent or prompt)
            if os.path.abspath(abs_source) == os.path.abspath(target_path):
                return 'up-to-date (in-place source)'
            shutil.copy2(abs_source, target_path)
            return 'refreshed from local source'

    # GitHub URL handling
    gh_pattern = re.compile(
        r'^https://(?:github\.com|raw\.githubusercontent\.com)/([^/]+)/([^/]+)/(?:blob/)?([^/]+)/(.+)$'
    )
    m = gh_pattern.match(source)
    if not m:
        return f'failed: unrecognized source format: {source}'

    org, repo, branch, file_path = m.groups()
    clone_url = f'https://github.com/{org}/{repo}.git'

    with tempfile.TemporaryDirectory() as tmp_dir:
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', '--branch', branch, clone_url, tmp_dir],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            # Try SSH fallback
            ssh_url = f'git@github.com:{org}/{repo}.git'
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', '--branch', branch, ssh_url, tmp_dir],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                return f'failed: clone failed ({result.stderr.strip()})'

        src_abs = os.path.join(tmp_dir, file_path)
        if kind == 'skills':
            src_dir = os.path.dirname(src_abs)
            shutil.rmtree(target_path, ignore_errors=True)
            shutil.copytree(src_dir, target_path)
        else:
            shutil.copy2(src_abs, target_path)
        return 'refreshed from GitHub'


def main():
    git_pull_library()
    cat = load_catalog()
    default_dirs = cat['default_dirs']

    sections = [
        ('skills', cat['library']['skills']),
        ('agents', cat['library']['agents']),
        ('prompts', cat['library']['prompts']),
    ]

    print("Step 2 — catalog loaded:")
    for kind, entries in sections:
        print(f"  {kind}: {len(entries)} entries")
    print()

    print("Step 3-4 — checking install status and refreshing...")
    synced = 0
    failed = 0
    skipped = 0
    rows = []
    for kind, entries in sections:
        for entry in entries:
            scope, target = is_installed(entry, kind, default_dirs)
            if scope is None:
                rows.append((kind, entry['name'], 'not installed (skipped)'))
                skipped += 1
                continue
            try:
                status = refresh_from_source(entry, kind, target)
                rows.append((kind, entry['name'], status))
                if status.startswith('failed'):
                    failed += 1
                else:
                    synced += 1
            except Exception as e:
                rows.append((kind, entry['name'], f'failed: {e}'))
                failed += 1

    print()
    print("## Sync Complete\n")
    print("| Type | Name | Status |")
    print("|------|------|--------|")
    for kind, name, status in rows:
        print(f"| {kind} | {name} | {status} |")
    print()
    print(f"Synced: {synced}, Failed: {failed}, Skipped: {skipped}")
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
