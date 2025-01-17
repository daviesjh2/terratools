"""
This submodule contains internal functions for performing
plotting of TerraModels and other classes in terratools.
"""

_CARTOPY_INSTALLED = True
_CARTOPY_NOT_INSTALLED_EXCEPTION = None

try:
    import cartopy.crs as ccrs
except ImportError as exception:
    _CARTOPY_INSTALLED = False
    _CARTOPY_NOT_INSTALLED_EXCEPTION = exception

import matplotlib.pyplot as plt
import numpy as np
import os
import scipy.interpolate
import scipy.stats
import sys


def layer_grid(
    lon,
    lat,
    radius,
    values,
    delta=None,
    extent=(-180, 180, -90, 90),
    label=None,
    method="nearest",
    coastlines=True,
    **subplots_kwargs,
):
    """
    Take a set of arbitrary points in longitude and latitude, each
    with a different value, and create a grid of these values, which
    is then plotted on a map.

    :param lon: Set of longitudes in degrees
    :param lat: Set of latitudes in degrees
    :param radius: Radius of layer in km
    :param values: Set of the values taken at each point
    :param delta: Grid spacing in degrees
    :param extent: Tuple giving min longitude, max longitude, min latitude
        and max latitude (all in degrees), defining the region to plot
    :param label: Label for values; e.g. "Temperature / K"
    :param method: Can be one of:
        * "nearest": nearest neighbour only;
        * "mean": mean of all values within each grid point
    :param coastlines: If ``True`` (the default) use cartopy
        to plot coastlines.  Otherwise, do not plot coastlines.
        This works around an issue with Cartopy when
        installed in certain situations.  See
        https://github.com/SciTools/cartopy/issues/879 for details.
    :param **kwargs: Extra keyword arguments passed to
        `matplotlib.pyplot.subplots`
    :returns: tuple of figure and axis handles, respectively
    """
    if not _CARTOPY_INSTALLED:
        sys.stderr.write("layer_grid require cartopy to be installed")
        raise _CARTOPY_NOT_INSTALLED_EXCEPTION

    fig, ax = plt.subplots(
        subplot_kw={"projection": ccrs.EqualEarth(), **subplots_kwargs}
    )

    if len(extent) != 4:
        raise ValueError("extent must contain four values")
    elif extent[1] <= extent[0]:
        raise ValueError(
            "maximum longitude must be more than minimum; have"
            + f"min = {extent[0]} and max = {extent[1]}"
        )
    elif extent[3] <= extent[2]:
        raise ValueError(
            "maximum latitude must be more than minimum; have"
            + f"min = {extent[2]} and max = {extent[3]}"
        )

    minlon, maxlon, minlat, maxlat = extent

    if delta is None:
        lonrange = maxlon - minlon
        latrange = maxlat - minlat
        max_range = max(lonrange, latrange)
        delta = max_range / 200
    elif delta <= 0:
        raise ValueError("delta must be more than 0")

    grid_lons = np.arange(minlon, maxlon, delta)
    grid_lats = np.arange(minlat, maxlat, delta)
    grid_lon, grid_lat = np.meshgrid(grid_lons, grid_lats)

    if method == "nearest":
        grid = scipy.interpolate.griddata(
            (lon, lat), values, (grid_lon, grid_lat), method="nearest"
        )
    elif method == "mean":
        grid, _, _, _ = scipy.stats.binned_statistic_2d(
            lon, lat, values, bins=[grid_lons, grid_lats]
        )
        grid = np.transpose(grid)
    else:
        raise ValueError(f"unsupported method '{method}'")

    grid = np.flip(grid, axis=0)

    transform = ccrs.PlateCarree()

    contours = ax.imshow(grid, transform=transform, extent=extent)
    ax.set_title(f"Radius {int(radius)} km")
    ax.set_xlabel(f"{label}", fontsize=12)

    cbar = plt.colorbar(
        contours,
        ax=ax,
        orientation="horizontal",
        pad=0.05,
        aspect=30,
        shrink=0.5,
        label=(label if label is not None else ""),
    )

    # This leads to a segfault on machines where cartopy is not installed
    # from conda-forge, or where it was not built from source:
    # https://github.com/SciTools/cartopy/issues/879
    if coastlines:
        ax.coastlines()

    return fig, ax


def spectral_heterogeneity(
    indat,
    title,
    depths,
    lmin,
    lmax,
    saveplot,
    savepath,
    lyrmin,
    lyrmax,
    **subplots_kwargs,
):
    """
    Creates a contour plot from the power spectrum over depth
    :param indat: array containing power spectrum at each radial layer.
        shape (nr,lmax+1)
    :param depths: array containing depths corresponding to power spectra
    :param lmin: minimum spherical harmonic degree to plot
    :param lmax: maximum spherical harmonic degree to plot
    :param saveplot: flag to save figure
    :param saveplot: path under which to save figure
    :param lyrmin: minimum layer to plot
    :param lyrmax: maximum layer to plot
    :param **subplot_kwargs: Extra keyword arguments passed to
            `matplotlib.pyplot.subplots`
    :returns: tuple of figure and axis handles, respectively
    """

    logged = np.log(indat[lyrmin:lyrmax, lmin : lmax + 1])
    deps = depths[lyrmin:lyrmax]

    fig, ax = plt.subplots(figsize=(8, 6), **subplots_kwargs)

    plotmin = np.min(logged)
    plotmax = np.max(logged)
    levels = np.linspace(plotmin, plotmax, 10)
    cs = ax.contourf(np.arange(lmin, lmax + 1), deps, logged, levels=levels)
    ax.set_ylabel("Depth (km)", fontsize=12)
    ax.set_xlabel("L", fontsize=12)
    ax.set_xlim(lmin - 1, lmax + 1)
    if title == None:
        ax.set_title(f"Spherical Harmonic Power Spectrum")
    else:
        ax.set_title(f"Spherical Harmonic Power Spectrum \n for {title} field")
    plt.gca().invert_yaxis()
    cbar = fig.colorbar(cs, ax=ax, shrink=0.9, orientation="horizontal", pad=0.1)
    cbar.set_label("ln(Power)", fontsize=12)

    if saveplot:
        if savepath == None:
            savepath = "."
        if title == None:
            title = ""
        plt.savefig(
            f"{savepath}/powers_{title}.pdf", format="pdf", dpi=200, bbox_inches="tight"
        )

    return fig, ax


# def plot_hp_layer
