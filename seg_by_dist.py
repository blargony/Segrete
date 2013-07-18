#!/usr/bin/env python
"""
Pull together the NCES data and the Segregation calculator to produce
general reports on segregation in the USA.
"""
import sys
import argparse

from segcalc import SegCalc
from nces_parser import NCESParser

from xlwt import Workbook

from tuda import tuda_dist
from big import big_dist

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
    parser.add_argument('--minority', action='store', dest='minority', required=False,
            help='Override the default list of Minority Groups')
    parser.add_argument('--sec_minority', action='store', dest='sec_minority', required=False,
            help='Override the default list of Secondary Minority Groups')
    parser.add_argument('--majority', action='store', dest='majority', required=False,
            help='Override the default list of Majority Groups')
    parser.add_argument('--year', action='store', dest='year', required=False, type=int,
            help='Override the default list of years to report on')
    parser.add_argument('-big_dist', action='store_true', dest='big_dist', required=False,
            help='Big District Mode')
    parser.add_argument('-debug', action='store_true', dest='debug', required=False,
            help='Debug Mode')
    args = parser.parse_args()

    # Lets calculate all the data first
    if args.debug:
        year_range = range(2009,2011)
        minorities = ['BLACK']
        sec_minorities = [None]
        majorities = ['WHITE']
    else:
        year_range = range(1987, 2011)
        minorities     = ['WHITE', 'BLACK', 'HISP', 'BLACK', 'HISP', 'FRELCH', 'FRELCH']
        sec_minorities = [None, None, None, 'HISP', None, None, 'REDLCH']
        majorities     = ['WHITE', 'WHITE', 'WHITE', 'WHITE', 'BLACK', None, None]

    # Override the default years/groups per command line requests
    if args.year:
        year_range = [args.year]
    if args.minority:
        minorities = [args.minority]
    if args.sec_minority:
        sec_minorities = [args.sec_minorities]
    if args.majority:
        majorities = [args.majority]
    if args.majority:
        majorities = [args.majority]
    if args.big_dist:
        dist_list = big_dist
    else:
        dist_list = tuda_dist

    wb = Workbook()
    worksheets = {}
    for leaid, dist_name in dist_list.items():
        worksheets[leaid] = wb.add_sheet(dist_name)

    # --------------------------------------
    # Create the row labels
    # --------------------------------------
    for ws in worksheets.values():
        for j, year in enumerate(year_range):
            ws.write(j+1, 0, year)
        base_col_offset = 1

    # --------------------------------------
    # Create the column labels
    # --------------------------------------
    minority_headers = [
        'count', # 'Minority Student Count',
        'prop', # 'Minority Proportion',
    ]

    min_maj_headers = [
        'dis_idx', # 'Dissimilarity Index',
        'exp_idx', # 'Exposure Index',
        'iso_idx', # 'Isolation Index',
    ]

    common_headers = [
        'stu_count', # 'Student Count',
        'mag_prop', # 'Magnet Proportion',
        'cha_prop', # 'Charter Proportion',
        'cho_prop', # 'Choice Proportion'
    ]

    for ws in worksheets.values():
        col_offset=1

        # Common Data Across minorities
        # e.g. Total Students in a district
        for header in common_headers:
            ws.write(0, col_offset, header)
            col_offset += 1

        # Data unique to each minority group
        # e.g. Proportion of Students in the Minority Group
        for j, minority in enumerate(minorities):
            min_label = minority[:2].lower()
            if sec_minorities[j]:
                min_label += "_"+sec_minorities[j][:2].lower()

            maj_label = min_label
            if majorities[j]:
                maj_label += "_"+majorities[j][:2].lower()

            for header in minority_headers:
                ws.write(0, col_offset, min_label+"_"+header)
                col_offset += 1
            for header in min_maj_headers:
                ws.write(0, col_offset, maj_label+"_"+header)
                col_offset += 1
        row_offset = 1

    # --------------------------------------
    # Now fill in the static data data
    # --------------------------------------
    for i, year in enumerate(year_range):
        # Reset the column offset as we move to a new row
        col_offset = base_col_offset

        # Default SegCalc search query - for calculating basic totals
        idx = {
            'TOTAL': 'MEMBER',
            'CATEGORY': 'LEAID',
            'MINORITY':  'BLACK',
            'SEC_MINORITY': '',
            'MAJORITY': 'WHITE',
            'MATCH_IDX': 'CHARTR',
            'MATCH_VAL': '1'
        }

        print "Loading NCES Data from:  %d" % year
        nces = NCESParser(year=year)
        schools = nces.parse(make_dict=True)
        segcalc = SegCalc(schools, idx)
        print "Finished Loading NCES Data from:  %d" % year

        print "Calculating Total Student Count"
        tot_idx = segcalc.calc_totals()
        for leaid in dist_list.keys():
            write_ws(worksheets, leaid, row_offset, col_offset, tot_idx)
        col_offset += 1

        print "Calculating Proportion of Students in a Magnet"
        mag_idx = segcalc.calc_dependant_totals(sum_idx='MEMBER', dep_idx='MAGNET')
        pmag_idx = segcalc.calc_prop(mag_idx, tot_idx)
        for leaid in dist_list.keys():
            write_ws(worksheets, leaid, row_offset, col_offset, pmag_idx)
        col_offset += 1

        print "Calculating Proportion of Students in a Charter"
        chr_idx = segcalc.calc_dependant_totals(sum_idx='MEMBER', dep_idx='CHARTR')
        pchr_idx = segcalc.calc_prop(chr_idx, tot_idx)
        for leaid in dist_list.keys():
            write_ws(worksheets, leaid, row_offset, col_offset, pchr_idx)
        col_offset += 1

        print "Calculating Proportion of Students in a Magnet or Charter"
        chc_idx = segcalc.calc_dependant_totals(sum_idx='MEMBER', dep_idx='CHARTR', sec_dep_idx='MAGNET')
        pchc_idx = segcalc.calc_prop(chc_idx, tot_idx)
        for leaid in dist_list.keys():
            write_ws(worksheets, leaid, row_offset, col_offset, pchc_idx)
        col_offset += 1

        # --------------------------------------
        # Now for each minority group - fill in the data
        # --------------------------------------
        for i, group in enumerate(minorities):
            idx['MINORITY'] = minorities[i]
            idx['SEC_MINORITY'] = sec_minorities[i]
            idx['MAJORITY'] = majorities[i]
            print "*" * 80
            print "Running all calculations with the following parameters"
            print "*" * 80
            print idx
            print "*" * 80
            segcalc = SegCalc(schools, idx)

            print "Performing Calculations on Data from:  %d" % year
            print "Calculating Total Minority Students"
            min_idx = segcalc.calc_totals('MINORITY')
            for leaid in dist_list.keys():
                write_ws(worksheets, leaid, row_offset, col_offset, min_idx)
            col_offset += 1

            print "Calculating Proportion of Students in the Minority"
            mper_idx = segcalc.calc_proportion(idx='MINORITY')
            for leaid in dist_list.keys():
                write_ws(worksheets, leaid, row_offset, col_offset, mper_idx)
            col_offset += 1

            print "Calculating Dissimilarity Index"
            dis_idx = segcalc.calc_dis_idx()
            for leaid in dist_list.keys():
                write_ws(worksheets, leaid, row_offset, col_offset, dis_idx)
            col_offset += 1

            print "Calculating Exposure Index"
            exp_idx = segcalc.calc_exp_idx()
            for leaid in dist_list.keys():
                write_ws(worksheets, leaid, row_offset, col_offset, exp_idx)
            col_offset += 1

            print "Calculating Isolation Index"
            iso_idx = segcalc.calc_iso_idx()
            for leaid in dist_list.keys():
                write_ws(worksheets, leaid, row_offset, col_offset, iso_idx)
            col_offset += 1
            print "Finished Performing Calculations on Data from:  %d" % year

        # New year, move to the next row
        row_offset += 1

    print "Generating Report"
    wb.save(args.outfile)

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



