#!/usr/bin/env python3
"""Static checks for the Kora txAdmin recipe. Requires PyYAML."""
from pathlib import Path
from collections import Counter
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
errors = []
def check(condition, message):
    if not condition: errors.append(message)

for name in ('recipe.yaml', 'server.cfg', 'permissions.cfg', 'kora.sql', 'README.md'):
    check((ROOT / name).is_file(), f'Missing {name}')
if errors:
    print('\n'.join('ERROR: '+x for x in errors)); sys.exit(1)

try:
    recipe = yaml.safe_load((ROOT/'recipe.yaml').read_text(encoding='utf-8'))
except yaml.YAMLError as exc:
    sys.exit(f'Invalid recipe YAML: {exc}')
check(isinstance(recipe, dict), 'Recipe must be a mapping')
recipe = recipe if isinstance(recipe, dict) else {}
tasks = recipe.get('tasks', [])
check(isinstance(tasks, list) and len(tasks)>0, 'Recipe tasks must be a nonempty list')
tasks = tasks if isinstance(tasks, list) else []
check(recipe.get('$engine') == 3, 'Expected txAdmin recipe engine 3')
check(str(recipe.get('$onesync')) == 'on', 'Expected OneSync on')
check(any(isinstance(t,dict) and t.get('action')=='connect_database' for t in tasks), 'Missing connect_database')
check(any(isinstance(t,dict) and t.get('action')=='query_database' and t.get('file')=='./kora.sql' for t in tasks), 'Missing database creation task')
check(any(isinstance(t,dict) and t.get('action')=='replace_string' and t.get('file')=='./kora.sql' and t.get('search')=='KORA_DATABASE_NAME' and t.get('replace')=='{{dbName}}' for t in tasks), 'Missing SQL database placeholder replacement')
check(any(isinstance(t,dict) and t.get('action')=='replace_string' and t.get('mode')=='all_vars' and './server.cfg' in (t.get('file') if isinstance(t.get('file'),list) else [t.get('file')]) for t in tasks), 'Missing server.cfg variable substitution')

downloads = [t for t in tasks if isinstance(t,dict) and t.get('action')=='download_github']
for field in ('src','dest'):
    check(all(isinstance(t.get(field),str) and t[field].strip() for t in downloads), f'All GitHub downloads must define {field}')
for field in ('src','dest'):
    dup = [x for x,n in Counter(t.get(field) for t in downloads).items() if n>1]
    check(not dup, f'Duplicate download {field}: {dup}')
for t in downloads:
    check(bool(re.fullmatch(r'https://github\.com/[^/\s]+/[^/\s]+/?',t.get('src',''))), f'Invalid GitHub repository URL: {t.get("src")}')

cfg=(ROOT/'server.cfg').read_text(encoding='utf-8')
sql=(ROOT/'kora.sql').read_text(encoding='utf-8')
for var in ('{{serverEndpoints}}','{{maxClients}}','{{svLicense}}','{{dbConnectionString}}'):
    check(var in cfg, f'Missing txAdmin server.cfg placeholder: {var}')
check('exec permissions.cfg' in cfg, 'server.cfg must load permissions.cfg')
check('https://docs.koraframe.work/' in cfg, 'Missing official Kora docs URL')
check('kora_fivemanage_token' in cfg, 'Missing optional FiveManage token example')
check('KORA_DATABASE_NAME' in sql, 'Missing database name marker in SQL')
check('CREATE DATABASE IF NOT EXISTS' in sql.upper(), 'SQL must create the database')
check(not re.search(r'\b(?:CREATE\s+TABLE|DROP\s+|TRUNCATE\s+|DELETE\s+FROM)\b',sql,re.I), 'SQL must not create tables or run destructive statements')
for key in ('sv_projectName','sv_projectDesc','sv_hostname','locale','tags','banner_connecting','banner_detail','load_server_icon'):
    check(not any(re.match(r'^\s*(?:sets?\s+)?'+re.escape(key)+r'\b',line) for line in cfg.splitlines() if not line.lstrip().startswith('#')), f'Portal-managed listing setting still active: {key}')

# Ensure required pre-resources are downloaded to their expected locations.
for resource in ('kora_lib','kora_sql','kora_inventory','kora_core'):
    check(any(t.get('dest')==f'./resources/[pre]/{resource}' for t in downloads), f'Missing pre-resource download: {resource}')
    check(re.search(r'^\s*ensure\s+'+resource+r'\s*$',cfg,re.M) is not None, f'Missing ensure: {resource}')

if errors:
    for error in errors: print('ERROR:',error)
    sys.exit(1)
print(f'PASS: recipe syntax, {len(tasks)} tasks, {len(downloads)} downloads, SQL and config checks')
