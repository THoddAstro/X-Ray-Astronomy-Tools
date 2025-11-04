"""
Identifies low and high phases by flux and writes them to a txt file for conversion
into a GTI file.

Usage
---------
python fluxResolve.py <FileName> <Start> <End> <significance> <BinSize>

FileName: - Light curve file

Start - Region of interest start in mission time

End - Region of interest end in mission time

Significance - Number of counts away from mean required for phase detection

BinSize - Light curve bin size in seconds

Options
---------
-b --build - Automatically build GTI files, then remove .txt files (Requires SAS)

---------

Author - Thomas Hodd

Date - 2nd May 2025

Version - 1.0
"""
import argparse
import os
import subprocess
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import patches, ticker
from pylag import LightCurve

cwd = os.getcwd()

# Input args
parser = argparse.ArgumentParser(description="Flux-resolved GTI finder.")
parser.add_argument("filename", type=str, help="Light curve file")
parser.add_argument("start", type=float, help="Region of interest start in mission time")
parser.add_argument("end", type=float, help="Region of interest end in mission time")
parser.add_argument("significance", type=float, nargs='?', default=0.5, help="Counts from mean required for phase detection (optional)")
parser.add_argument("binsize", type=int,   nargs='?', default=200, help="Bin size in seconds (optional)")
parser.add_argument("-b", "--build", action='store_true', help="Automatically build GTI files, then remove .txt files (Requires SAS)")

# Parse args
args = parser.parse_args()
filename = args.filename
start = args.start
end = args.end
sig = args.significance
binsize = args.binsize
build = args.build

# Open the light curve file
lc:  LightCurve = LightCurve(filename).rebin(binsize)

# Create an LC for the ROI
mask = (start < lc.time) & (lc.time <= end)
roi = LightCurve(t=lc.time[mask], r=lc.rate[mask], e=lc.error[mask])

# Get arrays of time and rate
times = roi.time
rates = roi.rate

# Determine the mean count rate
mean = np.mean(rates)
min_length = 3000

# Define initial values for GTI identification
prior_rate = rates[0]
gti_points = [[times[0], "High"]]

# Find low and high phases
print("Identifying phases...")
for rate, time in zip(rates[1:], times[1:]):
    if rate > mean + sig >= prior_rate and gti_points[-1][1] != "High":
        gti_points.append([time, "High"])
    if rate < mean - sig <= prior_rate and gti_points[-1][1] != "Low":
        gti_points.append([time, "Low"])

    prior_rate = rate

# Remove short phases
for i, point in enumerate(gti_points):
    if i % 2 != 0 and i != len(gti_points) - 1:
        length = gti_points[i+1][0] - point[0]
        if length < min_length:
            gti_points.pop(i)
            gti_points.pop(i)
            print(f"Removed misidentified phase ({int(length)}s) @ {str(round(point[0]))[3:]}s")
print(f"Found {len(gti_points)-1} GTIs")

# Write GTI text files
print("Writing GTIs to files...")
for phase in ["High", "Low"]:
    with open(f"gti_{phase}.txt", "w") as f:
        for i, point in enumerate(gti_points[:-1]):
            if point[1] == phase:
                print(f"{point[1]} GTI @ {str(round(point[0]))[3:]} - {str(round(gti_points[i+1][0]))[3:]}")
                f.write(f"{round(point[0])} {round(gti_points[i+1][0])} +\n")
print(f"GTIs Completed")

# Plot results
fig = plt.figure(figsize=(10, 6))
plt.scatter(lc.time, lc.rate, marker="+", s=20, color="k")
plt.axhline(y=mean, linestyle="--", color="k")

# Phase GTIs
for i, point in enumerate(gti_points[:-1]):
    if point[1] == "Low":
        colour="r"
    else:
        colour="g"
    plt.fill_betweenx(y=[lc.rate.min(), lc.rate.max()], x1=point[0], x2=gti_points[i+1][0], color=colour, alpha=0.4)

# Legend
high_patch = patches.Patch(color="g", alpha=0.4, label="High Phase")
low_patch = patches.Patch(color="r", alpha=0.4, label="Low Phase")
plt.legend(handles=[high_patch, low_patch])

# Axes labels
ax = plt.gca()
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):d}"[3:]))
plt.xlabel(f"Truncated Mission Time [{str(int(min(lc.time)))[:3]}] (s)")
plt.ylabel("Rate (counts/s)")
plt.title(f"Flux GTIs for {filename}", fontweight="bold")

# Show and save plot
plt.savefig(f"{cwd}/gti_fluxes.png", dpi=300, bbox_inches="tight")
plt.show()

if build:
    # Run gtibuild on both High and Low phase GTIs
    subprocess.run("gtibuild file=gti_High.txt table=gti_High.fits", shell=True)
    subprocess.run("gtibuild file=gti_Low.txt table=gti_Low.fits", shell=True)

    # Remove .txt files
    os.remove("gti_High.txt")
    os.remove("gti_Low.txt")
