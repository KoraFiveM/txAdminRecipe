#!/usr/bin/env python3
"""Generate recipe.yaml from the Kora docs catalog (catalog/resources.json).

Usage: generate_recipe.py CATALOG_JSON [--check]
  --check  exit 1 if recipe.yaml differs from what would be generated.

Static tasks live in recipe/base.yaml. Resource downloads come from the
catalog: kind kora/dependency (plus compat-type extras such as ox_lib),
skipping internal and retired entries, sorted by `order`.
Never edit the download section of recipe.yaml by hand.
"""
from pathlib import Path
import json, sys, yaml

ROOT = Path(__file__).resolve().parents[1]
PAUSE_EVERY, PAUSE_SECONDS = 3, 5

def included(r):
    if r.get('retired') or r.get('kind') == 'internal':
        return False
    return r.get('kind') in ('kora', 'dependency') or r.get('type') == 'compat'

def build(catalog):
    base = yaml.safe_load((ROOT / 'recipe' / 'base.yaml').read_text(encoding='utf-8'))
    res = sorted((r for r in catalog['resources'] if included(r)), key=lambda r: r['order'])
    tasks = list(base['before_resources'])
    for i, r in enumerate(res, 1):
        tasks.append({'action': 'download_github',
                      'src': r['repository'].removesuffix('.git'),
                      'ref': r['branch'],
                      'dest': './resources/' + r['path']})
        if i % PAUSE_EVERY == 0 and i != len(res):
            tasks.append({'action': 'waste_time', 'seconds': PAUSE_SECONDS})
    tasks += base['after_resources']
    return yaml.safe_dump({**base['meta'], 'tasks': tasks}, sort_keys=False, width=1000)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 1:
        sys.exit(__doc__)
    out = build(json.loads(Path(args[0]).read_text(encoding='utf-8')))
    target = ROOT / 'recipe.yaml'
    if '--check' in sys.argv:
        if target.read_text(encoding='utf-8') != out:
            sys.exit('recipe.yaml is out of date with the catalog; run generate_recipe.py')
        print('recipe.yaml is up to date')
        return
    target.write_text(out, encoding='utf-8')
    print('wrote recipe.yaml')

main()
