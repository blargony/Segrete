#!/usr/bin/env python
"""
A quick report that summarizes the details of all the charters
in a given district
"""
import sys
import argparse

from segcalc import SegCalc
from nces_parser import NCESParser

from xlwt import Workbook
from xlwt import Formula

# ==============================================================================
# Constants
# ==============================================================================
default_dist = '0634320'   # San Diego Unified

# ==============================================================================
# Functions
# ==============================================================================
def write_ws(worksheets, leaid, row, col, data):
    try:
        val = data[leaid]
    except KeyError:
        val = ""
    if val < 0.001:
        val = ""

    worksheets[leaid].write(row, col, val)

# -------------------------------------
# Parse the command line options
# -------------------------------------
def main(argv):
    parser = argparse.ArgumentParser(description='Segregation Report Generator')
    parser.add_argument('--outfile', action='store', dest='outfile', required=True,
            help='Report Filename')
    parser.add_argument('-leaid', action='store', dest='leaid', required=False,
            help='Local Agency (School District) ID')
    parser.add_argument('-debug', action='store_true', dest='debug', required=False,
            help='Debug Mode')
    args = parser.parse_args()

    # List of Districts
    if args.leaid:
        leaid = args.leaid
    else:
        leaid = default_dist

    nces = NCESParser(year=2010)
    schools = nces.parse(make_dict=True)

    wb = Workbook()
    ws = wb.add_sheet("Charter Summary")
    row_offset = 1

    # --------------------------------------
    # Create the column labels
    # --------------------------------------
    headers = [
        "School Name",
        "Enrollment",
        "White Enrollment",
        "White Proportion",
        "Black Enrollment",
        "Black Proportion",
        "Hisp Enrollment",
        "Hisp Proportion",
        "Minority Enrollment",
        "Minority Proportion"
    ]

    indexes = [
        "SCHNAM",
        "MEMBER",
        "WHITE",
        "BLACK",
        "HISP"
    ]

    col_offset=0

    # Common Data Across minorities
    # e.g. Total Students in a district
    for header in headers:
        ws.write(0, col_offset, header)
        col_offset += 1

    # --------------------------------------
    # Now fill in the static data data
    # --------------------------------------
    for school in schools:
        if (
            school['LEAID'] == leaid and
            school['STATUS'] == '1' and
            school['CHARTR'] == '1'
        ):
            print school

            name = school['SCHNAM']
            total = float(school['MEMBER'])
            white = float(school['WHITE'])
            black = float(school['BLACK'])
            hisp = float(school['HISP'])

            ws.write(row_offset, 0, name)
            ws.write(row_offset, 1, total)
            ws.write(row_offset, 2, white)
            ws.write(row_offset, 3, white/total)
            ws.write(row_offset, 4, black)
            ws.write(row_offset, 5, black/total)
            ws.write(row_offset, 6, hisp)
            ws.write(row_offset, 7, hisp/total)
            ws.write(row_offset, 8, black+hisp)
            ws.write(row_offset, 9, (black+hisp)/total)
            row_offset += 1

    print "Generating Report"
    wb.save(args.outfile)

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



