"""
Plots an XSPEC MCMC corner plot of the specified parameters.

Usage
---------
python plotMCMC.py <cwd> <filename> <par_map> <pars>

cwd: - Current working directory

---------

Author - Thomas Hodd

Date - 3rd July 2025

Version - 1.0
"""
import os
import numpy as np
import argparse
from astropy.io import fits
from matplotlib import pyplot as plt
import corner
from datetime import datetime as dt

parser = argparse.ArgumentParser(description="Plots a corner plot for an XSPEC MCMC chain")
parser.add_argument("cwd", type=str, help="Current working directory")
parser.add_argument("filename", type=str, help="File name")
parser.add_argument("par_map", type=str, help="Map of free parameters")
parser.add_argument("pars", type=str, nargs='+', help="Parameters to include in plot")

args = parser.parse_args()
cwd = args.cwd
filename = args.filename
par_map_str = args.par_map
pars_str = args.pars

# List of requested parameters, selected free parameter numbers, and map of free params from XSPEC
pars, f_pars, par_map = [], [], []

# Split the string input param map into a list
for p in par_map_str.split():
    par_map.append(p)

# Create a list of integers from the input params
for par in pars_str:
    try:
        pars.append(int(par))
    except ValueError:
        mini = int(par.split("-")[0])
        maxi = int(par.split("-")[1])
        for i in range(mini, maxi + 1):
            pars.append(i)

# Convert requested param numbers to list of free param numbers
for p in pars:
    if par_map[p-1] == "N":
        pass
        # print(f"Parameter {p} is not a free parameter!")
    else:
        print(f"Selected free parameter {par_map[p-1]} ({p})")
        f_pars.append(int(par_map[p-1]))

# Organise data
table = fits.open(cwd + "/" + filename)[1]
par_names = [n.name for n in table.columns]
par_vals = [table.data[name] for name in par_names]

# Plot
corner.corner(
    data = np.array([par_vals[i-1] for i in f_pars]).T,
    labels = [f"{par_names[num-1].split("__")[0]} ({par_names[num-1].split("__")[1]})[{num}]" for num in f_pars],
    quantiles=[0.16, 0.5, 0.84],
    show_titles=True,
    title_kwargs={"fontsize": 10},
)

# Save figure
try:
    plt.savefig(f"{cwd}/MCMCPlots/corner_{filename}_{dt.now().strftime("%Y-%m-%d-%H-%M-%S")}.jpg", dpi=300)
except FileNotFoundError:
    print("Making new directory")
    os.mkdir("MCMCPlots/")
    plt.savefig(f"{cwd}/MCMCPlots/corner_{filename}_{dt.now().strftime("%Y-%m-%d-%H-%M-%S")}.jpg", dpi=300)
