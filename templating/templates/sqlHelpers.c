#include <sqlite3.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "utilityFunctions.h"
#include "sqlHelpers.h"

static int prc;

void sql_bind_int(sqlite3_stmt *stmt, int index, int value) { 
  prc = sqlite3_bind_int(stmt, index, value);
  if (prc != SQLITE_OK) {
    die("sqlite3_bind_int failed \n");
  }
}

void sql_bind_double(sqlite3_stmt *stmt, int index, double value) { 
  prc = sqlite3_bind_double(stmt, index, value);
  if (prc != SQLITE_OK) {
    die("sqlite3_bind_int failed \n");
  }
}

void sql_bind_blob(sqlite3_stmt *stmt, int index, const void* value, int numBytes, void(*destructor)(void*)) {
  prc = sqlite3_bind_blob(stmt, index, value, numBytes, destructor);
  if (prc != SQLITE_OK) {
    die("sqlite3_bind_blob failed \n");
  }
}

void sql_exec(sqlite3 *db, const char* sql, int (*callback)(void*,int,char**,char**),void *arg, char **errmsg) {

}

void sql_prepare(sqlite3 *db, const char *zSql, int nByte, sqlite3_stmt **ppStmt, const char **pzTail) {
  prc = sqlite3_prepare_v2(db, zSql, nByte, ppStmt, pzTail);
  if (prc != SQLITE_OK) {
    die("sqlite3_prepare_v2 failed\n");
  }
}

void sql_step(sqlite3_stmt *stmt) {
  prc = sqlite3_step(stmt);
  if (prc != SQLITE_DONE) {
    printf("failed with %d\n", prc);
    die("sqlite3_step failed \n");
  }
}

void sql_finalize(sqlite3_stmt *stmt) {
  prc = sqlite3_finalize(stmt);
  if (prc != SQLITE_OK) {
    die("sqlite3_finalize failed \n");
  }
}