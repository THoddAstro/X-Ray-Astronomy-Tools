"""
Shows only commands from an XSPEC log file.

Usage
---------
python logCommands.py <logfile>

logfile: - XSPEC log file

Options
---------
-l --long - (0) Do not show long commands (>100 characters), (1) Show only location of long commands, (2) Show long commands

-s --supress - Supress commands from loading .xcm files.

---------

Author - Thomas Hodd

Date - 15th July 2025

Version - 1.0
"""
import argparse

parser = argparse.ArgumentParser(description="Shows only commands from an XSPEC log file")
parser.add_argument("logfile", type=str, help="XSPEC log file")
parser.add_argument("-l", "--long", type=int, default=0, help="Show long commands (optional, default 0)")
parser.add_argument("-s", "--supress", action="store_true", help="Supress commands from loading .xcm files")

args = parser.parse_args()
logf = args.logfile
long = args.long
supress = args.supress

with open(logf, "r") as f:
    for line in f.readlines():
        if line.startswith("!XSPEC12>"):
            if len(line.split()) < 100:
                if supress and line.split("!XSPEC12>")[1][0] == " ":
                    print(line.split("!XSPEC12>")[1][1:],  end="")
                elif not supress:
                    print(line.split("!XSPEC12>")[1], end="")
            else:
                if long == 1:
                    print("LINE TOO LONG TO PRINT")
                elif long == 2:
                    if supress and line.split("!XSPEC12>")[1][0] == " ":
                        print(line.split("!XSPEC12>")[1][1:],  end="")
                    elif not supress:
                        print(line.split("!XSPEC12>")[1], end="")
