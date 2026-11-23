#!/usr/bin/env python3
"""Generate recipe.yaml from the Kora docs catalog (catalog/resources.json).

Usage: generate_recipe.py CATALOG_JSON [--check]
  --check  exit 1 if recipe.yaml differs from what would be generated.

Static tasks live in recipe/base.yaml. Resource downloads come from the
catalog: kind kora/dependency (plus compat-type extras such as ox_lib),
skipping internal and retired entries. Published runtime ZIPs take precedence
over branch downloads, in the installer's catalog order.
Never edit the download section of recipe.yaml by hand.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath
import json
import os
import re
import sys
from urllib.error import URLError
from urllib.parse import quote, unquote
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]
PAUSE_EVERY, PAUSE_SECONDS = 3, 5

def included(r):
    if r.get('retired') or r.get('kind') == 'internal':
        return False
    return r.get('kind') in ('kora', 'dependency') or r.get('type') == 'compat'

def release_zip(resource):
    repository = resource['repository'].removesuffix('.git')
    match = re.fullmatch(r'https://github\.com/([\w.-]+/[\w.-]+)', repository)
    if not match:
        return None
    slug = match[1]
    folder = PurePosixPath(resource['path']).name
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Kora-txAdmin-recipe'}
    if token := os.getenv('GITHUB_TOKEN'):
        headers['Authorization'] = f'Bearer {token}'
    request = Request(f'https://api.github.com/repos/{slug}/releases?per_page=20', headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            releases = json.load(response)
    except (URLError, TimeoutError) as exc:
        sys.exit(f'Could not check published releases for {slug}: {exc}')

    for release in sorted(releases, key=lambda entry: entry['published_at'] or '', reverse=True):
        if release['draft'] or not release['published_at']:
            continue
        tag = release['tag_name']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', tag):
            continue
        name = f'{folder}-{tag}.zip'
        # GitHub can normalize brackets in the two collection asset names.
        names = {name, name.replace('[', '.').replace(']', '.').lstrip('.')}
        for asset in release['assets']:
            asset_name = asset["name"]
            path = f"{repository}/releases/download/{tag}/"
            if (asset_name in names and asset["state"] == "uploaded"
                    and unquote(asset["browser_download_url"]) == path + asset_name):
                return tag, path + quote(asset_name)
    return None


def download_tasks(resource, asset):
    repository = resource['repository'].removesuffix('.git')
    dest = './resources/' + resource['path']
    if asset is None:
        return [{'action': 'download_github', 'src': repository,
                 'ref': resource['branch'], 'dest': dest}]

    tag, url = asset
    archive = f"./tmp/{resource['id']}.zip"
    parent = dest.rsplit('/', 1)[0]
    tasks = [
        {'action': 'download_file', 'url': url, 'path': archive},
        {'action': 'unzip', 'src': archive, 'dest': parent},
    ]
    # This already-published phone ZIP references stream assets it did not bundle.
    if resource['id'] == 'kora-phone' and tag == 'v0.1.1-dev.2':
        tasks.append({'action': 'download_github', 'src': repository,
                      'ref': tag, 'subpath': 'stream', 'dest': f'{dest}/stream'})
    return tasks


def build(catalog):
    base = yaml.safe_load((ROOT / 'recipe' / 'base.yaml').read_text(encoding='utf-8'))
    # Match the installer: missing order sorts last and ties retain catalog order.
    resources = sorted((r for r in catalog['resources'] if included(r)),
                       key=lambda r: r['order'] if r.get('order') is not None else 2**32 - 1)
    tasks = list(base['before_resources'])
    with ThreadPoolExecutor(max_workers=6) as pool:
        assets = list(pool.map(release_zip, resources))
    for i, (resource, asset) in enumerate(zip(resources, assets), 1):
        tasks.extend(download_tasks(resource, asset))
        if i % PAUSE_EVERY == 0 and i != len(resources):
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
