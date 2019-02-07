from slite_api import *
from stats import *
from graphs import *
from helpers import *
from sentinel_hub import *
import time
import multiprocessing as mp

"""
AVAILABLE LAYERS FOR api_key: "6b3365db-b23d-487f-8916-b035229bb13b"

"""


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

def get_index_data_procedure(conn, poly_id, layer, logg):
    all_clouds_masks, all_ndvis, evi_r, evi2_r, poly_mask, dates = get_sentinel_data_procedure(conn, poly_id, layer, logg)

    ndvis = get_index_statistics(all_ndvis, poly_mask, all_clouds_masks, dates)
    evis = get_index_statistics(evi_r, poly_mask, all_clouds_masks, dates)
    evi2s = get_index_statistics(evi2_r, poly_mask, all_clouds_masks, dates)

    print(f"FEATURE: poly_id = {poly_id}, st. vseh opazovanj: {len(all_clouds_masks)}, st. opazovanj brez oblacnosti: {len(ndvis[0])}")
    logg.log(f"FEATURE: poly_id = {poly_id}, st. vseh opazovanj: {len(all_clouds_masks)}, st. opazovanj brez oblacnosti: {len(ndvis[0])}")
    return ndvis, evis, evi2s


def update_for_category(raba_id):

    conn_main = sqliteConnector(r"./dbs/raba_2018.sqlite")
    min_area = 50
    qq = f"SELECT * from raba_2018 WHERE RABA_ID = {raba_id} AND Area(GEOMETRY) > {min_area}"
    cur = conn_main.execute(qq)
    conn_main.commit()
    logg = logger()
    iters = 20
    layer = "ALL-BANDS"

    t0 = time.time()
    conn_upsert = sqliteConnector(f"./dbs/{raba_id}.sqlite")
    conn_upsert_c = conn_upsert.commit()
    api_create_tables(conn_upsert)
    for k in range(iters):
        start = time.time()
        poly_id = next(cur)[0]
        ndvis, evis, evi2s = get_index_data_procedure(conn_main, poly_id, layer, logg)

        #TODO: efficiency for transactions!! must have
        api_upsert_db(conn_upsert, poly_id, ndvis, evis, evi2s)

        stop = time.time()

        logg.log(f"Updated: {poly_id} in {round(stop-start, 2)} seconds")
        print(f"Updated: {poly_id} in {round(stop-start, 2)} seconds")

    t1 = time.time()
    print(f"Za {iters} iteracij sem porabil: {t1-t0} sekund")

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
    # TODO
    # - paralelizacija na 8 procesov (izdelava 8 zacasnih baz in na koncu merganje med njimi)
    # - evi2 index ?
    # - vecji od 10m2 ali poljubne velikosti: done
    # - meadiana: done
    # - add new fields and create table statement(assets) for sqlite: done
    # - ndwi (water content in leafes)

    conn = sqliteConnector(r"./dbs/raba_2018.sqlite")
    RABE = [1300, 1321, 1100, 1160, 1180, 1190, 1211, 1212]

    update_for_category(1300)
    #pool = mp.Pool(processes=4)
    #out = pool.map(update_for_category, RABA)
    #results = [pool.apply_async(update_for_category, args=(x,)) for x in RABA]
    RABE = [1300]
    api_merge_temp_databases(conn, RABE)


    #save_graphs(conn, 34)

    # PRIDOBIVANJE PODATKOV
    # main query for raba polygons selection




