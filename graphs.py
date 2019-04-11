import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from helpers import daterange_months
import sentinelhub
import os


def get_xticks(mindate, maxdate):
    return [date for date in daterange_months(mindate, maxdate)]


def mean_fit_graph(meaned_data, out_lowes, out_savgol, poly_id, index):
    dates = [np.datetime64(i[0].split()[0], 'D') for i in meaned_data]
    means = [i[1] for i in meaned_data]
    st_devs = [i[2] for i in meaned_data]

    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    yearsFmt = mdates.DateFormatter('%Y')
    monthsFmt = mdates.DateFormatter("%b")

    fig = plt.figure(figsize=(10, 4))
    ax = fig.add_subplot(111)

    ax.errorbar(dates, means, yerr=st_devs, color= "black", ecolor="lightgray", fmt='.-', capsize=1, label="Sredje vrednosti")
    ax.plot(dates, out_lowes, '.-.', color="green", label="LOESS filter")
    ax.plot(dates, out_savgol, '-.', color="orange", label = "Savitzky-Golay filter")

    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.xaxis.set_minor_formatter(monthsFmt)

    ax.xaxis.set_tick_params(which='major', grid_linewidth=1.5, pad=15)

    datemin = np.datetime64(dates[0], 'D')
    datemax = np.datetime64(dates[-1], 'D')
    ax.set_xlim(str(datemin), str(datemax))

    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.format_ydata = out_savgol[0]
    ax.grid(True, which="both")

    plt.title('Srednje vrednosti')
    plt.ylabel(index.upper())
    plt.xlabel('Datum')
    plt.legend()
    try:
        plt.savefig(f"./images/{poly_id}_{index}_mean.png")
    except:
        os.mkdir("./images/")
        plt.savefig(f"./images/{poly_id}_{index}_mean.png")


def median_fit_graph(data, out_lowes, out_savgol, poly_id, index):
    medians = [i[-1] for i in data]
    dates = [np.datetime64(i[0].split()[0], 'D') for i in data]

    years = mdates.YearLocator()  # every year
    months = mdates.MonthLocator()  # every month
    yearsFmt = mdates.DateFormatter('%Y')
    monthsFmt = mdates.DateFormatter("%b")

    fig = plt.figure(figsize=(10, 4))
    ax = fig.add_subplot(111)

    ax.plot(dates, medians, ".-", color="black", label="mediane")
    ax.plot(dates, out_lowes, '.-.', color="green", label="LOESS filter")
    ax.plot(dates, out_savgol, '-.', color="blue", label = "Savitzky-Golay filter")

    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)
    ax.xaxis.set_minor_formatter(monthsFmt)

    ax.xaxis.set_tick_params(which='major', grid_linewidth=1.5, pad=15)

    datemin = np.datetime64(dates[0], 'D')
    datemax = np.datetime64(dates[-1], 'D')
    ax.set_xlim(str(datemin), str(datemax))

    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
    ax.format_ydata = out_savgol[0]
    ax.grid(True, which="both")

    plt.title('Mediana')
    plt.ylabel(index.upper())
    plt.xlabel('Datum')
    plt.legend()
    try:
        plt.savefig(f"./images/{poly_id}_{index}_median.png")
    except:
        os.mkdir("./images/")
        plt.savefig(f"./images/{poly_id}_{index}_median.png")


def plot_bands(data, dates, cols=4, figsize=(15, 15)):
    """
    Utility to plot small "true color" previews.
    """
    width = data[-1].shape[1]
    height = data[-1].shape[0]

    rows = data.shape[0] // cols + (1 if data.shape[0] % cols else 0)
    fig, axs = plt.subplots(nrows=rows, ncols=cols, figsize=figsize)
    for index, ax in enumerate(axs.flatten()):
        if index < data.shape[0]:
            caption = '{}: {}'.format(index, dates[index].strftime('%Y-%m-%d'))
            ax.set_axis_off()
            ax.imshow(data[index] / 255., vmin=0.0, vmax=1.0)
            ax.text(0, -2, caption, fontsize=12, color='g')
        else:
            ax.set_axis_off()


def overlay_cloud_mask(image, mask=None, factor=1./255, figsize=(15, 15), fig=None):
    """
    Utility function for plotting RGB images with binary mask overlayed.
    """
    if fig == None:
        plt.figure(figsize=figsize)
    rgb = np.array(image)
    plt.imshow(rgb * factor)
    if mask is not None:
        cloud_image = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
        cloud_image[mask == 1] = np.asarray([255, 255, 0, 100], dtype=np.uint8)
        plt.imshow(cloud_image)


# def draw_mean_fit(graph_data, fited):
#     means= [i[5] for i in graph_data]
#     dates = [i[2].split()[0] for i in graph_data]
#
#     poly_fit = go.Scatter(
#         x=fited[1],
#         y=fited[0],
#
#         mode='lines+markers',
#         name="'polyfit 3'",
#
#     )
#
#     means_g = go.Scatter(
#         x=dates,
#         y=means,
#         name="Srednje vredn"
#     )
#     data = [means_g, poly_fit]
#
#     fig = go.Figure(data=data)
#     pio.write_image(fig, f".\\images\\test_1.png")
#
#
# def draw_min_max_mean(graph_data, fited, poly_id):
#     # init_notebook_mode()
#     minis, maxis, means, stdevs = [], [], [], []
#     dates = []
#     for epoch in graph_data:
#         mini, maxi, mean, stdev = epoch[3:]
#         dates.append(epoch[2].split()[0])
#         minis.append(mini), maxis.append(maxi)
#         means.append(mean), stdevs.append(stdev)
#
#     minis_g = go.Scatter(
#         x=dates,
#         y=minis,
#         name="Minimumi"
#     )
#
#     poly_fit = go.Scatter(
#         x=fited[0],
#         y=fited[1],
#
#         mode='lines+markers',
#         name="'polyfit 3'",
#         #text=["tweak line smoothness<br>with 'smoothing' in line object"],
#         #hoverinfo='text+name',
#
#     )
#
#     maxis_g = go.Scatter(
#         x=dates,
#         y=maxis,
#         xaxis='x2',
#         yaxis='y2',
#         name="Maksimumi"
#     )
#     means_g = go.Scatter(
#         x=dates,
#         y=means,
#         xaxis='x3',
#         yaxis='y3',
#         name="Srednje vredn"
#     )
#     stdev_g = go.Scatter(
#         x=dates,
#         y=stdevs,
#         xaxis='x4',
#         yaxis='y4',
#         name="Standardni odkloni"
#     )
#
#     data = [minis_g, maxis_g, means_g,poly_fit, stdev_g]
#     layout = go.Layout(
#         xaxis=dict(
#             domain=[0, 1],
#         ),
#         yaxis=dict(
#             domain=[0, 0.30],
#
#         ),
#         xaxis2=dict(
#             domain=[0, 1],
#             ticks="",
#             anchor="x2",
#             showticklabels=False
#         ),
#         xaxis3=dict(
#             domain=[0, 1],
#             anchor='y3',
#             ticks="",
#             showticklabels=False
#         ),
#         xaxis4=dict(
#             domain=[0, 1],
#             anchor='y4',
#             ticks="",
#             showticklabels=False
#         ),
#         yaxis2=dict(
#             domain=[0.33, 0.65],
#             anchor='x2',
#         ),
#         yaxis3=dict(
#             domain=[0.70, 1],
#             anchor= "y3"
#         ),
#     )
#     fig = go.Figure(data=data, layout=layout)
#     # fig = dict(data=data, layout=layout)
#     # iplot(fig, filename=f"travnik_{poly_id}")
#     pio.write_image(fig, f".\\images\\{poly_id}.png")
#
#
# def draw_graph(graph_data, fited, poly_id):
#     #init_notebook_mode()
#     minis, maxis, means, stdevs = [], [], [], []
#     dates = []
#     for epoch in graph_data:
#         mini, maxi, mean, stdev = epoch[3:]
#         dates.append(epoch[2].split()[0])
#         minis.append(mini), maxis.append(maxi)
#         means.append(mean), stdevs.append(stdev)
#
#     minis_g = go.Scatter(
#         x=dates,
#         y=minis,
#         name="Minimumi"
#     )
#     maxis_g = go.Scatter(
#         x=dates,
#         y=maxis,
#         xaxis='x2',
#         yaxis='y2',
#         name="Maksimumi"
#     )
#     means_g = go.Scatter(
#         x=dates,
#         y=means,
#         xaxis='x3',
#         yaxis='y3',
#         name="Srednje vredn"
#     )
#     stdev_g = go.Scatter(
#         x=dates,
#         y=stdevs,
#         xaxis='x4',
#         yaxis='y4',
#         name="Standardni odkloni"
#     )
#
#     data = [minis_g, maxis_g, means_g, stdev_g]
#     layout = go.Layout(
#         xaxis=dict(
#             domain=[0, 1],
#         ),
#         yaxis=dict(
#             domain=[0, 0.25],
#         ),
#         xaxis2=dict(
#             domain=[0, 1],
#             ticks="",
#             showticklabels=False
#         ),
#         xaxis3=dict(
#             domain=[0, 1],
#             anchor='y3',
#             ticks="",
#             showticklabels=False
#         ),
#         xaxis4=dict(
#             domain=[0, 1],
#             anchor='y4',
#             ticks="",
#             showticklabels=False
#         ),
#         yaxis2=dict(
#             domain=[0.25, 0.50],
#             anchor='x2',
#         ),
#         yaxis3=dict(
#             domain=[0.50, 0.75],
#
#         ),
#         yaxis4=dict(
#             domain=[0.75, 1],
#             anchor='x4'
#         )
#     )
#     fig = go.Figure(data=data, layout=layout)
#     #fig = dict(data=data, layout=layout)
#     #iplot(fig, filename=f"travnik_{poly_id}")
#     pio.write_image(fig, f".\\images\\{poly_id}.png")