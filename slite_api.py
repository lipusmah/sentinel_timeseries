import sqlite3
import os
import sys
from geomet import wkt
import json

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

    def execute(self, query):
        return self.conn.execute(query)

    def commit(self):
        self.conn.commit()


def api_upsert_db(conn, id_poly, mean_ndvis, std_ndvis, min_ndvis, max_ndvis, median, dates):
    #delete existing
    del_query = f"DELETE FROM index_ndvi WHERE id_poly={id_poly}"
    conn.execute(del_query)

    query = "INSERT INTO index_ndvi (id_poly, minimum, maximum, median, mean, stdev, epoch) " \
                               "VALUES ({}, {}, {}, {}, {}, {}, '{}')"

    for i, mean in enumerate(mean_ndvis):
        in_query = query.format(id_poly, min_ndvis[i], max_ndvis[i], median[i], mean, std_ndvis[i], dates[i])
        conn.execute(in_query)

    conn.commit()


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
