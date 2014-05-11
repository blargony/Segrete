#!/usr/bin/env python
"""
Pull together the NCES data and the Segregation calculator to produce
general reports on segregation in the USA.

This report has each district on its own tab with all the years on the
vertical axis and the data types in the columns.
"""
import sys
import argparse

from segcalc import SegCalc
from nces_parser import NCESParser

from fips import fips_to_st

from xlwt import Workbook
from xlwt import Formula
from xlrd import cellname

# ==============================================================================
# Constants
# ==============================================================================

# ==============================================================================
# Functions
# ==============================================================================
def write_ws(worksheets, category, row, col, data):
    try:
        val = data[category]
    except KeyError:
        val = ""
    if val < 0.001:
        val = ""

    worksheets[category].write(row, col, val)

# -------------------------------------
# Parse the command line options
# -------------------------------------
def main(argv):
    parser = argparse.ArgumentParser(description='Segregation Report Generator')
    parser.add_argument('--outfile', action='store', dest='outfile', required=True,
            help='Report Filename')
    parser.add_argument('--category', action='store', dest='category', required=False,
            help='Which Category do we sort the results by?')
    parser.add_argument('--minority', action='store', dest='minority', required=False,
            help='Override the default list of Minority Groups')
    parser.add_argument('--sec_minority', action='store', dest='sec_minority', required=False,
            help='Override the default list of Secondary Minority Groups')
    parser.add_argument('--majority', action='store', dest='majority', required=False,
            help='Override the default list of Majority Groups')
    parser.add_argument('--match_idx', action='store', dest='match_idx', required=False,
            help='Only use data points that match some criterion')
    parser.add_argument('--match_val', action='store', dest='match_val', required=False,
            help='Value to match when using --match_idx')
    parser.add_argument('--year', action='store', dest='year', required=False, type=int,
            help='Override the default list of years to report on')
    parser.add_argument('--grade', action='store', dest='grade', required=False, type=int,
            help='Select a specific grade that the school must have')
    parser.add_argument('-debug', action='store_true', dest='debug', required=False,
            help='Debug Mode')
    args = parser.parse_args()

    # Lets calculate all the data first
    if args.debug:
        year_range = range(2009,2012)
        minorities = ['BLACK']
        sec_minorities = [None]
        majorities = ['WHITE']
        grade = False # All Grades
    else:
        year_range = range(1987, 2012)
        # year_range = range(2002, 2012, 2)  # Even years based on NAEP data
        minorities     = ['WHITE', 'BLACK', 'HISP', 'BLACK', 'HISP', 'FRELCH', 'FRELCH']
        sec_minorities = [None, None, None, 'HISP', None, None, 'REDLCH']
        majorities     = ['WHITE', 'WHITE', 'WHITE', 'WHITE', 'BLACK', None, None]
        grade = False # All Grades

    # Override the default years/groups per command line requests
    if args.year:
        year_range = [args.year]
    if args.minority:
        minorities = [args.minority]
    if args.sec_minority:
        sec_minorities = [args.sec_minorities]
    if args.majority:
        majorities = [args.majority]
    if args.grade:
        grade = args.grade

    if args.category:
        category = args.category
    else:
        category = 'LEAID'

    # Search through the data for the list of districts to report on
    nces = NCESParser(year=2010)
    schools = nces.parse(make_dict=True)
    categories = {}
    for school in schools:
        id = school[category]
        if category == 'LEAID':
            name = school['LEANM'][:28].title()
            name = name.replace("/", "_")
        else:
            name = fips_to_st[id][1]

        if id not in categories.keys():
            if name + "_1" in categories.values():
                name += "_2"
                print name
            elif name in categories.values():
                name += "_1"
                print name
            categories[id] = name
    # print categories
    print "Found %d Districts" % (len(categories.keys()))

    # Default SegCalc search query - for calculating basic totals
    idx = {
        'TOTAL': 'MEMBER',
        'CATEGORY': category,
        'MINORITY':  'BLACK',
        'SEC_MINORITY': '',
        'MAJORITY': 'WHITE'
    }
    if args.match_idx:
        idx['MATCH_IDX'] = args.match_idx
        idx['MATCH_VAL'] = args.match_val

    # --------------------------------------
    # Create all the Spreadsheets objects to populate
    # --------------------------------------
    wb = Workbook()
    worksheets = {}
    for category, name in categories.items():
        worksheets[category] = wb.add_sheet(name)

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

    # We start one row/col in from the upper left corner (1,1 in xlwt, B2 in Excel)
    row_offset = 1

    for ws in worksheets.values():
        col_offset = 1

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

    # --------------------------------------
    # Now fill in the static data data
    # --------------------------------------
    for i, year in enumerate(year_range):
        # Reset the column offset as we move to a new row
        col_offset = base_col_offset

        print "Loading NCES Data from:  %d" % year
        nces = NCESParser(year=year)
        schools = nces.parse(make_dict=True)
        segcalc = SegCalc(schools, idx, grade=grade)
        print "Finished Loading NCES Data from:  %d" % year

        print "Calculating Total Student Count"
        tot_idx = segcalc.calc_totals()
        for category in categories.keys():
            write_ws(worksheets, category, row_offset, col_offset, tot_idx)
        col_offset += 1

        print "Calculating Proportion of Students in a Magnet"
        mag_idx = segcalc.calc_dependant_totals(sum_idx='MEMBER', dep_idx='MAGNET')
        pmag_idx = segcalc.calc_prop(mag_idx, tot_idx)
        for category in categories.keys():
            write_ws(worksheets, category, row_offset, col_offset, pmag_idx)
        col_offset += 1

        print "Calculating Proportion of Students in a Charter"
        chr_idx = segcalc.calc_dependant_totals(sum_idx='MEMBER', dep_idx='CHARTR')
        pchr_idx = segcalc.calc_prop(chr_idx, tot_idx)
        for category in categories.keys():
            write_ws(worksheets, category, row_offset, col_offset, pchr_idx)
        col_offset += 1

        print "Calculating Proportion of Students in a Magnet or Charter"
        chc_idx = segcalc.calc_dependant_totals(sum_idx='MEMBER', dep_idx='CHARTR', sec_dep_idx='MAGNET')
        pchc_idx = segcalc.calc_prop(chc_idx, tot_idx)
        for category in categories.keys():
            write_ws(worksheets, category, row_offset, col_offset, pchc_idx)
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
            segcalc = SegCalc(schools, idx, grade=grade)

            print "Performing Calculations on Data from:  %d" % year
            print "Calculating Total Minority Students"
            min_idx = segcalc.calc_totals('MINORITY')
            for category in categories.keys():
                write_ws(worksheets, category, row_offset, col_offset, min_idx)
            col_offset += 1

            print "Calculating Proportion of Students in the Minority"
            mper_idx = segcalc.calc_proportion(idx='MINORITY')
            for category in categories.keys():
                write_ws(worksheets, category, row_offset, col_offset, mper_idx)
            col_offset += 1

            print "Calculating Dissimilarity Index"
            dis_idx = segcalc.calc_dis_idx()
            for category in categories.keys():
                write_ws(worksheets, category, row_offset, col_offset, dis_idx)
            col_offset += 1

            print "Calculating Exposure Index"
            exp_idx = segcalc.calc_exp_idx()
            for category in categories.keys():
                write_ws(worksheets, category, row_offset, col_offset, exp_idx)
            col_offset += 1

            print "Calculating Isolation Index"
            iso_idx = segcalc.calc_iso_idx()
            for category in categories.keys():
                write_ws(worksheets, category, row_offset, col_offset, iso_idx)
            col_offset += 1
            print "Finished Performing Calculations on Data from:  %d" % year

        # New year, move to the next row
        row_offset += 1

    last_data_row = row_offset - 1
    row_offset += 1

    stats = [
        ('Average', 'AVERAGE'),
        ('Median', 'MEDIAN'),
        ('Max', 'MAX'),
        ('Min', 'MIN'),
        ('StandardDev', 'STDEV')
    ]

    for title, formula in stats:
        for ws in worksheets.values():
            ws.write(row_offset, 0, title)
            for col in range(1,col_offset):
                ws.write(row_offset, col, Formula("%s(%s:%s)" % (formula, cellname(1, col), cellname(last_data_row, col))))
        row_offset += 1


    print "Generating Report"
    wb.save(args.outfile)

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



