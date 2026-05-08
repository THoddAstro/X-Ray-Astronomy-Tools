#!/bin/bash

# Automatically download and process xtend spectra with minimal manual input.
#
# Will process all observations listed in obs.txt, this should be in CSV format with columns:
# obs_name, 3/obs_id, 311/obs_mode, min_energy, max_energy
# (Energies in eV)
#
# Requires that xtend_process.sh has already been ran and region files have been created.
#
# HEASoft must be initialised or XSelect commands will fail.
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
    minpha=$(awk "BEGIN { printf(\"%.0f\", $enmin * 0.1667) }")
    maxpha=$(awk "BEGIN { printf(\"%.0f\", $enmax * 0.1667) }")
    emins+=("$enmin")
    emaxs+=("$enmax")
    phamins+=("$minpha")
    phamaxs+=("$maxpha")

    echo -e "${GREN}Added Obs.ID $obsid, mode $obsmode with label: $label${ENDC}"
    echo -e "${GREN}Energy range ignored for spectra${ENDC}"
done < obs.txt

# Process each observation
for i in "${!obs[@]}"; do
    obsid="${obs[i]}"
    label="${lbl[i]}"
    obsmode="${mode[i]}"
    obsid=${obsid##*/}
    cd "${label}/${obsid}/analysis"

    # Extract image to identify src/bkg regions
    echo -e "${BLUE}Reading image from $label ($obsid) ...${ENDC}"
    event_file="xa${obsid}xtd_p0${obsmode}00010_cl.evt.gz"

    srcfile="${label}_src.reg"
    bkgfile="${label}_bkg.reg"
    src_spec="${label}_src.pha"
    bkg_spec="${label}_bkg.pha"
    rmf="${label}.rmf"

    # Extract Light Curves
    xselect << EOF
xtend_batch_process
clear all proceed=yes
read events xa${obsid}xtd_p0${obsmode}00010_cl.evt.gz .
set image det
filter region ${srcfile}
extr spec
save spec ${src_spec}
clear region
filter region ${bkgfile}
extr spec
save spec ${bkg_spec}
exit save_session=no
EOF

    punlearn xtdrmf
    xtdrmf $src_spec $rmf

    cd ../../../
done
