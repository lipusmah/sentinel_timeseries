from sklearn.svm import SVC
import scipy
from scipy.interpolate import interp1d

from main import *

def time_range_to_xaxis(data, date_range):
    dates_ind_out = []
    dates_out = []
    data_out = []
    comp_time = " 00:00:00"

    for val, date in data:
        date_comp = date.split()[0] + comp_time
        if date_comp in date_range:
            dates_ind_out.append(date_range.index(date_comp))
            dates_out.append(datetime.strptime(date, "%Y-%m-%d %H:%M:%S"))
            data_out.append(val)
        else:
            continue

    return data_out, dates_ind_out, dates_out


def api_get_bbox(conn, table, id_field, poly_id):
    query = f"SELECT AsGeoJSON(GEOMETRY), AsGeoJSON(Envelope(GEOMETRY)) FRdate_range[Unable to handle:]OM {table} where {id_field} = {poly_id}"
    cur = conn.execute(query)
    polygon_str, bbox_str = next(cur)

    polygon, bbox = json.loads(polygon_str)["coordinates"], json.loads(bbox_str)["coordinates"]

    return polygon, bbox


def get_xticks(mindate, maxdate):
    return [date for date in daterange_months(mindate, maxdate)]


def savgol_equal_vectors(dates, time_series, percent_data, degs, days=10):
    xs = []
    dates_inter = []
    for i, date in enumerate(dates):
        if i % days == 0:
            xs.append(i)
            dates_inter.append(date)

    dates = [str(i) for i in dates]
    out = []
    sav_out = []
    for poly in time_series:
        y, x, dates_ts = time_range_to_xaxis(poly, dates)
        window_in = round(len(poly) * percent_data)
        if window_in % 2 == 0:
            window_in += 1
        savgol = scipy.signal.savgol_filter(y, window_length=window_in, polyorder=degs)
        interpolate = interp1d(x, savgol, kind="nearest", fill_value="extrapolate")
        interpolated = interpolate(xs)
        #time_series_compared(interpolated, dates_inter, savgol, dates_ts)

        sav_out.append(savgol)
        out.append(interpolated)

    return (out, sav_out)

def save_data(conn, table, id_field, id_value, SRS="epsg:3912"):
    start = time.time()
    polygon, bbox = api_get_bbox(conn, table, id_field, id_value)

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
        api_upsert_db(conn, id_value, ndvis, evis, evi2s)
    except:
        api_create_tables(conn)
        api_upsert_db(conn, id_value, ndvis, evis, evi2s)

    stop = time.time()
    print(f"Feature id:{id_value} update from table: {table} in {round(stop-start)} seconds")

def svm(X, Y):
    pass


def daterange_days(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def get_vectors(conn, time_start, time_end,table, column, num):

    query = f"SELECT distinct id_poly FROM {table} LIMIT {num};"
    out = []
    ids = [int(i[0]) for i in conn.execute(query)]

    for i in ids:
        query_ts = f"SELECT {column}, epoch FROM {table} WHERE id_poly = {i} ORDER BY epoch ASC;"
        time_s = [j for j in conn.execute(query_ts)]
        out.append(time_s)

    return out



if __name__ == "__main__":
    os.chdir(os.path.split(sys.argv[0])[0])
    # get datatrue_data
    layer = "ALL-BANDS"

    true_conn = sqliteConnector(r"D:\git\sentinel_timeseries\dbs\samo_susni.sqlite")
    false_conn = sqliteConnector(r"D:\git\sentinel_timeseries\dbs\samo_nesusni.sqlite")

    # na 10 dni
    days = 10
    # time start, time end


    time_start, time_end = datetime(2017, 3, 1), datetime(2018, 10, 1)
    dates_range = list(daterange_days(time_start, time_end))


    true_data = get_vectors(true_conn, time_start, time_end, "index_ndvi", "mean", 95)
    false_data = get_vectors(false_conn, time_start, time_end, "index_ndvi", "mean", 95)

    true_savol_inter, true_savol = savgol_equal_vectors(dates_range, true_data, 0.10, 2)
    false_savol_inter, false_savol = savgol_equal_vectors(dates_range, false_data, 0.10, 2)

    true_learn = true_savol_inter[:70]
    false_learn = false_savol_inter[:70]

    true_assess = true_savol_inter[70:]
    false_assess = false_savol_inter[70:]

    learn_data_x = true_learn + false_learn
    learn_data_y = [1 for i in enumerate(true_learn)] + [0 for i in enumerate(false_learn)]

    classifier = SVC(kernel="linear")
    classifier.fit(learn_data_x, learn_data_y)

    #preštej vse pravilne in ne pravilne
    asserts_1 = 0
    asserts_0 = 0
    asserts_all = 0

    for i in classifier.predict(true_assess):
        if i == 1:
            asserts_1 += 1
    for i in classifier.predict(false_assess):
        if i == 0:
            asserts_0 += 1

    print(f"Natančnost določitve sušnih poligonov: {asserts_1/len(true_assess)}")
    print(f"Natančnost določitve ne sušnih poligonov: {asserts_0/len(false_assess)}")
    print(f"Skupna natančnost: {(asserts_1+asserts_0)/(len(true_assess)+len(false_assess))}")




    print()




    # true_conn = sqliteConnector(r"D:\git\sentinel_timeseries\dbs\samo_susni.sqlite")
    # true_query = "SELECT ogc_fid0 FROM samo_susni WHERE raba_id = 1300 AND Area(GEOMETRY) > 20000 and Area(GEOMETRY) < 40000 LIMIT 50;"
    # true_ids = [int(i[0]) for i in true_conn.execute(true_query)]
    #
    # for i in true_ids:
    #
    #     q = true_conn.execute(f"SELECT id_poly from index_ndvi WHERE id_poly = {int(i)}")
    #     ids = [i for i in q]
    #     if len(ids) == 0:
    #         save_data(true_conn, "samo_susni", "ogc_fid0", i)
    #     else:
    #         print(f"already in database {i}")
    #
    #     print(f"Skupping {i} due to memory error.")
    #
    # false_conn = sqliteConnector(r"D:\git\sentinel_timeseries\dbs\samo_nesusni.sqlite")
    # false_query = "SELECT ogc_fid0 FROM samo_nesusni WHERE Area(GEOMETRY) > 20000 and Area(GEOMETRY) < 40000 LIMIT 50;"
    # false_ids = [int(i[0]) for i in false_conn.execute(false_query)]
    #
    # for i in false_ids:
    #     q = false_conn.execute(f"SELECT id_poly from index_ndvi WHERE id_poly = {int(i)}")
    #     ids = [i for i in q]
    #     ids= []
    #     if len(ids) == 0:
    #         save_data(false_conn, "samo_nesusni", "ogc_fid0", i)
    #     else:
    #         print(f"already in database {i}")
    #
    #
    # print()
    # #run_for_one(conn, "raba_2018", ogc_id, smoother_parameters, layer, "epsg:3912")
