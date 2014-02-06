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
    sheets = []
    sheets.append(wb.add_sheet("School Summary"))
    sheets.append(wb.add_sheet("Charter Summary"))
    sheets.append(wb.add_sheet("Magnet Summary"))
    row_offset = [2, 2, 2]

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
        "Minority Proportion",
        "Other Enrollment",
        "Other Proportion"
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
        for ws in sheets:
            ws.write(0, col_offset, header)
        col_offset += 1

    # --------------------------------------
    # Now fill in the static data data
    # --------------------------------------
    dist_total = 0.0
    dist_white = 0.0
    dist_black = 0.0
    dist_hisp = 0.0
    for school in schools:
        if (
            school['LEAID'] == leaid and
            school['STATUS'] == '1'
        ):
            # print school
            if school['CHARTR'] == '1':
                idx = 1
            elif school['MAGNET'] == '1':
                idx = 2
            else:
                idx = 0

            name = school['SCHNAM']
            total = float(school['MEMBER'])
            white = float(school['WHITE'])
            black = float(school['BLACK'])
            hisp = float(school['HISP'])
            dist_total += total
            dist_white += white
            dist_black += black
            dist_hisp += hisp

            sheets[idx].write(row_offset[idx], 0, name)
            sheets[idx].write(row_offset[idx], 1, total)
            sheets[idx].write(row_offset[idx], 2, white)
            sheets[idx].write(row_offset[idx], 3, white/total)
            sheets[idx].write(row_offset[idx], 4, black)
            sheets[idx].write(row_offset[idx], 5, black/total)
            sheets[idx].write(row_offset[idx], 6, hisp)
            sheets[idx].write(row_offset[idx], 7, hisp/total)
            sheets[idx].write(row_offset[idx], 8, black+hisp)
            sheets[idx].write(row_offset[idx], 9, (black+hisp)/total)
            sheets[idx].write(row_offset[idx], 10, total-white-black-hisp)
            sheets[idx].write(row_offset[idx], 11, (total-white-black-hisp)/total)
            row_offset[idx] += 1

    print "District Summary"
    for idx in range(3):
        sheets[idx].write(1, 0, "District Totals")
        sheets[idx].write(1, 1, dist_total)
        sheets[idx].write(1, 2, dist_white)
        sheets[idx].write(1, 3, dist_white/dist_total)
        sheets[idx].write(1, 4, dist_black)
        sheets[idx].write(1, 5, dist_black/dist_total)
        sheets[idx].write(1, 6, dist_hisp)
        sheets[idx].write(1, 7, dist_hisp/dist_total)
        sheets[idx].write(1, 8, dist_black+dist_hisp)
        sheets[idx].write(1, 9, (dist_black+dist_hisp)/dist_total)
        sheets[idx].write(1, 10, dist_total-dist_white-dist_black-dist_hisp)
        sheets[idx].write(1, 11, (dist_total-dist_white-dist_black-dist_hisp)/dist_total)

    print "Generating Report"
    wb.save(args.outfile)

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



