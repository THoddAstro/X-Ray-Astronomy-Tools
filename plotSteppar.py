"""
Plots an XSPEC steppar saved by the `stp` Tcl proc.

Usage
---------
python plotSteppar.py <cwd>

cwd: - Current working directory

---------

Author - Thomas Hodd

Date - 18th June 2025

Version - 1.0
"""
import os
import numpy as np
import argparse
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, SymLogNorm
from scipy.interpolate import griddata
from datetime import datetime as dt

cs_map = LinearSegmentedColormap.from_list("cstat", [(0.0, "dodgerblue"),(0.5, "w"),(1.0, "orangered")])

parser = argparse.ArgumentParser(description="Plots an XSPEC steppar saved by the `stp` Tcl proc.")
parser.add_argument("cwd", type=str, help="Current working directory - location of steppar .dat files")

args = parser.parse_args()
cwd = args.cwd

with open(f"{cwd}/steppar_cstat.dat", "r") as f:
    cstat = f.read()
    cstat = np.array([float(c) for c in cstat.split("  ")[:-1]])

with open(f"{cwd}/steppar_par1.dat", "r") as f:
    par1 = f.readlines()
    par1_name = par1[0].split("\n")[0]
    par1 = np.array([float(p) for p in par1[1].split("  ")[:-1]])

with open(f"{cwd}/steppar_par2.dat", "r") as f:
    par2 = f.readlines()
    par2_name = par2[0].split("\n")[0]
    if "!" in par2_name:
        print("Loaded 1D steppar")
        par2 = None
    else:
        print("Loaded 2D steppar")
        par2 = np.array([float(p) for p in par2[1].split("  ")[:-1]])

# 1D steppar plot
if par2 is None:
    plt.figure(label="Steppar Result")
    plt.plot(par1, cstat, c="k")
    # plt.axhline(0, color="b", ls="--")
    plt.xlabel(par1_name)
    plt.ylabel("C-Statistic")
    try:
        plt.savefig(f"{cwd}/StepparPlots/steppar{dt.now().strftime("%Y-%m-%d-%H-%M-%S")}.png", dpi=300)
    except FileNotFoundError:
        os.mkdir("StepparPlots/")
        plt.savefig(f"{cwd}/StepparPlots/steppar{dt.now().strftime("%Y-%m-%d-%H-%M-%S")}.png", dpi=300)
    plt.show()

# 2D steppar plot
else:
    # Determine number of steps in each parameter
    steps1 = len(np.unique(par1)) - 1
    steps2 = len(np.unique(par2)) - 1

    # Create grid
    xi = np.linspace(par1.min(), par1.max(), steps1)
    yi = np.linspace(par2.min(), par2.max(), steps2)
    xy_grid = np.meshgrid(xi, yi)
    z_grid = griddata(points=(par1, par2), values=cstat, xi=(xy_grid[0], xy_grid[1]), method="linear")

    # Plot mesh
    plt.figure(label="Steppar Result")
    plt.pcolormesh(xy_grid[0], xy_grid[1], z_grid, cmap="plasma_r", vmin=min(cstat), vmax=np.percentile(cstat, 50),
                   norm="linear") #SymLogNorm(linthresh=1, linscale=1.0, vmin=min(0.0, min(cstat)), vmax=max(0.0, max(cstat)), base=10, clip=False))
    # plt.scatter(x_value, y_value, c=dstat, cmap=hard_map, s=5, vmin=min(dstat), vmax=-min(dstat))
    # plt.scatter(x_value, y_value, c=dstat, cmap="jet", s=5, alpha=0.3, vmin=min(dstat), vmax=-min(dstat))

    # Colourbar
    # ticks = [-10000, -1000, -100, -10, -1, -0.1, 0.0, 0.1, 1, 10, 100, 1000, 10000]
    # ticks = [t for t in ticks if min(0.0, min(cstat)) <= t <= max(0.0, max(cstat))]
    cb = plt.colorbar(label=r"C-Statistic", extend="max")
    # cb.set_ticks(ticks)

    plt.xlabel(par1_name)
    plt.ylabel(par2_name)
    try:
        plt.savefig(f"{cwd}/StepparPlots/steppar{dt.now().strftime("%Y-%m-%d-%H-%M-%S")}.png", dpi=300)
    except FileNotFoundError:
        os.mkdir("StepparPlots/")
        plt.savefig(f"{cwd}/StepparPlots/steppar{dt.now().strftime("%Y-%m-%d-%H-%M-%S")}.png", dpi=300)
    plt.show()
