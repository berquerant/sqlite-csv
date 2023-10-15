#!/bin/bash

usage() {
    cat - <<EOS
NAME
  sqlite-csv.sh - sql csv pipeline

SYNOPSIS
  sqlite-csv.sh QUERY [FILE]...

  QUERY
    query to be executed

  FILE
    csv file:
    import data to sqlite, the table name is the file name without the extension.
    if - is specified, csv will also be read from standard input, even if other files are specified

ENVIRONMENT VARIABLES

  SQLITE_CSV_CMD
    sqlite executable, default is sqlite3
EOS
}

SQLITE="${SQLITE_CSV_CMD:-sqlite3}"

sqlite_csv() {
    "${SQLITE}" -csv "$@"
}

import_stdin() {
    database_file="$1"
    sqlite_csv "${database_file}" ".import '|cat -' stdin"
}

import_file() {
    database_file="$1"
    filepath="$2"
    filename="$(basename -- "$filepath")"
    tablename="${filename%.*}"
    sqlite_csv "${database_file}" ".import ${filepath} ${tablename}"
}

import() {
    database_file="$1"
    target="$2"
    if [ "${target}" = "-" ] ; then
        import_stdin "${database_file}"
    else
        import_file "${database_file}" "${target}"
    fi
}

run_query() {
    database_file="$1"
    shift
    "${SQLITE}" -csv -header "${database_file}" "$@"
}

main() {
    if [ $# -lt 2 ] ; then
        usage
        exit 1
    fi

    database_file="$(mktemp)"
    query="$1"
    shift

    for arg in "$@" ; do
        import "${database_file}" "${arg}"
    done

    run_query "${database_file}" "${query}"
}

set -e

main "$@"
