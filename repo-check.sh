#!/bin/bash
retval=0

current_year=$(date +%Y)
current_month=$(date +%m)

BASE_DIR=$(git rev-parse --show-superproject-working-tree || pwd)
FAIL="[$(tput setab 1; tput bold)FAIL$(tput sgr0)]"
OK="[$(tput setab 2; tput bold)OK$(tput sgr0)]"

log_result () {
  printf "%-70s%4s\n" "${1}:" "$2"
}

check_beancount () {
  local errcount=0
  [[ -n $1 ]] && local dir=$1 || local dir=${BASE_DIR}
  beancount_files="$(ls -1 ${dir}/*.beancount 2>/dev/null) "
  [[ -d ${dir}/expense_reports ]] && beancount_files+="$(ls -1 ${dir}/expense_reports/*.beancount 2>/dev/null) "

  for beancount_file in $beancount_files; do
    local fileerr=0
    local_file=${beancount_file#$BASE_DIR/}
    OUTPUT=$(python check_file.py ${local_file}) || { fileerr=1; errcount=$(($errcount+1)); }
    [[ $fileerr -eq 0 ]] && log_result "${local_file}" "$OK" || { log_result "${local_file}" "$FAIL"; 
      echo -e "${OUTPUT}" | sed 's/^/  /'; }
  done
  retval=$(($retval+$errcount))
}

check_month () {
  local year=$1
  local month=$2
  local month_pretty=$(date -d ${year}-${month}-01 +%B)
  local dir=${BASE_DIR}/${year}/${month}
  local pretty_dir=${year}/${month}
  local errcount=0

  log_name="${month_pretty} ${year}"
  output=""
  [[ -d ${dir} ]] || { log_result "${log_name}" "$FAIL"; echo -e "  Directory ${year}/${month} doesn't exist"; return 1; }

  [[ -f ${dir}/books.beancount ]] || { output+="  ${month_pretty}/books.beancount doesn't exist\n"; errcount=$((errcount+1)); }
  grep -q "include \"${month}/books.beancount\"" ${BASE_DIR}/${year}/books.beancount 2>/dev/null || { output+="  ${month_pretty} not imported in ${year}/books.beancount\n"; errcount=$((errcount+1)); }
  [[ -d ${dir}/expense_reports ]] ||  { output+="  Directory ${pretty_dir}/expense_reports doesn't exist\n"; errcount=$((errcount+1)); }
  for file in $(ls -1 ${dir}/*.beancount 2>/dev/null | grep -v "books.beancount" | sed "s%${dir}/%%g"); do
    grep -q "include \"${file}\"" ${dir}/books.beancount 2>/dev/null || { output+="  ${pretty_dir}/${file} not imported in ${pretty_dir}/books.beancount\n"; errcount=$((errcount+1)); }
  done
  for report in $(ls -1 ${dir}/expense_reports/*.beancount 2>/dev/null | sed "s%${dir}/expense_reports/%%g"); do
    grep -q "include \"expense_reports/${report}\"" ${dir}/expenses.beancount 2>/dev/null || { output+="  ${pretty_dir}/expense_reports/${report} not imported in ${pretty_dir}/expenses.beancount\n"; errcount=$((errcount+1)); }
  done
  [[ ${errcount} -eq 0 ]] && log_result "${log_name}" "$OK" || log_result "${log_name}" "$FAIL"; [[ -n "$output" ]] && echo -n -e "$output"
  check_beancount ${dir}
}

check_year () {
  local year=$1
  [[ ${year} == "2020" ]] && local start_month=12 || local start_month=1 # Books start December 2020
  local dir=${BASE_DIR}/${year}
  local errcount=0

  [[ -d ${BASE_DIR}/${year} ]] || { log_result "${year}" "${FAIL}"; echo -e "  Directory ${year} doesn't exist"; return 1; }

  output=""
  [[ -f ${dir}/books.beancount ]] || { output+="  ${year}/books.beancount doesn't exist\n"; errcount=$((errcount+1)); }
  grep -q "include \"${year}/books.beancount\"" ${BASE_DIR}/books.beancount 2>/dev/null || { output+="  ${year} not imported in books.beancount\n"; errcount=$((errcount+1)); }
  for file in $(ls -1 ${dir}/*.beancount 2>/dev/null | grep -v "books.beancount" | sed "s%${dir}/%%g"); do
    grep -q "include \"${file}\"" ${dir}/books.beancount 2>/dev/null || { output+="  ${year}/${file} not imported in ${year}/books.beancount\n"; errcount=$((errcount+1)); }
  done
  [[ ${errcount} -eq 0 ]] && log_result "${year}" "$OK" || log_result "${year}" "$FAIL"; [[ -n "$output" ]] && echo -n -e "$output"

  for month in $(seq ${start_month} ${current_month}); do
    check_month ${year} ${month}
  done
  check_beancount ${dir}
}

for year in $(seq 2020 ${current_year}); do
  check_year ${year}
done

check_beancount
exit $retval
