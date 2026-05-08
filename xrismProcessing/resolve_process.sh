#!/bin/bash

# Automatically download and process resolve spectra with minimal manual input.
#
# Will process all observations listed in obs.txt, this should be in CSV format with columns:
# obs_name, 3/obs_id, 311/obs_mode, min_energy, max_energy
#
# HEASoft must be initialised or XSelect commands will fail.
#
# Author: Thomas Hodd
#
# Date: 8th May 2026
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
    echo -e "${GREN}Energy range $enmin-$enmax ($minpha-$maxpha)${ENDC}"
done < obs_r.txt

# Make directories for each observation
for label in "${lbl[@]}"; do
    if [ ! -d "$label" ]; then
        mkdir "$label"
    else
        echo -e "${ERRR}Cannot proceed! Directory $label already exists!${ENDC}"
        # exit 1
    fi
done

# Process each observation
for i in "${!obs[@]}"; do
    obsid="${obs[i]}"
    label="${lbl[i]}"
    obsmode="${mode[i]}"
    cd $label

    # Download and extract ODF (NASA)
    # Download event_cl only
    echo -e "${BLUE}Downloading $label ($obsid) ...${ENDC}"
    wget -nv -m -np -nH --cut-dirs=5 -R "index.html*" -erobots=off --wait=1 "https://heasarc.gsfc.nasa.gov/FTP/xrism/data/obs/$obsid/resolve/event_cl/"
    wget -nv -m -np -nH --cut-dirs=5 -R "index.html*" -erobots=off --wait=1 "https://heasarc.gsfc.nasa.gov/FTP/xrism/postlaunch/gainreports/"$obsid"_resolve_energy_scale_report.pdf"

    # Get obsid proper (Not including the x/ part used in the wget URL)
    spec="${label}_rsl.pha"
    obsid=${obsid##*/}

    # Copy event file to analysis directory
    echo -e "${BLUE}Extracting image from $label ($obsid) ...${ENDC}"
    event_file="xa${obsid}rsl_p0px${obsmode}_cl.evt.gz"
    cd "$obsid"
    mkdir -p analysis
    cp resolve/event_cl/${event_file} analysis/${event_file}
    cd analysis

    # Extract spectrum
    xselect << EOF
test_session
clear all proceed=yes
read events ${event_file} .
filter GRADE "0:0"
filter column "PIXEL=0:11,13:26,28:35"
filter pha_cut ${phamins[i]} ${phamaxs[i]}
extr spec
save spec ${spec}
exit save_session=no
EOF

    echo -e "${GREN}Extracted spectrum for ${label}${ENDC}"
    cd ../../../
done


