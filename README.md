# X-Ray-Astronomy-Tools
A collection of useful scripts and config files.

---
## quickView.py

Quickly view any light curve, or multiple light curves.

`python quickView.py <FileName> <BinSize>`

Options:
```
s --save - Save plot to image

-x --extra - Add additional light curves to plot

-m --mean - Show mean/median statistics

-t --stdev - Show the standard deviation statistics

-d --xmmdata - Load XMM light curves: lc, bg, lccor. Give only the prefix as the FileName

-e --energy - Specify the energy range of XMM light curves, defaults to 0.3-10keV

-a --all - Plot all light curves in current directory
```

---
## fluxResolve.py

Identifies low and high phases by flux and writes them to a txt file for conversion into a GTI file.

`python fluxResolve.py <FileName> <Start> <End> <significance> <BinSize>`

## phaseResolve.py

Phase resolve a light curve and write to a txt file for conversion into a GTI file.

`python phaseResolve.py <FileName> <Start> <End> <frequency> <phase> <BinSize>`

---
## plotSteppar.py

Plots an Xspec steppar saved by the `stp` proc (See `xspec.rc`). Can plot either 1D or 2D steppars directly from Xspec.

## plotMCMC.py

Generates a corner plot based on the distributions of the specified parameters of the most recent MCMC run in Xspec. Should be called by the `corner` proc (See `xspec.rc`).

---
## LightCurveCut.py

Cuts all light curves down to between two specified points in time. Specify a file containing the start and end points, all light curves in the current directory will be cut down to between these points. You can specify the suffix of the new light curve files.

`python LightCurveCut.py <FileName> <Suffix>`

---
## xspec_log.sh

Automatically set the Xspec log file the set directory and with current date as a suffix.

## logCommands.py

Quickly view only the commands in an Xspec log file. 

`python logCommands.py <logfile>`

Options:
```
-l --long - (0) Do not show long commands (>100 characters),
            (1) Show only location of long commands,
            (2) Show long commands

-s --supress - Supress commands from loading .xcm files.
```
---
## xspec.rc

Xspec config file containing several useful procs and timesaving aliases.

---
