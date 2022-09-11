#include "loggingStruct.h"
#include "constants.h"

#ifndef _SQL_HELPERS_
#define _SQL_HELPERS_

// SQL query construction constants 
#define CREATE_TABLE_STR "CREATE TABLE IF NOT EXISTS "
#define OPEN_BRACE " ("
#define CLOSE_BRACE_SEMI ");"
#define CLOSE_BRACE ")"
#define INSERT_STR "INSERT INTO "
#define VALUES_STR " VALUES"
#define COMMA ","
#define SPACE " "
#define SINGLE_QUOTE "'"
#define QUESTION "?"
// constants for buffering data
// number of seconds to buffer
#define NUM_BUF_S 20
#define NUM_MS_IN_S 1000
#define SQL_TEXT_FIELD_LEN 64

void sql_bind_int(sqlite3_stmt *stmt, int index, const char* dtype, const void* value);
void sql_bind_int64(sqlite3_stmt *stmt, int index, const void* value);
void sql_bind_double(sqlite3_stmt *stmt, int index,  const char* dtype, const void* value);
void sql_bind_text(sqlite3_stmt *stmt, int index, const void* value, int numBytes, void(*destructor)(void*));
void sql_bind_blob(sqlite3_stmt *stmt, int index, const void* value, int numBytes, void(*destructor)(void*));
void sql_prepare(sqlite3 *db, const char *zSql, int nByte, sqlite3_stmt **ppStmt, const char **pzTail);
void sql_step(sqlite3_stmt *stmt);
void sql_finalize(sqlite3_stmt *stmt);

void openDatabase(sqlite3 **db, char *startName, int db_index, char* newNameLocation);
void createTables(sqlite3 *db, SQLTable* databaseArr);

#endif
