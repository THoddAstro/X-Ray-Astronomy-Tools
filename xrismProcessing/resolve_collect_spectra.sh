#!/bin/bash

# Copies resolve spectra from multiple observations into one directory.
#
# Will process all observations listed in obs_r.txt, this should be in CSV format with columns:
# obs_name, 3/obs_id, 311/obs_mode
#
# Spectra must have been extracted already by resolve_process.sh
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
while IFS=", " read -r label obsid obsmode; do
    lbl+=("$label")
    obs+=("$obsid")
    mode+=("$obsmode")

    echo -e "${GREN}Added Obs.ID $obsid, mode $obsmode with label: $label${ENDC}"
done < obs_r.txt

# Process each observation
mkdir -p "ResolveSpectra/"
for i in "${!obs[@]}"; do
    obsid="${obs[i]}"
    label="${lbl[i]}"
    obsid=${obsid##*/}
    cp ${label}/${obsid}/analysis/*_rsl.pha ResolveSpectra/
    echo -e "${BLUE}Copied ${label}${ENDC}"
done
