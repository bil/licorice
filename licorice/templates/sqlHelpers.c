#include <sqlite3.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include "utilityFunctions.h"
#include "sqlHelpers.h"

static int prc;

void sql_bind_int(sqlite3_stmt *stmt, int index, const char* dtype, const void* value) { 
  int val;
  if (strstr(dtype, "8") != NULL) {
    // int8
    val = *(char *)value;
  } else if (strstr(dtype, "16") != NULL) {
    // int16
    val = *(short *)value;
  } else {
    // int32
    val = *(long *)value;
  }
  prc = sqlite3_bind_int(stmt, index, val);
  if (prc != SQLITE_OK) {
    die("sqlite3_bind_int failed \n");
  }
}

void sql_bind_int64(sqlite3_stmt *stmt, int index, const void* value) {
  prc = sqlite3_bind_int64(stmt, index, *(sqlite3_int64 *)value);
  if (prc != SQLITE_OK) {
    die("sqlite3_bind_int64 failed \n");
  }
}

void sql_bind_double(sqlite3_stmt *stmt, int index, const char* dtype, const void* value) { 
  double val;
  if (strstr(dtype, "32") != NULL){
    // float
    val = *(float *)value;
  } else {
    // double
    val = *(double *)value;
  }
  prc = sqlite3_bind_double(stmt, index, val);
  if (prc != SQLITE_OK) {
    die("sqlite3_bind_double failed \n");
  }
}

void sql_bind_text(sqlite3_stmt *stmt, int index, const void* value, int numBytes, void(*destructor)(void*)) {
  prc = sqlite3_bind_text(stmt, index, (const char *)value, numBytes, destructor);
  if (prc != SQLITE_OK) {
    die("sqlite3_bind_text failed \n");
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
    die("sqlite3_prepare_v2 failed: %d\n", prc);
  }
}

void sql_step(sqlite3_stmt *stmt) {
  prc = sqlite3_step(stmt);
  if (prc != SQLITE_DONE) {
    printf("failed with %d\n", prc);
    die("sqlite3_step failed: %d\n", prc);
  }
}

void sql_finalize(sqlite3_stmt *stmt) {
  prc = sqlite3_finalize(stmt);
  if (prc != SQLITE_OK) {
    die("sqlite3_finalize failed: %d \n", prc);
  }
}

static char buf[64];
static char db_index_str[DB_INDEX_PAD_LENGTH];
static int rc;
static int tempVal = 0;
static char tempBuf[16];
static int flags;
static char *zErrMsg = NULL;
void openDatabase(
  sqlite3 **db, char* startName, int db_index, char* newNameLocation
) {
  if(strlen(startName) > 48 - DB_INDEX_PAD_LENGTH) { // was > 48, but now need to leave room for db index
    sprintf(buf, "Name %s too long.\n", startName);
    die(buf);
  }
  strcpy(buf, startName);
  strcat(buf, "_");
  sprintf(db_index_str, "%d", db_index);
  // add preceding zeros for db index
  for (int i = 0; i < DB_INDEX_PAD_LENGTH - strlen(db_index_str); i++) {
    strcat(buf, "0");
  }
  strcat(buf, db_index_str);
  strcat(buf,".db");
  flags = SQLITE_OPEN_READWRITE; // | SQLITE_OPEN_MEMORY;
  rc = sqlite3_open_v2(buf, db, flags, NULL);
  while(!rc) {
    tempVal++;
    sqlite3_close(*db);
    //int max for 4 byte integer
    if(tempVal == 2147483647) {
      die("Too many files. Clean up workspace.\n");
    }
    strcpy(buf, startName);

    sprintf(tempBuf,"(%d)",tempVal);
    strcat(buf, tempBuf);
    strcat(buf,".db");
    rc = sqlite3_open_v2(buf, db, flags, NULL);
  }
  sqlite3_open(buf, db);
  strcpy(newNameLocation,buf);

  // chown(buf, atoi(getenv("SUDO_UID")), atoi(getenv("SUDO_GID"))); // set db file ownership to user
}

static char* cmd;
static int i,j;
void createTables(sqlite3 *db, SQLTable* databaseArr, int numTables) {
  for(i = 0; i < numTables; i++) {
    size_t queryLen = (
      strlen(CREATE_TABLE_STR) + strlen(databaseArr[i].tableName) +
      strlen(OPEN_BRACE) + strlen(CLOSE_BRACE_SEMI)
    );
    for (j = 0; j < databaseArr[i].numCol; j++) {
      queryLen += strlen(databaseArr[i].columns[j].colName);
      queryLen += strlen(SPACE);
      queryLen += strlen(databaseArr[i].columns[j].SQLtype);
      queryLen += strlen(COMMA);
      queryLen += strlen(SPACE);
    }
    queryLen -= strlen(COMMA);
    queryLen -= strlen(SPACE);
    //+1 for null terminator
    cmd = (char*) malloc(queryLen + 1);
    strcpy(cmd, CREATE_TABLE_STR);
    strcat(cmd, databaseArr[i].tableName);
    strcat(cmd, OPEN_BRACE);
    for(j = 0; j < databaseArr[i].numCol; j++) {
      strcat(cmd, databaseArr[i].columns[j].colName);
      strcat(cmd, SPACE);
      strcat(cmd, databaseArr[i].columns[j].SQLtype);
      if(j < (databaseArr[i].numCol - 1)) {
        strcat(cmd, COMMA);
        strcat(cmd, SPACE);
      }
    } 
    strcat(cmd, CLOSE_BRACE_SEMI);
    rc = sqlite3_exec(db, cmd, NULL, NULL, &zErrMsg);
    if (rc != SQLITE_OK) {
      printf("%s\n", zErrMsg);
      fflush(stdout);
      sqlite3_free(zErrMsg);
      die("SQL exec error\n");
    }
    fflush(stdout);
  }
}
