#!/bin/bash

# Copies xtend background subtracted light curves from multiple observations into one directory.
#
# Will process all observations listed in obs.txt, this should be in CSV format with columns:
# obs_name, 3/obs_id, 311/obs_mode, min_energy, max_energy
# (Energies in eV)
#
# Light curves must have been extracted already by xtend_process.sh
#
# Author: Thomas Hodd
#
# Date: 4th May 2026
#
# Version: 1.0

# Terminal colour codes
set -e
ENDC="\033[0m"
ERRR="\033[91m"
GREN="\033[92m"
WARN="\033[93m"
BLUE="\033[94m"
PINK="\033[95m"
CYAN="\033[96m"

# Initialise arrays
lbl=()
obs=()
mode=()

# Read requested observations
while IFS=", " read -r label obsid obsmode enmin enmax; do
    lbl+=("$label")
    obs+=("$obsid")
    mode+=("$obsmode")
    echo -e "${GREN}Added Obs.ID $obsid, mode $obsmode with label: $label${ENDC}"
    echo -e "${GREN}Energy range ignored${ENDC}"
done < obs.txt

# Process each observation
for i in "${!obs[@]}"; do
    obsid="${obs[i]}"
    label="${lbl[i]}"
    obsmode="${mode[i]}"
    obsid=${obsid##*/}
    mkdir -p "XtendLightcurves/${label}"
    cp ${label}/${obsid}/analysis/energy_lcs/*_lccor.lc XtendLightcurves/${label}
    cp ${label}/${obsid}/analysis/*_lccor.lc XtendLightcurves/
    echo -e "${BLUE}Copied ${label}${ENDC}"
done
