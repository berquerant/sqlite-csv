# sqlite-csv

```
❯ ./sqlite-csv.sh
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
```
