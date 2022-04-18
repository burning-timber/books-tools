#!/usr/bin/env python3
import json
import os
import subprocess
from sys import stderr

from beancount.core.data import Open, Close
from beancount.parser import parser as beancount
from beancount.parser.printer import print_error

git_working_tree = subprocess.run(
    ['git', 'rev-parse', '--show-superproject-working-tree'],
    stdout=subprocess.PIPE,
    universal_newlines=True)

git_toplevel = subprocess.run(
    ['git', 'rev-parse', '--show-toplevel'],
    stdout=subprocess.PIPE,
    universal_newlines=True)

if os.path.exists(git_working_tree.stdout.strip()):
  os.chdir(git_working_tree.stdout.strip())
elif os.path.exists(git_toplevel.stdout.strip()):
  os.chdir(git_toplevel.stdout.strip())

definitions, errors, _ = beancount.parse_file('definitions.beancount')
for error in errors:
  print_error(error, stderr)

accounts = {}

def account2dict(account_parts, metadata, account_dict, depth=0):
  if depth == len(account_parts) - 1:
    account_dict[account_parts[-1]] = { "account": metadata }
  else:
    account_dict[account_parts[depth]] = {}
    account_dict[account_parts[depth]]['children'] = {}
    account2dict(account_parts, metadata, account_dict[account_parts[depth]]['children'], depth+1)

def merge(a, b, path=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            else:
                if str(key) == "status":
                    a[key] = b[key] # Let the most recent status through
                elif str(key) == "name":
                    pass # Leave original name value
                else:
                    raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a

for account in [ definition for definition in definitions if isinstance(definition, Open) or isinstance(definition, Close)]:
  metadata = {}
  account_parts = account.account.split(":")
  if isinstance(account, Close):
    metadata['status'] = "closed"
    metadata['closed_date'] = account.date.strftime("%Y-%m-%d")
  else:
    metadata['status'] = "open"
    metadata['opened_date'] = account.date.strftime("%Y-%m-%d")
  metadata['account_id'] = account.account

  if account.meta.get('pretty-name'):
    metadata['name'] = account.meta['pretty-name']
  else:
    metadata['name'] = account_parts[-1].capitalize()

  if account.meta.get('description'):
    metadata['description'] = account.meta['description']

  account_dict = {}
  account2dict(account_parts, metadata, account_dict) 
  
  merge(accounts, account_dict)

rules = ""
rule_file = open("rules.json", "r")
rule_line = rule_file.readline()
while rule_line:
  if not rule_line.startswith("#"):
    rules += rule_line
  rule_line = rule_file.readline()

merge(accounts, json.loads(rules)['accounts'])
print(json.dumps(accounts))
