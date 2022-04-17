#!/usr/bin/env python3
import argparse
from dateutil import parser
from jinja2 import Environment, FileSystemLoader
import os
from pathlib import Path
import re
import subprocess

argparser = argparse.ArgumentParser()
argparser.add_argument("date")
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

date = parser.parse(args.date)
data = {
  "month": str(date.month),
  "months": [str(month) for month in list(range(1,date.month+1))],
  "year": str(date.year),
  "years": [str(year) for year in list(range(2020,date.year+1))]
}
regex = re.compile("month|year")
 
jinja2 = Environment(loader=FileSystemLoader("tpl"))

# Create directory structure (if needed)
dirpath = Path(f"{date.year}/{date.month}")
if not dirpath.exists():
  print(f"Directory {str(dirpath)} does not exist, creating...")
  Path(dirpath,Path(f"expense_reports")).mkdir(parents=True)

for tpl_path in list(Path("tpl").glob('**/*.j2')):
  relative_path = tpl_path.relative_to("tpl")
  template = jinja2.get_template(str(relative_path))
  basedir = regex.sub(lambda m: data[re.escape(m.group(0))], str(relative_path.parent))
  file_path = Path(f"{basedir}/{relative_path.stem}")
  write_mode = "x" if relative_path.stem != "books.beancount" else "w"
  try:
    with file_path.open(mode=write_mode) as file:
      file.write(template.render(data))
    file.close()
  except FileExistsError:
    print(f"File {file_path} exists, skipping...")
  print(f"Wrote {file_path}")
