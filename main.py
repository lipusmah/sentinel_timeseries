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

def get_index_data_procedure(conn, poly_id, layer, logg):
    all_clouds_masks, all_ndvis, poly_mask, dates = get_sentinel_data_procedure(conn, poly_id, layer, logg)

    dates_used = []
    mean_ndvis = []
    std_ndvis = []
    min_ndvis = []
    max_ndvis = []
    median_ndvis = []

    poly_nan = poly_mask.astype(float)
    poly_nan[poly_nan == 0.0000] = np.nan

    for i, x in enumerate(all_clouds_masks):
        mask = x ^ 1
        poly_clouds = mask * poly_nan

        if np.count_nonzero(~np.isnan(poly_clouds)) > round(np.count_nonzero(~np.isnan(poly_nan))/3.1):
            ndvis_tf = poly_clouds * all_ndvis[i]
            maxi = np.nanmax(ndvis_tf)
            mini = np.nanmin(ndvis_tf)
            if maxi != 0 and mini != 0:
                mean_ndvis.append(np.nanmean(ndvis_tf))
                std_ndvis.append(np.nanstd(ndvis_tf))
                min_ndvis.append(mini)
                max_ndvis.append(maxi)
                median_ndvis.append(np.nanmedian(ndvis_tf))
                dates_used.append(dates[i])

    print(f"FEATURE: poly_id = {poly_id}, st. vseh opazovanj: {len(all_clouds_masks)}, st. opazovanj brez oblacnosti: {len(mean_ndvis)}")
    logg.log(f"FEATURE: poly_id = {poly_id}, st. vseh opazovanj: {len(all_clouds_masks)}, st. opazovanj brez oblacnosti: {len(mean_ndvis)}")
    return mean_ndvis, std_ndvis, min_ndvis, max_ndvis, median_ndvis, dates_used


def update_for_category(raba_id):
    conn = sqliteConnector(r"./dbs/raba_2018.sqlite")
    min_area = 50
    qq = f"SELECT * from raba_2018 WHERE RABA_ID = {raba_id} AND Area(GEOMETRY) > {min_area}"
    cur = conn.execute(qq)
    conn.commit()
    logg = logger()
    iters = 20
    layer = "ALL-BANDS"

    t0 = time.time()
    for k in range(iters):
        start = time.time()
        poly_id = next(cur)[0]
        mean_ndvis, std_ndvis, min_ndvis, max_ndvis, median_ndvis, dates = get_index_data_procedure(conn, poly_id,
                                                                                                    layer, logg)

        api_upsert_db(conn, poly_id, mean_ndvis, std_ndvis, min_ndvis, max_ndvis, median_ndvis, dates)

        stop = time.time()

        logg.log(f"Updated: {poly_id} in {round(stop-start, 2)} seconds")
        print(f"Updated: {poly_id} in {round(stop-start, 2)} seconds")

    t1 = time.time()
    print(f"Za {iters} iteracij sem porabil: {t1-t0} sekund")

def save_graphs(conn, poly_id):

    graph_data = api_ndvi_stats_for_poly(conn, poly_id)

    xs, out_lowes_y = lowess_fit_mean(graph_data, 0.20, 5)
    out_savgol_y = savgol_fit_mean(graph_data, 0.20, 5)

    xs1, out_lowes_y_median = lowess_fit_median(graph_data, 0.20, 5)
    out_savgol_y_median = savgol_fit_mean(graph_data, 0.20, 5)

    mean_fit_graph(graph_data, out_lowes_y, out_savgol_y, poly_id)
    median_fit_graph(graph_data, out_lowes_y_median, out_savgol_y_median, poly_id)


if __name__ == "__main__":
    # TODO
    # - paralelizacija na 8 procesov
    # - evi2 index ?
    # - vecji od 10m2 ali poljubne velikosti: done
    # - meadiana: done
    # - add new fields and create table statement(assets) for sqlite: done
    # - ndwi (water content in leafes)

    conn = sqliteConnector(r"./dbs/raba_2018.sqlite")
    RABA = [1300, 1321, 1100, 1160, 1180, 1190, 1211, 1212]
    pool = mp.Pool(processes=4)
    #out = pool.map(update_for_category, RABA)
    results = [pool.apply_async(update_for_category, args=(x,)) for x in RABA]

    # PRIDOBIVANJE PODATKOV
    # main query for raba polygons selection




