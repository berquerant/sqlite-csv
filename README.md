# sqlite-csv

```
❯ ./sqlite-csv.sh
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
```
