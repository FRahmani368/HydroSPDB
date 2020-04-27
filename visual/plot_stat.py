"""使用seaborn库绘制各类统计相关的图形"""
import matplotlib
import seaborn as sns
import matplotlib.pyplot as plt
import geopandas as gpd
import geoplot as gplt
import geoplot.crs as gcrs
import numpy as np
import pandas as pd
import cartopy.crs as ccrs
from cartopy.feature import NaturalEarthFeature
from matplotlib import gridspec

from explore.stat import ecdf
from utils.hydro_math import flat_data


def plot_boxs(data, x_name, y_name):
    """绘制箱型图"""
    sns.set(style="ticks", palette="pastel")

    # Draw a nested boxplot to show bills by day and time
    sns_box = sns.boxplot(x=x_name, y=y_name, data=data, showfliers=False)
    sns.despine(offset=10, trim=True)
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=45)
    plt.show()
    return sns_box.get_figure()


def plot_diff_boxes(data, row_and_col=None, y_col=None, x_col=None):
    """绘制箱型图 in one row and different cols"""
    if type(data) != pd.DataFrame:
        data = pd.DataFrame(data)
    if y_col is None:
        subplot_num = data.shape[1]
    else:
        subplot_num = len(y_col)
    if row_and_col is None:
        row_num = 1
        col_num = subplot_num
        f, axes = plt.subplots(row_num, col_num)
    else:
        assert subplot_num <= row_and_col[0] * row_and_col[1]
        row_num = row_and_col[0]
        col_num = row_and_col[1]
        f, axes = plt.subplots(row_num, col_num)
    for i in range(subplot_num):
        if y_col is None:
            if row_num == 1 or col_num == 1:
                sns.boxplot(y=data.columns.values[i], data=data, orient='v', ax=axes[i], showfliers=False)
            else:
                row_idx = int(i / col_num)
                col_idx = i % col_num
                sns.boxplot(y=data.columns.values[i], data=data, orient='v', ax=axes[row_idx, col_idx],
                            showfliers=False)
        else:
            assert x_col is not None
            if row_num == 1 or col_num == 1:
                sns.boxplot(x=data.columns.values[x_col], y=data.columns.values[y_col[i]], data=data, orient='v',
                            ax=axes[i], showfliers=False)
            else:
                row_idx = int(i / col_num)
                col_idx = i % col_num
                sns.boxplot(x=data.columns.values[x_col], y=data.columns.values[y_col[i]],
                            data=data, orient='v', ax=axes[row_idx, col_idx], showfliers=False)
    plt.show()
    return f


def plot_ts(data, row_name, col_name, x_name, y_name):
    """绘制时间序列对比图"""
    sns.set(style="whitegrid")
    g = sns.FacetGrid(data, row=row_name, col=col_name, margin_titles=True)
    g.map(plt.plot, x_name, y_name, color="steelblue")

    plt.show()
    return g


def plot_point_map(gpd_gdf, percentile=0, save_file=None):
    """plot point data on a map"""
    # Choose points in which NSE value are bigger than the 25% quartile value range
    percentile_data = np.percentile(gpd_gdf['NSE'].values, percentile).astype(float)
    # the result of query is a tuple with one element, but it's right for plotting
    data_chosen = gpd_gdf.query("NSE > " + str(percentile_data))
    contiguous_usa = gpd.read_file(gplt.datasets.get_path('contiguous_usa'))
    proj = gcrs.AlbersEqualArea(central_longitude=-98, central_latitude=39.5)
    polyplot_kwargs = {'facecolor': (0.9, 0.9, 0.9), 'linewidth': 0}
    pointplot_kwargs = {'hue': 'NSE', 'legend': True, 'linewidth': 0.01}
    # ax = gplt.polyplot(contiguous_usa.geometry, projection=proj, **polyplot_kwargs)
    ax = gplt.webmap(contiguous_usa, projection=gcrs.WebMercator())
    gplt.pointplot(data_chosen, ax=ax, **pointplot_kwargs)
    ax.set_title("NSE " + "Map")
    plt.show()
    if save_file is not None:
        plt.savefig(save_file)
        # plt.savefig("NSE-usa.png", bbox_inches='tight', pad_inches=0.1)


def plot_ecdfs(xs, y, legends=None):
    """Empirical cumulative distribution function"""
    assert type(xs) == list
    assert (all(xi < yi for xi, yi in zip(y, y[1:])))
    frames = []
    for i in range(len(xs)):
        df_dict_i = {}
        if legends is None:
            str_i = "x" + str(i)
        else:
            str_i = legends[i]
        assert (all(xi < yi for xi, yi in zip(xs[i], xs[i][1:])))
        df_dict_i["x"] = xs[i]
        df_dict_i["y"] = y
        df_dict_i["case"] = np.full([xs[i].size], str_i)
        df_i = pd.DataFrame(df_dict_i)
        frames.append(df_i)
    df = pd.concat(frames)
    sns.set_style("ticks", {'axes.grid': True})
    sns.lineplot(x="x", y="y", hue="case", data=df, estimator=None).set(xlim=(0, 1), xticks=np.arange(0, 1, 0.05),
                                                                        yticks=np.arange(0, 1, 0.05))
    plt.show()


def plot_ecdf(mydataframe, mycolumn, save_file=None):
    """Empirical cumulative distribution function"""
    x, y = ecdf(mydataframe[mycolumn])
    df = pd.DataFrame({"x": x, "y": y})
    sns.set_style("ticks", {'axes.grid': True})
    sns.lineplot(x="x", y="y", data=df, estimator=None).set(xlim=(0, 1), xticks=np.arange(0, 1, 0.05),
                                                            yticks=np.arange(0, 1, 0.05))
    plt.show()
    if save_file is not None:
        plt.savefig(save_file)


def plot_pdf_cdf(mydataframe, mycolumn):
    # settings
    f, axes = plt.subplots(1, 2, figsize=(18, 6), dpi=320)
    axes[0].set_ylabel('fraction (PDF)')
    axes[1].set_ylabel('fraction (CDF)')

    # left plot (PDF) # REMEMBER TO CHANGE bins, xlim PROPERLY!!
    sns.distplot(
        mydataframe[mycolumn], kde=True, axlabel=mycolumn,
        hist_kws={"density": True}, ax=axes[0]
    ).set(xlim=(0, 1))

    # right plot (CDF) # REMEMBER TO CHANGE bins, xlim PROPERLY!!
    sns.distplot(
        mydataframe[mycolumn], kde=False, axlabel=mycolumn,
        hist_kws={"density": True, "cumulative": True, "histtype": "step", "linewidth": 4}, ax=axes[1],
    ).set(xlim=(0, 1), ylim=(0, 1))
    plt.show()


def plot_loss_early_stop(train_loss, valid_loss):
    # visualize the loss as the network trained
    fig = plt.figure(figsize=(10, 8))
    plt.plot(range(1, len(train_loss) + 1), train_loss, label='Training Loss')
    plt.plot(range(1, len(valid_loss) + 1), valid_loss, label='Validation Loss')

    # find position of lowest validation loss
    minposs = valid_loss.index(min(valid_loss)) + 1
    plt.axvline(minposs, linestyle='--', color='r', label='Early Stopping Checkpoint')
    max_loss = max(np.amax(np.array(train_loss)), np.amax(np.array(valid_loss)))
    plt.xlabel('epochs')
    plt.ylabel('loss')
    plt.ylim(0, max_loss + 0.05)  # consistent scale
    plt.xlim(0, len(train_loss) + 1)  # consistent scale
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
    return fig


def plot_map_carto(data, lat, lon, ax=None, pertile_range=None):
    temp = data
    if pertile_range is None:
        vmin = np.amin(temp)
        vmax = np.amax(temp)
    else:
        assert 0 <= pertile_range[0] < pertile_range[1] <= 100
        vmin = np.percentile(temp, pertile_range[0])
        vmax = np.percentile(temp, pertile_range[1])
    llcrnrlat = np.min(lat),
    urcrnrlat = np.max(lat),
    llcrnrlon = np.min(lon),
    urcrnrlon = np.max(lon),
    extent = [llcrnrlon[0], urcrnrlon[0], llcrnrlat[0], urcrnrlat[0]]
    # Figure
    if ax is None:
        fig = plt.figure()
        ax = fig.subplots(projection=ccrs.PlateCarree())
    ax.set_extent(extent)
    states = NaturalEarthFeature(category="cultural", scale="50m",
                                 facecolor="none",
                                 name="admin_1_states_provinces_shp")
    ax.add_feature(states, linewidth=.5, edgecolor="black")
    ax.coastlines('50m', linewidth=0.8)
    # auto projection
    scat = plt.scatter(lon, lat, c=temp, s=10, cmap='viridis', vmin=vmin, vmax=vmax)
    plt.colorbar()
    return scat, ax


def plot_ts_matplot(t, y, color='r', ax=None, title=None):
    assert type(t) == list
    assert type(y) == list
    if ax is None:
        fig = plt.figure()
        ax = fig.subplots()
    ax.plot(t, y[0], color=color, label='pred')
    ax.plot(t, y[1], label='obs')
    ax.legend()
    if title is not None:
        ax.set_title(title, loc='center')
    if ax is None:
        return fig, ax
    else:
        return ax


def plot_ts_map(dataMap, dataTs, lat, lon, t, sites_id, pertile_range=None):
    # show the map in a pop-up window
    matplotlib.use('TkAgg')
    assert type(dataMap) == list
    assert type(dataTs) == list
    # setup axes
    fig = plt.figure(figsize=(8, 8), dpi=100)
    gs = gridspec.GridSpec(2, 1)
    # plt.subplots_adjust(left=0.13, right=0.89, bottom=0.05)
    # plot maps
    ax1 = plt.subplot(gs[0], projection=ccrs.PlateCarree())
    scat, ax1 = plot_map_carto(dataMap, lat=lat, lon=lon, ax=ax1, pertile_range=pertile_range)
    # line plot
    ax2 = plt.subplot(gs[1])

    # plot ts
    def onclick(event):
        print("click event")
        # refresh the ax2, then new ts data can be showed without previous one
        ax2.cla()
        xClick = event.xdata
        yClick = event.ydata
        d = np.sqrt((xClick - lon) ** 2 + (yClick - lat) ** 2)
        ind = np.argmin(d)
        titleStr = 'site_id %s, lat %.3f, lon %.3f' % (sites_id[ind], lat[ind], lon[ind])
        tsLst = dataTs[ind]
        plot_ts_matplot(t, tsLst, ax=ax2, title=titleStr)
        # following funcs both work
        fig.canvas.draw()
        # plt.draw()

    fig.canvas.mpl_connect('button_press_event', onclick)
    plt.show()
