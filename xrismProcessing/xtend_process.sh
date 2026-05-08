#!/bin/bash

# Automatically download and process xtend light curves with minimal manual input.
#
# Will process all observations listed in obs.txt, this should be in CSV format with columns:
# obs_name, 3/obs_id, 311/obs_mode, min_energy, max_energy
# (Energies in eV)
#
# Requires get_regions_xrism.py in the same directory as bash script
# User must select background region when prompted, and verify the source has been correctly identified.
#
# Extracted light curves will have 10s bins.
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

    # Determine min/max pha channels from energy limits
    minpha=$(awk "BEGIN { printf(\"%.0f\", $enmin * 0.1667) }")
    maxpha=$(awk "BEGIN { printf(\"%.0f\", $enmax * 0.1667) }")
    emins+=("$enmin")
    emaxs+=("$enmax")
    phamins+=("$minpha")
    phamaxs+=("$maxpha")

    echo -e "${GREN}Added Obs.ID $obsid, mode $obsmode with label: $label${ENDC}"
    echo -e "${GREN}Energy range $enmin-$enmax ($minpha-$maxpha)${ENDC}"
done < obs.txt

# Make directories for each observation
for label in "${lbl[@]}"; do
    if [ ! -d "$label" ]; then
        mkdir "$label"
    else
        echo -e "${WARN}Directory $label already exists!${ENDC}"
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
    wget -nv -m -np -nH --cut-dirs=5 -R "index.html*" -erobots=off --wait=1 "https://heasarc.gsfc.nasa.gov/FTP/xrism/data/obs/$obsid/xtend/event_cl/"
    wget -nv -m -np -nH --cut-dirs=5 -R "index.html*" -erobots=off --wait=1 "https://heasarc.gsfc.nasa.gov/FTP/xrism/postlaunch/gainreports/"$obsid"_resolve_energy_scale_report.pdf"

    # Get obsid proper (Not including the x/ part used in the wget URL)
    obsid=${obsid##*/}

    # Copy event file to analysis directory
    echo -e "${BLUE}Extracting image from $label ($obsid) ...${ENDC}"
    event_file="xa${obsid}xtd_p0${obsmode}00010_cl.evt.gz"
    cd "$obsid"
    mkdir -p analysis
    cp xtend/event_cl/${event_file} analysis/${event_file}
    cd analysis

    # Extract image to identify src/bkg regions
    xselect << EOF
xtend_batch_process
clear all proceed=yes
read events xa${obsid}xtd_p0${obsmode}00010_cl.evt.gz .
set image det
filter pha_cut ${phamins[i]} ${phamins[i]}
extr image
save image ${label}.img clobberit=true
exit save_session=no
EOF

    # Get regions using Python script
    echo -e "${BLUE}Identifying regions for $label ($obsid) ...${ENDC}"
    python ../../../get_regions_xrism.py ${label}.img $label
    echo -e "${GREN}Written region files ${label}_src.reg, ${label}_bkg.reg${ENDC}"

    # Define region and light curve file names
    srcfile="${label}_src.reg"
    bkgfile="${label}_bkg.reg"
    src_lc="${label}_tbin10_en${emins[i]}_${emaxs[i]}_src.lc"
    bkg_lc="${label}_tbin10_en${emins[i]}_${emaxs[i]}_bkg.lc"
    cor_lc="${label}_tbin10_en${emins[i]}_${emaxs[i]}_lccor.lc"

    # Extract Light Curves
    xselect << EOF
xtend_batch_process
clear all proceed=yes
read events xa${obsid}xtd_p0${obsmode}00010_cl.evt.gz .
set image det
filter pha_cut ${phamins[i]} ${phamaxs[i]}
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
    echo -e "${GREN}Extracted light curves for ${label}${ENDC}"
    cd ../../../
done


