from slite_api import *
from stats import *
from graphs import *
from helpers import *
from sentinel_hub import *
import time
from multiprocessing import Pool
from os.path import isfile


def save_graphs(conn, poly_id, index="ndvi"):
    """
    :param conn: sqliteConnector object from slite_api.py file
    :param poly_id: ogc_id of the polygon feature
    :param index: string, working options: "ndvi", "evi", "evi2"
    :return:
    """
    graph_data = api_get_timeseries(conn, poly_id, index)

    if len(graph_data) == 0:
        raise Exception("No timeseries data for this polygon feature in database")

    xs, out_lowes_y = lowess_fit_mean(graph_data, 0.20, 5)
    out_savgol_y = savgol_fit_mean(graph_data, 0.20, 5)

    xs1, out_lowes_y_median = lowess_fit_median(graph_data, 0.20, 5)
    out_savgol_y_median = savgol_fit_mean(graph_data, 0.20, 5)

    mean_fit_graph(graph_data, out_lowes_y, out_savgol_y, poly_id, index)
    median_fit_graph(graph_data, out_lowes_y_median, out_savgol_y_median, poly_id, index)


def update_for_category(raba_id, min_area=300, layer="ALL-BANDS", SRS="epsg:3912"):

    def proc_for_one(conn, ogc_id, table="raba_2018"):
        polygon, bbox = api_get_bbox(conn, table, ogc_id)
        all_bands, all_clouds_masks, dates = get_all_bands(bbox, layer, SRS)

        ndvi_r = [extract_ndvi(epoch) for epoch in all_bands]
        evi_r = [extract_evi(epoch) for epoch in all_bands]
        evi2_r = [extract_evi2(epoch) for epoch in all_bands]

        poly_mask = toRaster(polygon, bbox)

        ndvis = get_index_statistics(ndvi_r, poly_mask, all_clouds_masks, dates)
        evis = get_index_statistics(evi_r, poly_mask, all_clouds_masks, dates)
        evi2s = get_index_statistics(evi2_r, poly_mask, all_clouds_masks, dates)

        return ndvis, evis, evi2s

    conn_main = sqliteConnector(r"./dbs/raba_2018.sqlite")

    if isfile(f"./dbs/{raba_id}.sqlite"):
        conn_upsert = sqliteConnector(f"./dbs/{raba_id}.sqlite")
        max_raba_id_query = "SELECT MAX(id_poly) FROM index_ndvi"
        max_raba_id = next(conn_upsert.execute(max_raba_id_query))[0]
        if max_raba_id is not None:
            qq = f"SELECT * from raba_2018 WHERE RABA_ID = {raba_id} AND Area(GEOMETRY) > {min_area} AND OGC_FID >= {max_raba_id};"
            cur = conn_main.execute(qq)
        else:
            qq = f"SELECT * from raba_2018 WHERE RABA_ID = {raba_id} AND Area(GEOMETRY) > {min_area};"
            cur = conn_main.execute(qq)
    else:
        conn_upsert = sqliteConnector(f"./dbs/{raba_id}.sqlite")
        api_create_tables(conn_upsert)
        conn_upsert.commit()
        qq = f"SELECT * from raba_2018 WHERE RABA_ID = {raba_id} AND Area(GEOMETRY) > {min_area};"
        cur = conn_main.execute(qq)

    for k in cur:
        start = time.time()
        poly_id = k[0]

        ndvis, evis, evi2s = proc_for_one(conn_main, poly_id)
        api_upsert_db(conn_upsert, poly_id, ndvis, evis, evi2s)

        stop = time.time()
        print(f"Updated: raba:{raba_id}, polygon ID:{poly_id}, time:{round(stop-start, 2)} seconds")


def run_for_one(conn, table, ogc_id, layer="ALL-BANDS", SRS="epsg:3912"):
    """
    Creates tables in *.sqlite db file for storing time series (see ./assets/). Saves time series in created
    tables. Reads created table for ogc_id and plots the results for years 2017/2018.

    Upserts by ogc_id so it deletes old entries.

    Smoothing functions parameters can be changed in save_graphs() function.

    :param: conn: sqliteConnector object from slite_api.py file
    :param: table: name of the table with polygon features
    :param: ogc_id: ID of wanted polygon
    :return: Saves images to ./images/ folder with name {ogc_id}_mean.png
    """

    start = time.time()

    polygon, bbox = api_get_bbox(conn, table, ogc_id)
    if SRS is not None:
        all_bands, all_clouds_masks, dates = get_all_bands(bbox, layer, SRS)
    else:
        all_bands, all_clouds_masks, dates = get_all_bands(bbox, layer)  # SRS is epsg:3912 (default)

    ndvi_r = [extract_ndvi(epoch) for epoch in all_bands]
    evi_r = [extract_evi(epoch) for epoch in all_bands]
    evi2_r = [extract_evi2(epoch) for epoch in all_bands]
    poly_mask = toRaster(polygon, bbox)

    ndvis = get_index_statistics(ndvi_r, poly_mask, all_clouds_masks, dates)
    evis = get_index_statistics(evi_r, poly_mask, all_clouds_masks, dates)
    evi2s = get_index_statistics(evi2_r, poly_mask, all_clouds_masks, dates)

    try:
        api_upsert_db(conn, ogc_id, ndvis, evis, evi2s)
    except:
        api_create_tables(conn)
        api_upsert_db(conn, ogc_id, ndvis, evis, evi2s)

    stop = time.time()
    print(f"Saved time series for polygon: {ogc_id}, table: {table}. Time taken: {round(stop-start, 2)} sec.")
    print("Saving graphs for all indices ...")
    save_graphs(conn, ogc_id, "ndvi")
    save_graphs(conn, ogc_id, "evi")
    save_graphs(conn, ogc_id, "evi2")
    print("Graphs successfully saved in ./images/ folder.")

if __name__ == "__main__":
    # provide your api key here or create assets/api.id file
    # api_key = read_api_key() look at sentinel_hub.py -> get_all_bands function

    conn = sqliteConnector(r"./dbs/raba_2018.sqlite")
    layer = "ALL-BANDS"# one of the layers registered on sentinel-hub configurator
    # FOR GETTING TIMESERIES FOR ONE POLYGON (saves timeseries)
    # Change parameters for smoothing functions in save_graphs() function
    
    # Sample polygons
    ogc_ids = [500, 292370, 1027557, 706496]
    # Create graphs
    for id in ogc_ids:
        print("Time series for", id)
        run_for_one(conn, "raba_2018", id, layer, "epsg:3912")

    ## FOR BUILDING DATABASE
    # RABE = [1100, 1160, 1180, 1190, 1300, 1321, 1211, 1212, 1221,
    #         1222, 1230, 1240, 1410, 1420, 1500, 1600, 1800, 2000]
    # proc_num = 18
    # pool = Pool(proc_num)
    # out = pool.map(update_for_category, RABE)
    # api_merge_temp_databases(conn, RABE)
