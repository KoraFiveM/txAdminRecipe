#!/usr/bin/env python3
"""Check referenced public GitHub repos and refs, without cloning them."""
from pathlib import Path
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import yaml

root=Path(__file__).resolve().parents[1]
recipe=yaml.safe_load((root/'recipe.yaml').read_text(encoding='utf-8'))
repos={}
for task in recipe['tasks']:
    if task.get('action')!='download_github': continue
    parts=urllib.parse.urlparse(task['src']).path.strip('/').split('/')
    if len(parts)!=2: continue
    repos.setdefault((parts[0],parts[1]),set()).add(task.get('ref') or 'HEAD')

token=os.getenv('GITHUB_TOKEN','')
headers={'Accept':'application/vnd.github+json','User-Agent':'Kora-recipe-resource-check','X-GitHub-Api-Version':'2022-11-28'}
if token: headers['Authorization']='Bearer '+token
errors=[]
for (owner,repo),refs in sorted(repos.items()):
    for ref in sorted(refs):
        url=f'https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/commits/{urllib.parse.quote(ref,safe="")}'
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=15) as response:
                data=json.load(response)
                if not data.get('sha'): raise ValueError('Missing commit SHA')
            print(f'OK   {owner}/{repo}@{ref}')
        except urllib.error.HTTPError as e:
            message={404:'not found, private, or branch missing',403:'forbidden or API rate limit',401:'bad credentials'}.get(e.code,f'HTTP {e.code}')
            errors.append(f'{owner}/{repo}@{ref}: {message}')
            print('FAIL',errors[-1])
        except (urllib.error.URLError,TimeoutError,ValueError) as e:
            errors.append(f'{owner}/{repo}@{ref}: {e}')
            print('FAIL',errors[-1])
if errors:
    print(f'\nFAILED: {len(errors)} of {sum(map(len,repos.values()))} resource refs unavailable.')
    sys.exit(1)
print(f'PASS: {len(repos)} repositories and all referenced branches reachable')
