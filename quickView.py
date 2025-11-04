"""
Quickly plots a light curve.

Usage
---------
python quickView.py <FileName> <BinSize>

FileName: - Light curve file

BinSize - Light curve bin size in seconds (Optional, default 100)

Options
---------
-s --save - Save plot to image

-x --extra - Add additional light curves to plot

-m --mean - Show mean/median statistics

-t --stdev - Show the standard deviation statistics

-d --xmmdata - Load XMM light curves: lc, bg, lccor. Give only the prefix as <FileName>

-e --energy - Specify the energy range of XMM light curves, defaults to 0.3-10keV

-a --all - Plot all light curves in directory

---------

Author - Thomas Hodd

Date - 21st August 2025

Version - 1.2
"""
import argparse
import os
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import ticker
from pylag import LightCurve

cwd = os.getcwd()
COLOURS = ["dodgerblue", "orangered", "forestgreen", "deeppink", "darkturquoise", "orange",
           "darkorchid", "lawngreen", "mediumblue", "violet", "black", "grey", "peru"]
LAYOUT = {1 : (1, 1),
          2 : (1, 2),
          3 : (1, 3),
          4 : (4, 1),
          5 : (5, 1)}
SIZE = {1 : (10, 6),
        2 : (16, 7),
        3 : (18, 7),
        4 : (12, 12),
        5 : (12, 12)}

# Input args
parser = argparse.ArgumentParser(description="Quickly view light curves.")
parser.add_argument("filename", type=str, help="Light curve file")
parser.add_argument("binsize", type=int, nargs="?", default=100, help="Bin size in seconds (optional)")
parser.add_argument("-s", "--save", action="store_true", help="Save plot to image")
parser.add_argument("-x", "--extra", nargs="+", default=[], help="Add additional light curves to plot")
parser.add_argument("-m", "--mean", action="store_true", help="Show mean/median statistics")
parser.add_argument("-t", "--stdev", action="store_true", help="Show standard deviation statistics")
parser.add_argument("-d", "--xmmdata", action="store_true", help="Load XMM light curves")
parser.add_argument("-e", "--energy", nargs="+", default=["0.3", "10"], help="Specify energy range of XMM light curves")
parser.add_argument("-a", "--all", action="store_true", help="Plot all light curves in directory")

# Parse args
args = parser.parse_args()
filename = args.filename
binsize = args.binsize
save = args.save
extra = args.extra
mean_stats = args.mean
std_stats = args.stdev
xmm_data = args.xmmdata
energy = args.energy
all_lc = args.all

energy = [int(float(i) * 1000) for i in energy]

if xmm_data:
    # Load XMM data
    all_lcs = [LightCurve(f"{filename}_lc_raw_{energy[0]}-{energy[1]}.fits").rebin(binsize),
               LightCurve(f"{filename}_bg_raw_{energy[0]}-{energy[1]}.fits").rebin(binsize),
               LightCurve(f"{filename}_lccor_{energy[0]}-{energy[1]}.fits").rebin(binsize)]
    windows = [[all_lcs[0].time[0], all_lcs[0].time[-1]]]
    window_map = [0, 0, 0]
    if extra:
        print("Extra light curves ignored - not compatible with XMM data!")

else:
    if all_lc:
        all_lcs = []
        for f in os.listdir(cwd):
            all_lcs.append(LightCurve(f"{cwd}/{f}").rebin(binsize))
        COLOURS = [None] * len(all_lcs)
    else:
        # Open the light curve file
        lc:  LightCurve = LightCurve(filename).rebin(binsize)
        lc.filename = filename

        # Add additional light curves
        extra_lcs = []
        if extra:
            for l in extra:
                extra_lcs.append(LightCurve(l).rebin(binsize))

        for l, name in zip(extra_lcs, extra):
            l.filename = name

        # Determine number of subplots
        all_lcs = extra_lcs.copy()
        all_lcs.append(lc)

    all_lcs.sort(key=lambda x: x.time[0])
    windows = [[all_lcs[0].time[0], all_lcs[0].time[-1]]]
    window_map = [0]
    for l in all_lcs[1:]:
        for i, w in enumerate(windows):
            if l.time[0] >= w[0] and l.time[-1] <= w[1]:
                window_map.append(i)
                break
            if i == len(windows) - 1:
                windows.append([l.time[0], l.time[-1]])
                window_map.append(i+1)
                break

# Create Figure
fig, ax = plt.subplots(*LAYOUT[len(windows)], figsize=SIZE[len(windows)], label=f"QuickView - {filename}")

# Ensure the Axes is subscriptable
if len(windows) == 1:
    ax = [ax, None]

# Plot light curves
plot_set = [False] * len(windows)
plot_list = []
for i, l in enumerate(all_lcs):
    plot = window_map[i]
    plot_list.append(ax[plot].scatter(l.time, l.rate, marker="+", s=20, color=COLOURS[i]))
    if mean_stats:
        mean = np.mean(l.rate)
        median = np.median(l.rate)
        ax[plot].axhline(y=mean, linestyle="--", color=COLOURS[i], label=f"Mean ({round(mean, 2)})")
        ax[plot].axhline(y=median, linestyle=":", color=COLOURS[i], label=f"Median ({round(median, 2)})")
        ax[plot].legend()

    if std_stats:
        ax[plot].text(l.time[0] - 5000, -1.3 * i - 3, f"Standard Deviation: {round(np.std(l.rate), 3)}", color=COLOURS[i])

    # Axes
    if not plot_set[plot]:
        ax[plot].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):d}"[3:]))
        ax[plot].set_xlim(l.time[0] - 5000, l.time[-1] + 5000)
        ax[plot].set_ylabel("Rate (counts/s)")
        ax[plot].set_xlabel(f"Truncated Mission Time [{str(int(min(l.time)))[:3]}] (s)")

        ax2 = ax[plot].twiny()
        ax2.set_xlim([0 - 5, (l.time[-1] - l.time[0]) * 1E-3 + 5])
        ax2.set_xlabel("Time (ks)")
        plot_set[plot] = True

        ax[plot].set_title(f"{l.filename}", fontweight="bold")

    if xmm_data:
        ax[plot].set_title(f"{filename}_lccor_raw_{energy[0]}-{energy[1]}.fits", fontweight="bold")

if xmm_data and not mean_stats:
    plt.legend([plot_list[0], plot_list[1], plot_list[2]], ["Raw", "Background", "Corrected"])

# Show and save plot
plt.tight_layout()
if save:
    plt.savefig(f"{cwd}/quick_view.png", dpi=300, bbox_inches="tight")
plt.show()
