from slite_api import *
from stats import *
from graphs import *
from helpers import *
from sentinel_hub import *
import time
"""
AVAILABLE LAYERS FOR api_key: "6b3365db-b23d-487f-8916-b035229bb13b"

"""

def get_ndvi_data_procedure(conn, poly_id, layer, logg):
    all_clouds_masks, all_ndvis, poly_mask, dates = get_sentinel_data_procedure(conn, poly_id, layer, logg)

    dates_used = []
    mean_ndvis = []
    std_ndvis = []
    min_ndvis = []
    max_ndvis = []
    poly_nan = poly_mask.astype(float)
    poly_nan[poly_nan == 0.0000] = np.nan

    for i, x in enumerate(all_clouds_masks):
        mask = x ^ 1
        if np.count_nonzero(mask) > 0:
            ndvis_tf = mask * poly_nan * all_ndvis[i]
            if np.isnan(ndvis_tf).all():
                continue
            else:
                mean_ndvis.append(np.nanmean(ndvis_tf))
                std_ndvis.append(np.nanstd(ndvis_tf))
                min_ndvis.append(np.nanmin(ndvis_tf))
                max_ndvis.append(np.nanmax(ndvis_tf))
                dates_used.append(dates[i])

    print(f"FEATURE: poly_id = {poly_id}, st. vseh opazovanj: {len(all_clouds_masks)}, st. opazovanj brez oblacnosti: {len(mean_ndvis)}")
    logg.log(f"FEATURE: poly_id = {poly_id}, st. vseh opazovanj: {len(all_clouds_masks)}, st. opazovanj brez oblacnosti: {len(mean_ndvis)}")
    return mean_ndvis, std_ndvis, min_ndvis, max_ndvis, dates_used

def save_data_procedure(poly_id, mean_ndvis, std_ndvis, min_ndvis, max_ndvis, dates):
    pass

def get_graph(conn, poly_id):
    pass


if __name__ == "__main__":
    # TODO
    # - paralelizacija na 8 procesov
    # - evi2 index
    # - meadiana
    # - ndwi (water content in leafes)

    LAYER1 = "SENTINEL2-L2A-NDVI"
    #LAYER2 = "SENTINEL2-L1C-NDVI"
    LAYER3 = "LANDSAT8-NDVI"

    LAYERS = [LAYER1, LAYER3]

    conn = sqliteConnector(r"./dbs/raba_2018.sqlite")
    RABA = 1300
    layer = "ALL-BANDS"

    # PRIDOBIVANJE PODATKOV

    qq = f"SELECT * from raba_2018 WHERE RABA_ID = {RABA} AND ogc_fid > 98"
    cur = conn.execute(qq)
    logg = logger()
    iters = 20

    t0 = time.time()
    for k in range(iters):
        start = time.time()
        poly_id = next(cur)[0]
        mean_ndvis, std_ndvis, min_ndvis, max_ndvis, dates = get_ndvi_data_procedure(conn, poly_id, layer, logg)
        api_upsert_db(conn, poly_id, mean_ndvis, std_ndvis, min_ndvis, max_ndvis, dates, RABA)
        stop = time.time()

        logg.log(f"Updated: {poly_id} in {round(stop-start, 2)} seconds")
        print(f"Updated: {poly_id} in {round(stop-start, 2)} seconds")

    t1 = time.time()
    print(f"Za {iters} iteracij sem porabil: {t1-t0} sekund")

    # IZRIS GRAFOV - ZA ZDAJ SE EN POMEMBEN
    poly_id = 87
    graph_data = api_get_stats_for_poly(conn, poly_id)

    xs, out_lowes_y = lowess_fit(graph_data, 0.20, 5)
    out_savgol_y = savgol_fit(graph_data, 0.20, 5)

    mean_fit_graph(graph_data, out_lowes_y, out_savgol_y, poly_id)

