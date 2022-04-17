#!/usr/bin/env python3
import argparse
import collections
import os
from pathlib import Path, PurePath
import subprocess
import sys

from beancount.parser import parser as beancount_parser
from beancount.parser.printer import print_error
from beancount.ops import validation
from beancount import loader as beancount_loader
from beancount.core.data import Open, Close

argparser = argparse.ArgumentParser()
argparser.add_argument("filename")
args = argparser.parse_args()

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

retval=0

file = Path(args.filename).read_text()
parsed_file = beancount_parser.parse_string(file)

# Check for accounts defined in files other than definitions.beancount
if not args.filename.endswith("definitions.beancount"):
  accounts = [ definition for definition in beancount_parser.parse_file(args.filename)[0] if isinstance(definition, Open) or isinstance(definition, Close)]
  if len(accounts) > 0:
    for account in accounts:
      print_error(validation.ValidationError(
        account.meta,
        "File contains account definition.  Define accounts in definitions.beancount",
        account))
  retval+=len(accounts)

if "definitions.beancount" not in parsed_file[2]['include'] and not args.filename.endswith("definitions.beancount"):
  files = [(Path('definitions.beancount').resolve().as_posix(), True),(Path(args.filename).resolve().as_posix(), True)]
else:
  files = [(Path(args.filename).resolve().as_posix(), True)]

entries, errors, _ = beancount_loader._load(files, None, validation.HARDCORE_VALIDATIONS, None)
for error in errors:
  error.source['filename'] = error.source['filename'].replace(str(Path.cwd())+'/', '')
  print_error(error, sys.stdout)
retval+=len(errors)

# Validate that books.beancount files have no transactions
if args.filename.endswith("books.beancount"):
  for entry in entries:
    if entry.meta['filename'].endswith("books.beancount"):
      entry.meta['filename'] = entry.meta['filename'].replace(str(Path.cwd())+'/', '')
      print_error(validation.ValidationError(
        entry.meta,
        "Transaction found in books.beancount file - this will be overwritten",
        entry), sys.stdout)
      retval+=1

sys.exit(retval)

