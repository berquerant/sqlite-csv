#!/bin/bash

usage() {
    cat - <<EOS
NAME
  sqlite-csv.sh - sql csv pipeline

SYNOPSIS
  sqlite-csv.sh [-h] [-c] [-f] [-i] QUERY [FILE]...

  QUERY
    query to be executed

  FILE
    csv file:
    import data to sqlite, the table name is the file name without the extension.
    if - is specified, csv will also be read from standard input, even if other files are specified

OPTIONS

  -c
    rename column names to index (from 0)

  -f
    rename table names to index (from 0)

  -h
    show this help

  -i
    -c and -f

ENVIRONMENT VARIABLES

  SQLITE_CSV_CMD
    sqlite executable, default is sqlite3

  SQLITE_CSV_KEEP_DB
    if not empty, do not delete sqlite database file
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
    sqlite_csv "${database_file}" "PRAGMA table_info(\"${tablename}\");" |\
        awk -F"," -v table="${tablename}" '{printf("ALTER TABLE \"%s\" RENAME COLUMN \"%s\" to \"%s\"\n", table, $2, $1)}' |\
        while read line ; do "${SQLITE}" "${database_file}" "${line}" ; done
}

rename_tablenames_to_index() {
    database_file="$1"
    sqlite_csv "${database_file}" "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%'" |\
        awk '{printf("ALTER TABLE \"%s\" RENAME TO \"%s\"\n", $1, NR-1)}' |\
        while read line ; do "${SQLITE}" "${database_file}" "${line}" ; done
}

remove_database_file() {
    database_file="$1"
    if [ -n "${SQLITE_CSV_KEEP_DB}" ] ; then
        echo "DB=${database_file}" >&2
        return
    fi
    rm -f "${database_file}"
}

main() {
    if [ $# -lt 2 ] ; then
        usage
        exit 1
    fi

    # parse options
    index_headers=0
    index_filenames=0
    indexes=0

    while getopts "hcfi" OPT ; do
        case "$OPT" in
            c) index_headers=1 ;;
            f) index_filenames=1 ;;
            i) indexes=1 ;;
            h) usage
               exit
               ;;
        esac
    done
    if [ "${indexes}" = "1" ] ; then
        index_headers=1
        index_filenames=1
    fi
    shift $(($OPTIND - 1))

    database_file="$(mktemp)"
    trap "remove_database_file ${database_file}" EXIT
    query="$1"
    shift

    for arg in "$@" ; do
        import "${database_file}" "${arg}"
        if [ "${index_headers}" = "1" ] ; then
            rename_columns_to_index "${database_file}" "$(get_tablename $arg)"
        fi
    done
    if [ "${index_filenames}" = "1" ] ; then
        rename_tablenames_to_index "${database_file}"
    fi

    run_query "${database_file}" "${query}"
}

set -e

main "$@"
