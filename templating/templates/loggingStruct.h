typedef struct {
    char colName[32];
    char type[16];
    short number;
    char unit[16];
    void *data;
    char SQLtype[32];
} SQLTableElement;

typedef struct {
  char tableName[32];
  short numCol;
  SQLTableElement *columns;
} SQLTable;