#ifndef _LOGGING_STRUCT_
#define _LOGGING_STRUCT_

typedef struct {
    char *colName; // max 32
    char *type; // max 16
    short number;
    char *unit; // max 16
    void *data;
    char *SQLtype; // max 32
} SQLTableElement;

typedef struct {
  char *tableName; // max 32
  short numCol;
  SQLTableElement *columns;
} SQLTable;

#endif