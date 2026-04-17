#!/usr/bin/env python3
"""FLINT wiki-gap finder — /library audit (deterministic parts only).

Handles:
  - Finding C: orphan catalog entries (source path missing on disk)
  - Finding D: low-score / never-evaled skills (from eval.last_score field)

Findings A (manual workflows) and B (external services) are topic-reading
tasks — handled by an Explore subagent in the calling code.
"""
import yaml
import os
import sys
import json

LIBRARY_YAML = os.path.expanduser('~/.claude/skills/library/library.yaml')


def main():
    with open(LIBRARY_YAML) as f:
        cat = yaml.safe_load(f)

    orphans = []
    improvement_candidates = []

    for kind_key, kind_label in [('skills', 'skill'), ('agents', 'agent'), ('prompts', 'prompt')]:
        for e in cat['library'].get(kind_key, []):
            # Finding C — orphan check
            source = e.get('source', '')
            if source.startswith('~') or source.startswith('/') or (len(source) > 1 and source[1] == ':'):
                abs_path = os.path.expanduser(source)
                if not os.path.isfile(abs_path):
                    orphans.append({
                        'type': kind_label,
                        'name': e['name'],
                        'source': source,
                        'issue': 'source file not found on disk',
                        'proposed_fix': 'remove entry or correct the source path',
                    })

            # Finding D — low-score or never-evaled
            ev = e.get('eval', {}) or {}
            last_score = ev.get('last_score')
            criteria_count = ev.get('criteria_count')

            if last_score is None:
                improvement_candidates.append({
                    'type': kind_label,
                    'name': e['name'],
                    'reason': 'never evaled (eval.last_score is null)',
                    'current_score': None,
                    'priority': 'medium',
                })
            else:
                # Parse "N/M" format or numeric
                if isinstance(last_score, str) and '/' in last_score:
                    parts = last_score.split('/')
                    try:
                        passed, total = int(parts[0]), int(parts[1])
                        ratio = passed / total if total > 0 else 0
                    except (ValueError, ZeroDivisionError):
                        ratio = 0
                elif isinstance(last_score, (int, float)) and criteria_count:
                    ratio = last_score / criteria_count if criteria_count > 0 else 0
                else:
                    ratio = 1  # Unknown format; skip

                if ratio < 0.9:
                    improvement_candidates.append({
                        'type': kind_label,
                        'name': e['name'],
                        'reason': f'eval score below 90% ({last_score})',
                        'current_score': str(last_score),
                        'priority': 'high' if ratio < 0.75 else 'medium',
                    })

    result = {
        'orphans': orphans,
        'improvement_candidates': improvement_candidates,
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    main()
