#!/bin/bash

# Automatically create response matrices for resolve spectra with minimal manual input.
#
# Will process all observations listed in obs.txt, this should be in CSV format with columns:
# obs_name, 3/obs_id, 311/obs_mode
# HEASoft must be initialised. Resolve processing must have been run already.
#
# Author: Thomas Hodd
#
# Date: 12th May 2026
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
for i in "${!obs[@]}"; do
    obsid="${obs[i]}"
    label="${lbl[i]}"
    obsmode="${mode[i]}"
    cd $label

    # Get obsid proper (Not including the x/ part used in the wget URL)
    spec="${label}_rsl.pha"
    obsid=${obsid##*/}

    # Create RMF
    event_file="xa${obsid}rsl_p0px${obsmode}_cl.evt.gz"
    cd $obsid/analysis
    punlearn rslmkrmf
    rslmkrmf infile=${event_file} outfileroot=${label}_rsl regmode=DET whichrmf=L resolist=0 regionfile=None pixlist=0-11,13-26,28-35

    echo -e "${GREN}Created response matrix for ${label}${ENDC}"
    cd ../../../
done
