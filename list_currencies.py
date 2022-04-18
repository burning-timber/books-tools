import json
import os
import subprocess
from sys import stderr

from beancount.core.data import Commodity
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

currencies = {}

for moccodity in [ definition for definition in definitions if isinstance(definition, Commodity)]:
  # Here comes the duty
  metadata = {key.replace("-", "_"): value for key, value in moccodity.meta.items() if key not in ['filename', 'lineno']}
  metadata['creation_date'] = moccodity.date.strftime("%Y-%m-%d")
  currencies[moccodity.currency] = metadata

print(json.dumps(currencies))
