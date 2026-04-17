#!/usr/bin/env python3
"""Keyword search across the catalog — /library search <keyword>."""
import yaml
import os
import sys
import subprocess

LIBRARY_YAML = os.path.expanduser('~/.claude/skills/library/library.yaml')
LIBRARY_DIR = os.path.expanduser('~/.claude/skills/library')


def main():
    if len(sys.argv) < 2:
        print("usage: search.py <keyword>", file=sys.stderr)
        sys.exit(2)
    keyword = ' '.join(sys.argv[1:]).lower()

    # Step 1 — sync library repo
    subprocess.run(['git', '-C', LIBRARY_DIR, 'pull'], capture_output=True, text=True)

    # Step 2 — read catalog
    with open(LIBRARY_YAML) as f:
        cat = yaml.safe_load(f)

    # Step 3 — search (case-insensitive substring match on name + description)
    rows = []
    for kind_key, kind_label in [('skills', 'skill'), ('agents', 'agent'), ('prompts', 'prompt')]:
        for e in cat['library'].get(kind_key, []):
            name = e.get('name', '')
            desc = (e.get('description', '') or '').replace('\n', ' ').strip()
            src = e.get('source', '')
            if keyword in name.lower() or keyword in desc.lower():
                # Truncate desc for display
                d = desc if len(desc) <= 90 else desc[:87] + '...'
                rows.append((kind_label, name, d, src))

    # Step 4 — display
    if not rows:
        print(f'No results found for "{keyword}".')
        print()
        print('Tip: Try broader keywords or run `/library list` to see the full catalog.')
        return

    print(f'## Search Results for "{keyword}"\n')
    print('| Type | Name | Description | Source |')
    print('|------|------|-------------|--------|')
    for kind, name, desc, src in rows:
        print(f'| {kind} | {name} | {desc} | `{src}` |')
    print()
    print(f'**{len(rows)} match(es).**')
    # Step 5
    print()
    print('Run `/library use <name>` to install one of these.')


if __name__ == '__main__':
    main()
