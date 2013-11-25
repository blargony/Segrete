#!/usr/bin/env python
"""
Quick report on the school counts by district.
"""
import sys
import argparse

from segcalc import SegCalc
from nces_parser import NCESParser

from filters.tuda import tuda_dist
from filters.ca_big import ca_big_dist

from xlwt import Workbook
from xlwt import Formula

# ==============================================================================
# Constants
# ==============================================================================

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
    parser.add_argument('-ca_big', action='store_true', dest='ca_big', required=False,
            help='Report Filename')
    parser.add_argument('-debug', action='store_true', dest='debug', required=False,
            help='Debug Mode')
    args = parser.parse_args()

    # List of Districts
    if args.ca_big:
        dist_list = ca_big_dist
    else:
        dist_list = tuda_dist

    dist_k12 = {}
    dist_hs = {}
    dist_mh = {}
    dist_ms = {}
    dist_k8 = {}
    dist_el = {}
    dist_other = {}
    dist_tot = {}
    for dist in dist_list.keys():
        dist_k12[dist] = 0
        dist_hs[dist] = 0
        dist_mh[dist] = 0
        dist_ms[dist] = 0
        dist_k8[dist] = 0
        dist_el[dist] = 0
        dist_other[dist] = 0
        dist_tot[dist] = 0

    nces = NCESParser(year=2010)
    schools = nces.parse(make_dict=True)

    # Default SegCalc search query - for calculating basic totals
    idx = {
        'TOTAL': 'MEMBER',
        'CATEGORY': 'LEAID',
        'MINORITY':  'BLACK',
        'SEC_MINORITY': '',
        'MAJORITY': 'WHITE'
    }
    segcalc = SegCalc(schools, idx)

    wb = Workbook()
    ws = wb.add_sheet("TUDA Summary")

    row_offset = 1
    for j, dist_name in enumerate(dist_list.values()):
        ws.write(j+1, 0, dist_name)

    # --------------------------------------
    # Create the column labels
    # --------------------------------------
    headers = [
        "Elementary Schools",
        "K-8 Schools",
        "Middle Schools",
        "Middle+High Schools",
        "High Schools",
        "K-12 Schools",
        "Other Schools",
        "Total Schools"
    ]

    col_offset=1

    # Common Data Across minorities
    # e.g. Total Students in a district
    for header in headers:
        ws.write(0, col_offset, header)
        col_offset += 1

    # --------------------------------------
    # Now fill in the static data data
    # --------------------------------------
    for school in schools:
        if segcalc.is_elementary(school):
            dist_el[school['LEAID']] += 1
        elif segcalc.is_high_school(school):
            dist_hs[school['LEAID']] += 1
        elif segcalc.is_middle(school):
            dist_ms[school['LEAID']] += 1
        elif segcalc.is_mh(school):
            dist_mh[school['LEAID']] += 1
        elif segcalc.is_k8(school):
            dist_k8[school['LEAID']] += 1
        elif segcalc.is_k12(school):
            dist_k12[school['LEAID']] += 1
        else:
            dist_other[school['LEAID']] += 1
            print dist_list[school['LEAID']]
            print school['SCHNAM']
            print segcalc.get_grade(school, high=True)
            print segcalc.get_grade(school, high=False)
        dist_tot[school['LEAID']] += 1

    for dist in dist_list.keys():
        ws.write(row_offset, 1, dist_el[dist])
        ws.write(row_offset, 2, dist_k8[dist])
        ws.write(row_offset, 3, dist_ms[dist])
        ws.write(row_offset, 4, dist_mh[dist])
        ws.write(row_offset, 5, dist_hs[dist])
        ws.write(row_offset, 6, dist_k12[dist])
        ws.write(row_offset, 7, dist_other[dist])
        ws.write(row_offset, 8, dist_tot[dist])
        # ws.write(row_offset, 9, Formula("SUM(B%d:H%d)" % (row_offset+1, row_offset+1)))   # Excel starts counting at 1, silly Excel
        row_offset += 1

    print "Generating Report"
    wb.save(args.outfile)

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



