#!/bin/bash

# Automatically process xtend narrow-band light curves with minimal manual input.
#
# Will process all observations listed in obs.txt, this should be in CSV format with columns:
# obs_name, 3/obs_id, 311/obs_mode, min_energy, max_energy
#
# Reads engs.txt to determine energy bins. This file should be a list of lower,upper energies in eV.
#
# Extracted light curves will have 10s bins.
#
# HEASoft must be initialised or XSelect commands will fail
#
# Author: Thomas Hodd
#
# Date: 7th May 2026
#
# Version: 1.1

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
emins=()
emaxs=()
phamins=()
phamaxs=()

# Read requested observations
while IFS=", " read -r label obsid obsmode enmin enmax; do
    lbl+=("$label")
    obs+=("$obsid")
    mode+=("$obsmode")

    echo -e "${GREN}Added Obs.ID $obsid, mode $obsmode with label: $label${ENDC}"
done < obs.txt

# Determine min/max pha channels from energy limits
while IFS=", " read -r enmin enmax; do
    minpha=$(awk "BEGIN { printf(\"%.0f\", $enmin * 0.1667) }")
    maxpha=$(awk "BEGIN { printf(\"%.0f\", $enmax * 0.1667) }")
    emins+=("$enmin")
    emaxs+=("$enmax")
    phamins+=("$minpha")
    phamaxs+=("$maxpha")

    echo -e "${GREN}Energy range $enmin-$enmax ($minpha-$maxpha)${ENDC}"
done < engs.txt

# Process each observation
for i in "${!obs[@]}"; do
    obsid="${obs[i]}"
    label="${lbl[i]}"
    obsid=${obsid##*/}
    obsmode="${mode[i]}"
    echo -e "${PINK}Extracting light curves from $label ($obsid) ...${ENDC}"
    cd ${label}/${obsid}/analysis
    mkdir -p energy_lcs

    # Define region file names
    srcfile="${label}_src.reg"
    bkgfile="${label}_bkg.reg"

    # Extract Light Curves
    for ((j=0; j<${#emins[@]}; j++)); do
        src_lc="energy_lcs/${label}_tbin10_en${emins[j]}_${emaxs[j]}_src.lc"
        bkg_lc="energy_lcs/${label}_tbin10_en${emins[j]}_${emaxs[j]}_bkg.lc"
        cor_lc="energy_lcs/${label}_tbin10_en${emins[j]}_${emaxs[j]}_lccor.lc"
        xselect << EOF
xtend_batch_process
clear all proceed=yes
read events xa${obsid}xtd_p0${obsmode}00010_cl.evt.gz .
set image det
filter pha_cut ${phamins[j]} ${phamaxs[j]}
set binsize 10
filter region ${srcfile}
extr curve
save curve ${src_lc}
clear region
filter region ${bkgfile}
extr curve
save curve ${bkg_lc}
exit save_session=no
EOF

        # Create Background-Subtracted Light Curve
        lcmath infile=${src_lc} bgfile=${bkg_lc} outfile=${cor_lc} multi=1 multb=1
        echo -e "${BLUE}Created ${src_lc}${ENDC}"
    done
    echo -e "${GREN}Extracted light curves for ${label}${ENDC}"
    cd ../../../
done
