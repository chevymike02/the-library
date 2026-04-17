#!/usr/bin/env python3
"""Validate library.yaml parses and every source file exists."""
import yaml
import os
import sys

LIBRARY_YAML = os.path.expanduser('~/.claude/skills/library/library.yaml')

with open(LIBRARY_YAML) as f:
    d = yaml.safe_load(f)

print('library.yaml parsed cleanly')
print(f'  skills:  {len(d["library"]["skills"])}')
print(f'  agents:  {len(d["library"]["agents"])}')
print(f'  prompts: {len(d["library"]["prompts"])}')
print()

missing = 0
for item in d['library']['skills'] + d['library']['agents']:
    src = os.path.expanduser(item['source'])
    ok = os.path.isfile(src)
    if not ok:
        missing += 1
    marker = 'OK  ' if ok else 'MISS'
    print(f'  {marker}  {item["name"]:<28}  {item["source"]}')

total = len(d['library']['skills']) + len(d['library']['agents'])
print()
print(f'Total: {total}, Missing: {missing}')
sys.exit(0 if missing == 0 else 1)
