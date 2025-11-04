"""
Phase resolve a light curve and write to a txt file for conversion
into a GTI file.

Usage
---------
python phaseResolve.py <FileName> <Start> <End> <frequency> <phase> <BinSize>

FileName: - Light curve file

Start - Region of interest start in mission time

End - Region of interest end in mission time

Frequency - Frequency of interest

Phase - Light curve phase

Amplitude - Sinusoid amplitude (optional)

BinSize - Light curve bin size in seconds (optional)

Options
---------
-b --build - Automatically build GTI files, then remove .txt files (Requires SAS)

---------

Author - Thomas Hodd

Date - 13th May 2025

Version - 1.0
"""
import argparse
import os
import subprocess
import numpy as np
from scipy.optimize import minimize
from matplotlib import pyplot as plt
from matplotlib import patches, ticker
from pylag import LightCurve

cwd = os.getcwd()

# Input args
parser = argparse.ArgumentParser(description="Phase-resolved GTI finder.")
parser.add_argument("filename", type=str, help="Light curve file")
parser.add_argument("start", type=float, help="Region of interest start in mission time")
parser.add_argument("end", type=float, help="Region of interest end in mission time")
parser.add_argument("frequency", type=float, help="Frequency of interest")
parser.add_argument("phase", type=float, nargs='?', default=0.5, help="Phase")
parser.add_argument("amplitude", type=float, nargs='?', default=1.0, help="Sinusoid amplitude (optional)")
parser.add_argument("binsize", type=int, nargs='?', default=200, help="Bin size in seconds (optional)")
parser.add_argument("-b", "--build", action='store_true', help="Automatically build GTI files, then remove .txt files (Requires SAS)")

# Parse args
args = parser.parse_args()
filename = args.filename
start = args.start
end = args.end
freq = args.frequency
phase = args.phase
amp = args.amplitude
binsize = args.binsize
build = args.build

chis = []


def sin_model(lvl, a, f, p, t):
    if p > 1:
        return 0
    return a * np.sin(2 * np.pi * f * 1E-6 * t + p * 2 * np.pi) + lvl


def chi_squared(lvl: float, a: float, f: float, p: float, t: np.ndarray, y: np.ndarray, dy: np.ndarray) -> float:
    """
    Calculate chi-squared for our model of y position as a function of time.
    :param lvl: zero level of sinusoid
    :param a: amplitude
    :param f: frequency
    :param p: phase
    :param t: Time
    :param y: y position
    :param dy: y error
    :return: Chi-squared
    """
    y_fit = sin_model(lvl, a, f, p, t)
    chis.append(np.sum(((y - y_fit) / dy) ** 2, -1))
    return np.sum(((y - y_fit) / dy) ** 2, -1)


# Open the light curve file
lc:  LightCurve = LightCurve(filename).rebin(binsize)

# Create an LC for the ROI
mask = (start < lc.time) & (lc.time <= end)
roi = LightCurve(t=lc.time[mask], r=lc.rate[mask], e=lc.error[mask])

# Get arrays of time and rate
times = roi.time
rates = roi.rate
errors = roi.error

# Determine the mean count rate
mean = np.mean(rates)
level = mean
min_length = 3000

# Lambda function that calculates the sum of squares error
chi = lambda theta: chi_squared(theta[0], theta[1], theta[2], theta[3], t=times, y=rates, dy=errors)

# Initial guesses for params
theta_guess = np.array([level, amp, freq, phase])
bounds = [(level, level), (1., 3.), (10, 100), (0., 1.)]

# Do MLE
options = {'xtol': 1e-4, 'ftol': 1e-4, 'maxiter': 1E+6}
mle_estimate = minimize(chi, theta_guess, tol=1e-12, method="BFGS")
print(mle_estimate.values())
print(f"\nMLE Estimates:\nlevel = {round(mle_estimate.x[0], 3)}\namplitude = {round(mle_estimate.x[1], 4)}"
      f"\nfrequency = {round(mle_estimate.x[2], 3)}\nphase = {round(mle_estimate.x[3], 4)}")

# The inverse of the Hessian matrix is an estimate of the covariance matrix
cov_matrix = mle_estimate.hess_inv

# The standard errors are found from the sqrt of the diagonal elements of the covariance matrix
standard_errors = np.sqrt(np.diag(cov_matrix))

print(standard_errors)

plt.plot(chis)
plt.ylabel(r"$\chi^2$")
plt.xlabel(r"Iteration")
plt.yscale("log")

params = mle_estimate.x

# Define initial values for GTI identification
if sin_model(*params, times[0]) > mean:
    gti_points = [[times[0], "High"]]
elif sin_model(*params, times[0]) < mean:
    gti_points = [[times[0], "Low"]]
else:
    print("Initial point is neither high nor low!")
    exit()

# Find low and high phases
print("Identifying phases...")
for time in times[1:-1]:
    if sin_model(*params, time) > mean and gti_points[-1][1] != "High":
        gti_points.append([time, "High"])
    if  sin_model(*params, time) < mean and gti_points[-1][1] != "Low":
        gti_points.append([time, "Low"])

if sin_model(*params, times[-1]) > mean:
    gti_points.append([times[-1], "High"])
if  sin_model(*params, times[-1]) < mean:
    gti_points.append([times[-1], "Low"])

# Write GTI text files
print("Writing GTIs to files...")
for p in ["High", "Low"]:
    with open(f"gti_{p}.txt", "w") as f:
        for i, point in enumerate(gti_points[:-1]):
            if point[1] == p:
                print(f"{point[1]} GTI @ {str(round(point[0]))[3:]} - {str(round(gti_points[i+1][0]))[3:]}")
                f.write(f"{round(point[0])} {round(gti_points[i+1][0])} +\n")
print(f"GTIs Completed")

# Plot results
fig = plt.figure(figsize=(10, 6))
plt.scatter(lc.time, lc.rate, marker="+", s=20, color="k")
plt.plot(lc.time, sin_model(*params, lc.time), color="b")
plt.axhline(y=mean, linestyle="--", color="k")

# Phase GTIs
for i, point in enumerate(gti_points[:-1]):
    if point[1] == "Low":
        colour="r"
    else:
        colour="g"
    plt.fill_betweenx(y=[lc.rate.min(), lc.rate.max()], x1=point[0], x2=gti_points[i+1][0], color=colour, alpha=0.4)

plt.fill_between(x = lc.time,
                 y1 = sin_model(params[0], params[1] - standard_errors[1], params[2] - standard_errors[2], params[3] - standard_errors[3] - 1, lc.time),
                 y2 = sin_model(params[0], params[1] + standard_errors[1], params[2] + standard_errors[2], params[3] + standard_errors[3] - 1, lc.time),
                 color="b", alpha=0.5)

# Legend
high_patch = patches.Patch(color="g", alpha=0.4, label="High Phase")
low_patch = patches.Patch(color="r", alpha=0.4, label="Low Phase")
plt.legend(handles=[high_patch, low_patch])

# Axes labels
ax = plt.gca()
ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):d}"[3:]))
plt.xlabel(f"Truncated Mission Time [{str(int(min(lc.time)))[:3]}] (s)")
plt.ylabel("Rate (counts/s)")
plt.title(f"Phase GTIs for {filename}", fontweight="bold")

# Calculate chi-squared and chi-squared per degree of freedom
chi2 = chi_squared(*params, t=times, y=rates, dy=errors)
chi2dof = chi2 / (lc.time.size - len(theta_guess))

print(f"chi^2 = {round(chi2, 3)}\nchi^2/dof = {round(chi2dof, 3)}")

plt.text(times[0], lc.rate.min() + 0.4, r"$\chi^2 = $" + f"{round(chi2, 3)}\n" + r"$\chi^2_{dof} = $" + f"{round(chi2dof, 3)}")

# Show and save plot
plt.savefig(f"{cwd}/gti_phases.png", dpi=300, bbox_inches="tight")
plt.show()

if build:
    # Run gtibuild on both High and Low phase GTIs
    subprocess.run("gtibuild file=gti_High.txt table=gti_High.fits", shell=True)
    subprocess.run("gtibuild file=gti_Low.txt table=gti_Low.fits", shell=True)

    # Remove .txt files
    os.remove("gti_High.txt")
    os.remove("gti_Low.txt")
