import sqlite3
import os
import sys
from geomet import wkt
import json
import time

# environment variables
working_dir = os.path.dirname(os.path.abspath(__file__))
api_key = "6b3365db-b23d-487f-8916-b035229bb13b"


class sqliteConnector:
    def __init__(self, db, libdir=None):
        if libdir is None:
            if sys.platform == "linux" or sys.platform == "linux2":
                libdir = os.path.dirname(os.path.abspath(__file__)) + "/spatialite/linux"
            elif sys.platform == "darwin":
                libdir = os.path.dirname(os.path.abspath(__file__)) + "/spatialite/mac"
            elif sys.platform == "win32" or sys.platform == "win64":
                libdir = os.path.dirname(os.path.abspath(__file__)) + r"\spatialite\windows"

        os.environ["path"] = libdir + ';' + os.environ['PATH']

        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")

        self.conn = conn

    def cursor(self):
        return self.conn.cursor()

    def execute(self, query):
        return self.conn.execute(query)

    def executemany(self, query, data):
        return self.conn.executemany(query, data)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


def api_upsert_db(conn, poly_id, ndvis, evis, evi2s):
    # delete existing
    tables = ["index_ndvi", "index_evi", "index_evi2"]
    for table in tables:
        del_query = f"DELETE FROM {table} WHERE id_poly={poly_id}"
        try:
            conn.execute(del_query)
        except:
            time.sleep(0.1)
            try:
                conn.execute(del_query)
            except:
                time.sleep(0.5)
        conn.commit()

    # insert new
    for table, data in zip(tables, [ndvis, evis, evi2s]):
        mean_, std_, min_, max_, median_, dates = data
        data_insert = []
        for i, date in enumerate(dates):
            data_insert.append([poly_id, min_[i], max_[i], median_[i], mean_[i], std_[i], date])

        query = "INSERT INTO {} (id_poly, minimum, maximum, median, mean, stdev, epoch) " \
                                 "VALUES (?, ?, ?, ?, ?, ?, ?)".format(table)

        conn.executemany(query, data_insert)
        # for i, mean in enumerate(mean_):
        #     in_query = query.format(table, poly_id, min_[i], max_[i], median_[i], mean, std_[i], dates[i])
        #     conn.execute(in_query)
        #     conn.commit()


def api_ndvi_stats_for_poly(conn, poly_id):
    query = f"SELECT epoch, mean, stdev, median FROM index_ndvi WHERE id_poly={poly_id} ORDER BY epoch ASC"
    cur = conn.execute(query)
    all_epoch = [i for i in cur]
    return all_epoch


def api_get_bbox(conn, poly_id):
    query = f"SELECT AsGeoJSON(GEOMETRY), AsGeoJSON(Envelope(GEOMETRY)) FROM raba_2018 where ogc_fid = {poly_id}"
    cur = conn.execute(query)
    polygon_str, bbox_str = next(cur)

    polygon, bbox = json.loads(polygon_str)["coordinates"], json.loads(bbox_str)["coordinates"]

    return polygon, bbox


def api_poly_bbox(conn, poly_id):
    query = f"SELECT AsText(GEOMETRY), AsText(Envelope(GEOMETRY)) FROM raba_2018 where ogc_fid = {poly_id}"
    cur = conn.execute(query)
    polygon, bbox = next(cur)

    bbox = wkt.loads(bbox)["coordinates"]
    polygon = wkt.loads(polygon)["coordinates"]

    return polygon, bbox


def api_create_tables(conn_upsert):
    with open("./assets/create_index_ndvi.txt") as ndvi_create:
        ndvi_table = ndvi_create.read()
        conn_upsert.execute(ndvi_table)
        conn_upsert.commit()

    with open("./assets/create_index_evi.txt") as evi_create:
        evi_table = evi_create.read()
        conn_upsert.execute(evi_table)
        conn_upsert.commit()

    with open("./assets/create_index_evi2.txt") as evi2_create:
        evi2_table = evi2_create.read()
        conn_upsert.execute(evi2_table)
        conn_upsert.commit()


def api_merge_temp_databases(conn, RABE):
    """
    :param conn: V katero bazo se napolnijo podatki
    :param RABE: Vse rabe, ki so bile uporabljene
    :return: None
    """
    tables = ["index_ndvi", "index_evi", "index_evi2"]
    for raba_id in RABE:
        raba_loc = "./dbs/{}.sqlite".format(raba_id)
        conn_raba = sqliteConnector(raba_loc)

        for table in tables:
            cur_ndvi = conn_raba.execute("SELECT id_poly, minimum, maximum, median, mean, stdev, epoch "
                                         "FROM {}".format(table))

            temp_table_data = [(poly_id, min_, max_, median_, mean_, std_, date) for
                               (poly_id, min_, max_, median_, mean_, std_, date) in cur_ndvi]
            query = "INSERT INTO {} (id_poly, minimum, maximum, median, mean, stdev, epoch) " \
                    "VALUES (?, ?, ?, ?, ?, ?, ?)".format(table)

            conn.executemany(query, temp_table_data)

        conn_raba.close()
        os.remove(raba_loc)

