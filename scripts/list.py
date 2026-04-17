#!/usr/bin/env python3
"""Render the library catalog with install status — /library list."""
import yaml
import os

LIBRARY_YAML = os.path.expanduser('~/.claude/skills/library/library.yaml')

with open(LIBRARY_YAML) as f:
    d = yaml.safe_load(f)

def check_install(name, kind):
    """Return install status by checking default + global dirs."""
    dirs = d['default_dirs'][kind]
    # dirs is a list of {default: ..., global: ...}
    default_dir = os.path.expanduser(dirs[0]['default'])
    global_dir = os.path.expanduser(dirs[1]['global'])

    # For skills + agents, entry dir is <dir>/<name>/
    # For prompts, it's <dir>/<name>.md
    if kind == 'prompts':
        if os.path.isfile(os.path.join(default_dir, f'{name}.md')):
            return 'installed (default)'
        if os.path.isfile(os.path.join(global_dir, f'{name}.md')):
            return 'installed (global)'
    else:
        if os.path.isdir(os.path.join(default_dir, name)):
            return 'installed (default)'
        if os.path.isdir(os.path.join(global_dir, name)):
            return 'installed (global)'
        # Agents — check for single-file form at global
        if kind == 'agents' and os.path.isfile(os.path.join(global_dir, f'{name}.md')):
            return 'installed (global)'
    return 'not installed'


def render_section(title, entries, kind):
    print(f'\n## {title}\n')
    if not entries:
        print(f'No {kind} in catalog.')
        return 0, 0
    print(f'| Name | Description | Status |')
    print(f'|------|-------------|--------|')
    installed = 0
    for e in entries:
        status = check_install(e['name'], kind)
        if status.startswith('installed'):
            installed += 1
        # Truncate description for table readability
        desc = (e.get('description', '') or '').replace('\n', ' ').strip()
        if len(desc) > 80:
            desc = desc[:77] + '...'
        print(f"| {e['name']} | {desc} | {status} |")
    return len(entries), installed


print('# Library Catalog\n')
print(f"Source of truth: {LIBRARY_YAML}")

total, total_installed = 0, 0
for title, key, kind in [
    ('Skills', 'skills', 'skills'),
    ('Agents', 'agents', 'agents'),
    ('Prompts', 'prompts', 'prompts'),
]:
    count, installed = render_section(title, d['library'].get(key, []), kind)
    total += count
    total_installed += installed

print(f'\n---\n')
print(f'**Summary:** {total} total entries, {total_installed} installed locally, {total - total_installed} not installed')
