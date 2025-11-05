"""
Cut light curves down to size between two points in time

Reads the given file and cuts all light curves in cwd down to the size specified.
File should have the format:
<StartTime>, <EndTime>

Usage
---------
python LightCurveCut.py <FileName>

FileName: - Name of text file with start and end times

Suffix: - Suffix of cut light curves (optional)

---------

Author: Thomas Hodd

Date - 6th August 2025

Version - 1.0
"""
import os
import argparse
from pylag import LightCurve as LC

# Input args
parser = argparse.ArgumentParser(description="Cut light curve down to size")
parser.add_argument("filename", type=str, help="Name of text file with start and end times")
parser.add_argument("suffix", type=str, nargs="?", default="_cut", help="Suffix of cut light curves (optional)")

# Parse args
pargs = parser.parse_args()
filename = pargs.filename
suffix = pargs.suffix

# Get start and end times
with open(filename, "r") as f:
    start, stop = f.read().split(",")

# Create light curves between start and end times
for file in os.listdir():
    if file.endswith(".fits"):
        lc = LC(file)
        print(f"\nFound LC: {file}\n{round(lc.time[0])} - {round(lc.time[-1])}")
        mask = (float(start) < lc.time) & (lc.time < float(stop))

        lc.time = lc.time[mask]
        lc.rate = lc.rate[mask]
        lc.error = lc.error[mask]

        lc.write_fits(f"{file[:-5]}{suffix}.fits")
        print(f"Written LC: {file[:-5]}{suffix}.fits\n{round(lc.time[0])} - {round(lc.time[-1])}")