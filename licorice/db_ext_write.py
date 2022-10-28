import glob
import os
import sqlite3
import time

import msgpack
import yaml


def createTables(cur, table):
    if table == "metadata":
        dir_name = "yaml"
    else:
        dir_name = "code"

    dir_path = os.path.join(os.getenv("BINARY_DIR"), dir_name)
    if not (os.path.exists(dir_path)):
        return

    cur.execute(
        "CREATE TABLE IF NOT EXISTS "
        + table
        + " (Filename TEXT, Timestamp DATETIME, File Contents BLOB)"
    )
    con.text_factory = str

    for filename in os.listdir(dir_path):
        if table == "metadata":
            if filename[-5:] != ".yaml":  # check if filename is true yaml file
                continue
        file_path = os.path.join(dir_path, filename)
        file_stat = os.stat(file_path)
        mtime = file_stat.st_mtime
        if dir_name == "yaml":
            contents = yaml.safe_load(open(file_path, "r"))
        else:
            f = open(file_path, "r")
            contents = f.read()
        packed_contents = msgpack.packb(contents)
        # insert into database
        cur.execute(
            "INSERT INTO " + table + " VALUES (?,?,?)",
            (filename, mtime, packed_contents),
        )


# MAIN
while True:
    out_dir_path = os.getenv("BINARY_DIR")

    # check all existing databases in directory
    f = glob.glob(os.path.join(out_dir_path, "data", ".db"))
    if not f:
        time.sleep(5)
        continue

    # connect to most recently closed database
    u_index = f[0].rfind("_")  # index of underscore
    indices = [int(i[u_index + 1 : -3]) for i in f]  # database indices
    if max(indices) == 0:  # first database still being created
        time.sleep(5)
        continue
    cur_index = indices.index(
        max(indices) - 1
    )  # index in array corresponding to most recently closed db

    con = sqlite3.connect(f[cur_index])
    cur = con.cursor()

    # create metadata and code tables if nonexistent
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        ("metadata",),
    )
    t1 = cur.fetchone()
    if t1 is None:
        createTables(cur, "metadata")
        createTables(cur, "code")

    # commit changes and close the database
    con.commit()
    con.close()

    time.sleep(5)
