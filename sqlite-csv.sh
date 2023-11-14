#!/bin/bash

usage() {
    cat - <<EOS
NAME
  sqlite-csv.sh - sql csv pipeline

SYNOPSIS
  sqlite-csv.sh [--index-headers] QUERY [FILE]...

  QUERY
    query to be executed

  FILE
    csv file:
    import data to sqlite, the table name is the file name without the extension.
    if - is specified, csv will also be read from standard input, even if other files are specified

OPTIONS

  --index-headers
    rename column names to index (from 0)

ENVIRONMENT VARIABLES

  SQLITE_CSV_CMD
    sqlite executable, default is sqlite3
EOS
}

SQLITE="${SQLITE_CSV_CMD:-sqlite3}"

sqlite_csv() {
    "${SQLITE}" -csv "$@"
}

get_tablename() {
    target="$1"
    if [ "${target}" = "-" ] ; then
        echo "stdin"
    else
        filename="$(basename -- "$target")"
        echo "${filename%.*}"
    fi
}

import_stdin() {
    database_file="$1"
    tablename="$2"
    sqlite_csv "${database_file}" ".import '|cat -' ${tablename}"
}

import_file() {
    database_file="$1"
    tablename="$2"
    filepath="$3"
    sqlite_csv "${database_file}" ".import ${filepath} ${tablename}"
}

import() {
    database_file="$1"
    target="$2"
    tablename="$(get_tablename $2)"
    if [ "${target}" = "-" ] ; then
        import_stdin "${database_file}" "${tablename}"
    else
        import_file "${database_file}" "${tablename}" "${target}"
    fi
}

run_query() {
    database_file="$1"
    shift
    "${SQLITE}" -csv -header "${database_file}" "$@"
}

rename_columns_to_index() {
    database_file="$1"
    tablename="$2"
    sqlite_csv "${database_file}" "PRAGMA table_info(${tablename});" |\
        awk -F"," -v table="${tablename}" '{printf("ALTER TABLE \"%s\" RENAME COLUMN \"%s\" to \"%s\"\n", table, $2, $1)}' |\
        while read line ; do "${SQLITE}" "${database_file}" "${line}" ; done
}

main() {
    if [ $# -lt 2 ] ; then
        usage
        exit 1
    fi

    index_headers=0
    if [ "$1" = "--index-headers" ] ; then
        shift
        index_headers=1
    fi

    database_file="$(mktemp)"
    query="$1"
    shift

    for arg in "$@" ; do
        import "${database_file}" "${arg}"
        if [ "${index_headers}" = "1" ] ; then
            rename_columns_to_index "${database_file}" "$(get_tablename $arg)"
        fi
    done

    run_query "${database_file}" "${query}"
}

set -e

main "$@"
