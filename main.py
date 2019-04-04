from slite_api import *
from stats import *
from graphs import *
from helpers import *
from sentinel_hub import *
import time
from multiprocessing import Pool
from os.path import isfile

def get_index_statistics(index_array, poly_mask, clouds_mask_array, dates):
    dates_ = []
    mean_ = []
    std_ = []
    min_ = []
    max_ = []
    median_ = []

    poly_nan = poly_mask.astype(float)
    poly_nan[poly_nan == 0.0000] = np.nan

    for i, x in enumerate(clouds_mask_array):
        mask = x ^ 1
        poly_clouds = mask * poly_nan
        poly_clouds = poly_clouds.astype(float)
        poly_clouds[poly_clouds == 0.0000] = np.nan

        if np.count_nonzero(~np.isnan(poly_clouds)) > round(np.count_nonzero(~np.isnan(poly_nan)) / 3.1):
            index_tf = poly_clouds * index_array[i] # index for timeframe
            if not np.isnan(index_tf).all():
                maxi = np.nanmax(index_tf)
                mini = np.nanmin(index_tf)
                if maxi != 0 and mini != 0:
                    mean_.append(np.nanmean(index_tf))
                    std_.append(np.nanstd(index_tf))
                    min_.append(mini)
                    max_.append(maxi)
                    median_.append(np.nanmedian(index_tf))
                    dates_.append(dates[i])

    return mean_, std_, min_, max_, median_, dates_

def get_index_data_procedure(conn, poly_id, layer):
    all_clouds_masks, all_ndvis, evi_r, evi2_r, poly_mask, dates = get_sentinel_data_procedure(conn, poly_id, layer)

    ndvis = get_index_statistics(all_ndvis, poly_mask, all_clouds_masks, dates)
    evis = get_index_statistics(evi_r, poly_mask, all_clouds_masks, dates)
    evi2s = get_index_statistics(evi2_r, poly_mask, all_clouds_masks, dates)

    return ndvis, evis, evi2s


def update_for_category(raba_id, min_area = 300, layer = "ALL-BANDS"):

    conn_main = sqliteConnector(r"./dbs/raba_2018.sqlite")

    if isfile(f"./dbs/{raba_id}.sqlite"):
        conn_upsert = sqliteConnector(f"./dbs/{raba_id}.sqlite")
        max_raba_id_query = "SELECT MAX(id_poly) FROM index_ndvi"
        max_raba_id = next(conn_upsert.execute(max_raba_id_query))[0]
        qq = f"SELECT * from raba_2018 WHERE RABA_ID = {raba_id} AND Area(GEOMETRY) > {min_area} AND OGC_FID >= {max_raba_id};"
        cur = conn_main.execute(qq)
    else:
        conn_upsert = sqliteConnector(f"./dbs/{raba_id}.sqlite")
        api_create_tables(conn_upsert)
        conn_upsert.commit()
        qq = f"SELECT * from raba_2018 WHERE RABA_ID = {raba_id} AND Area(GEOMETRY) > {min_area};"
        cur = conn_main.execute(qq)

    t0 = time.time()

    for k in cur:
        start = time.time()
        poly_id = k[0]
        ndvis, evis, evi2s = get_index_data_procedure(conn_main, poly_id, layer)

        #TODO: efficiency for transactions!! must have
        api_upsert_db(conn_upsert, poly_id, ndvis, evis, evi2s)
        stop = time.time()
        print(f"Updated: raba:{raba_id}, polygon ID:{poly_id}, time:{round(stop-start, 2)} seconds")


def save_graphs(conn, poly_id):

    graph_data = api_ndvi_stats_for_poly(conn, poly_id)

    if len(graph_data) == 0:
        return None

    xs, out_lowes_y = lowess_fit_mean(graph_data, 0.20, 5)
    out_savgol_y = savgol_fit_mean(graph_data, 0.20, 5)

    xs1, out_lowes_y_median = lowess_fit_median(graph_data, 0.20, 5)
    out_savgol_y_median = savgol_fit_mean(graph_data, 0.20, 5)

    mean_fit_graph(graph_data, out_lowes_y, out_savgol_y, poly_id)
    median_fit_graph(graph_data, out_lowes_y_median, out_savgol_y_median, poly_id)


if __name__ == "__main__":

    #provide your api key here or create assets/api.id file
    #api_key = read_api_key() look at sentinel_hub.py -> get_all_bands function

    conn = sqliteConnector(r"./dbs/raba_2018.sqlite")
    RABE = [1100, 1160, 1180, 1190, 1300, 1321, 1211, 1212,
        1221,1222,1230, 1240, 1410, 1420, 1500, 1600, 1800, 2000]
    #update_for_category(1300)

    proc_num = 18
    pool = Pool(proc_num)
    out = pool.map(update_for_category, RABE)

    #api_merge_temp_databases(conn, RABE)

    #save_graphs(conn, 34)

