import numpy as np
import statsmodels.nonparametric.smoothers_lowess as stmodels
import scipy.signal

from helpers import *



def list_fitted_n(polyfit, n):
    p3 = np.poly1d(polyfit)
    return [[p3(i) for i in range(n)], list(range(n))]


def lowess_fit_mean(graph_data, percent_data, iters):
    mean = np.asarray([i[1] for i in graph_data])
    dates = [i[0].split()[0] for i in graph_data]

    x = time_range_to_xaxis(dates)

    out_lowes = stmodels.lowess(mean, np.asarray(x), percent_data, iters, delta=0.0, is_sorted=True)
    o = out_lowes.tolist()

    return [i[0] for i in o], [i[1] for i in o]

def lowess_fit_median(graph_data, percent_data, iters):
    mean = np.asarray([i[-1] for i in graph_data])
    dates = [i[0].split()[0] for i in graph_data]

    x = time_range_to_xaxis(dates)

    out_lowes = stmodels.lowess(mean, np.asarray(x), percent_data, iters, delta=0.0, is_sorted=True)
    o = out_lowes.tolist()

    return [i[0] for i in o], [i[1] for i in o]


def savgol_fit_mean(graph_data, percent_data, degs):
    mean = np.asarray([i[1] for i in graph_data])
    window_in = round(len(mean) * percent_data)
    if window_in % 2 == 0:
        window_in += 1

    out_savgol = scipy.signal.savgol_filter(mean, window_in, degs)

    return out_savgol.tolist()

def savgol_fit_median(graph_data, percent_data, degs):

    median = np.asarray([i[-11] for i in graph_data])
    window_in = round(len(median) * percent_data)
    if window_in % 2 == 0:
        window_in += 1

    out_savgol = scipy.signal.savgol_filter(median, window_in, degs)

    return out_savgol.tolist()


if __name__ == "__main__":
    pass
