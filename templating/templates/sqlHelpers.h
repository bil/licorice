void sql_bind_int(sqlite3_stmt *stmt, int index, int value);

void sql_bind_double(sqlite3_stmt *stmt, int index, double value);

void sql_bind_blob(sqlite3_stmt *stmt, int index, const void* value, int numBytes, void(*destructor)(void*));

void sql_prepare(sqlite3 *db, const char *zSql, int nByte, sqlite3_stmt **ppStmt, const char **pzTail);

void sql_step(sqlite3_stmt *stmt);

void sql_finalize(sqlite3_stmt *stmt);