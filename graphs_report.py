import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from helpers import daterange_months
import sentinelhub
import os
from stats import *
from whittaker_eilers import *
from slite_api import *
from graphs import *

def save_graphs(conn, poly_id, smooth_param=None, index="ndvi"):
    """
    :param conn: sqliteConnector object from slite_api.py file
    :param poly_id: ogc_id of the polygon feature
    :param: smooth_params: dict: values for smoothing parameters, if none take default
    :param index: string, working options: "ndvi", "evi", "evi2"
    :return:
    """
    if smooth_param is None:
        smooth_param = {
            "loess": {"frac": 0.20, "it": 10},
            "savitzky-golay": {"frac": 0.20, "polyorder": 2},
            "whittaker-eilers": {"lambda": 1, "order": 2}
        }


    graph_data = api_get_timeseries(conn, poly_id, index)

    if len(graph_data) == 0:
        raise Exception("No timeseries data for this polygon feature in database")

    xs, out_lowes_y = lowess_fit_mean(graph_data, smooth_param["loess"]["frac"], smooth_param["loess"]["it"])
    out_savgol_y = savgol_fit_mean(graph_data,
                                   smooth_param["savitzky-golay"]["frac"],
                                   smooth_param["savitzky-golay"]["polyorder"])

    xs1, out_lowes_y_median = lowess_fit_median(graph_data, smooth_param["loess"]["frac"], smooth_param["loess"]["it"])
    out_savgol_y_median = savgol_fit_mean(graph_data,
                                          smooth_param["savitzky-golay"]["frac"],
                                          smooth_param["savitzky-golay"]["polyorder"])

    out_whittaker = whittaker_smooth(np.asarray([i[1] for i in graph_data]), smooth_param["whittaker-eilers"]["lambda"])
    out_whittaker_median = whittaker_smooth(np.asarray([i[-1] for i in graph_data]), 1)

    mean_fit_graph(graph_data, out_lowes_y, out_savgol_y, out_whittaker, poly_id, index)
    median_fit_graph(graph_data, out_lowes_y_median, out_savgol_y_median, out_whittaker_median, poly_id, index)


def parameters_comparison(conn, poly_id, index):


    graph_data = api_get_timeseries(conn, poly_id, index)

    if len(graph_data) == 0:
        raise Exception("No timeseries data for this polygon feature in database")


    out_savgol_y = savgol_fit_mean(graph_data,0.05, 2)
    out_savgol_y1 = savgol_fit_mean(graph_data, 0.10, 2)
    out_savgol_y2 = savgol_fit_mean(graph_data, 0.20, 2)
    out_savgol_y3 = savgol_fit_mean(graph_data, 0.30, 2)
    out_savgol_y4 = savgol_fit_mean(graph_data, 0.40, 2)

    dates = [np.datetime64(i[0].split()[0], 'D') for i in graph_data]
    means = [i[1] for i in graph_data]

    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    yearsFmt = mdates.DateFormatter('%Y')
    monthsFmt = mdates.DateFormatter("%b")

    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111)


    ax.plot(dates, means, "-", color= "black", label=r"vrednosti indeksa")
    #ax.plot(dates, out_savgol_y, '-', color="green", label=r"$\alpha$ = 5%")
    ax.plot(dates, out_savgol_y1, '-', color="orange", label = r"$\alpha$ = 10%")
    ax.plot(dates, out_savgol_y2, "-", color= "red", label= r"$\alpha$ = 20%")
    ax.plot(dates, out_savgol_y3, '-', color="blue", label=r"$\alpha$ = 30%")
    ax.plot(dates, out_savgol_y4, "-", color="pink", label=r"$\alpha$ = 40%")

    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.xaxis.set_minor_formatter(monthsFmt)

    ax.xaxis.set_tick_params(which='major', grid_linewidth=1.5, pad=15)

    datemin = np.datetime64(dates[0], 'D')
    datemax = np.datetime64(dates[-1], 'D')
    ax.set_xlim(str(datemin), str(datemax))

    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.format_ydata = graph_data[0]
    ax.grid(True, which="both")
    plt.title('Primerjava parametrov pri glajenju s Savitzky-Golay filtrom.')
    plt.ylabel(index.upper())
    plt.xlabel('Datum')
    plt.legend()

    plt.savefig(f"./images/parameter_comparison_{poly_id}.png")


def parameters_comparison_whittaker(conn, poly_id, index):


    graph_data = api_get_timeseries(conn, poly_id, index)

    if len(graph_data) == 0:
        raise Exception("No timeseries data for this polygon feature in database")


    out_savgol_y1 = whittaker_smooth(np.asarray([i[-1] for i in graph_data]), 0.2, 2)
    out_savgol_y2 = whittaker_smooth(np.asarray([i[-1] for i in graph_data]), 0.5, 2)
    out_savgol_y3 = whittaker_smooth(np.asarray([i[-1] for i in graph_data]), 0.1, 2)
    out_savgol_y4 = whittaker_smooth(np.asarray([i[-1] for i in graph_data]), 0.2, 2)

    dates = [np.datetime64(i[0].split()[0], 'D') for i in graph_data]
    means = [i[1] for i in graph_data]

    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    yearsFmt = mdates.DateFormatter('%Y')
    monthsFmt = mdates.DateFormatter("%b")

    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111)


    ax.plot(dates, means, "-", color= "black", label=r"vrednosti indeksa")
    #ax.plot(dates, out_savgol_y, '-', color="green", label=r"$\alpha$ = 5%")
    ax.plot(dates, out_savgol_y2, "-", color= "red", label= r"$\lambda$ = 0.5")
    ax.plot(dates, out_savgol_y3, '-', color="blue", label=r"$\lambda$ = 1")
    ax.plot(dates, out_savgol_y4, "-", color="orange", label=r"$\lambda$ = 2")

    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.xaxis.set_minor_formatter(monthsFmt)

    ax.xaxis.set_tick_params(which='major', grid_linewidth=1.5, pad=15)

    datemin = np.datetime64(dates[0], 'D')
    datemax = np.datetime64(dates[-1], 'D')
    ax.set_xlim(str(datemin), str(datemax))

    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.format_ydata = graph_data[0]
    ax.grid(True, which="both")
    plt.title('Primerjava parametrov pri glajenju s Whittaker-Eilers filtrom.')
    plt.ylabel(index.upper())
    plt.xlabel('Datum')
    plt.legend()

    plt.savefig(f"./images/parameter_comparison_whittaker_{poly_id}.png")

def ndvi_comparison(conn, poly_id, index):


    ndvi_data = api_get_timeseries(conn, poly_id, "ndvi")
    # evi_data = api_get_timeseries(conn, poly_id, "evi")
    # evi2_data = api_get_timeseries(conn, poly_id, "evi2")

    if len(ndvi_data) == 0:
        raise Exception("No timeseries data for this polygon feature in database")


    out_savgol_y1 = savgol_fit_mean(ndvi_data, 0.2, 2)
    # out_savgol_y2 = savgol_fit_mean(evi_data, 0.5, 2)
    # out_savgol_y3 = savgol_fit_mean(evi2_data, 0.1, 2)

    dates = [np.datetime64(i[0].split()[0], 'D') for i in ndvi_data]
    means = [i[1] for i in ndvi_data]

    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    yearsFmt = mdates.DateFormatter('%Y')
    monthsFmt = mdates.DateFormatter("%b")

    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111)


    ax.plot(dates, means, "-", color= "black", label=r"vrednosti indeksa")
    #ax.plot(dates, out_savgol_y, '-', color="green", label=r"$\alpha$ = 5%")
    ax.plot(dates, out_savgol_y1, "-", color= "red", label= r"Savitzky-Golay")


    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.xaxis.set_minor_formatter(monthsFmt)

    ax.xaxis.set_tick_params(which='major', grid_linewidth=1.5, pad=15)

    datemin = np.datetime64(dates[0], 'D')
    datemax = np.datetime64(dates[-1], 'D')
    ax.set_xlim(str(datemin), str(datemax))

    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.format_ydata = ndvi_data[0]
    ax.grid(True, which="both")
    plt.title('Primer NDVI indeksa.')
    plt.ylabel(index.upper())
    plt.xlabel('Datum')
    plt.legend()

    plt.savefig(f"./images/ndvi_{poly_id}.png")


def evi2_comparison(conn, poly_id, index):


    ndvi_data = api_get_timeseries(conn, poly_id, "evi2")
    # evi_data = api_get_timeseries(conn, poly_id, "evi")
    # evi2_data = api_get_timeseries(conn, poly_id, "evi2")

    if len(ndvi_data) == 0:
        raise Exception("No timeseries data for this polygon feature in database")


    out_savgol_y1 = savgol_fit_mean(ndvi_data, 0.2, 2)
    # out_savgol_y2 = savgol_fit_mean(evi_data, 0.5, 2)
    # out_savgol_y3 = savgol_fit_mean(evi2_data, 0.1, 2)

    dates = [np.datetime64(i[0].split()[0], 'D') for i in ndvi_data]
    means = [i[1] for i in ndvi_data]

    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    yearsFmt = mdates.DateFormatter('%Y')
    monthsFmt = mdates.DateFormatter("%b")

    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111)


    ax.plot(dates, means, "-", color= "black", label=r"vrednosti indeksa")
    #ax.plot(dates, out_savgol_y, '-', color="green", label=r"$\alpha$ = 5%")
    ax.plot(dates, out_savgol_y1, "-", color= "red", label= r"Savitzky-Golay")


    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.xaxis.set_minor_formatter(monthsFmt)

    ax.xaxis.set_tick_params(which='major', grid_linewidth=1.5, pad=15)

    datemin = np.datetime64(dates[0], 'D')
    datemax = np.datetime64(dates[-1], 'D')
    ax.set_xlim(str(datemin), str(datemax))

    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.format_ydata = ndvi_data[0]
    ax.grid(True, which="both")
    plt.title('Primer EVI2 indeksa.')
    plt.ylabel(index.upper())
    plt.xlabel('Datum')
    plt.legend()

    plt.savefig(f"./images/evi2_{poly_id}.png")


if __name__ == "__main__":
    conn = sqliteConnector(r"./dbs/samo_nesusni.sqlite")
    poly_id = 9246
    #parameters_comparison(conn, poly_id, "ndvi")
    #parameters_comparison_whittaker(conn, poly_id, "ndvi")
    #index_comparison(conn, poly_id, "ndvi")
    evi2_comparison(conn, poly_id, "evi2")