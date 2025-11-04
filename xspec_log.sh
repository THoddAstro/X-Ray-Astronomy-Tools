#!/bin/bash
## Get the current date
current_date=$(date +%F)

## File names
xspec_rc="/home/thodd/.xspec/xspec.rc"
xspec_log="/home/thodd/xspec_logs/xspec_${current_date}.log"

## Set today's log file location
sed -i "s|^log >.*|log >${xspec_log}|" "$xspec_rc"

echo "XSPEC log file set to: ${xspec_log}"
