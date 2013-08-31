#!/usr/bin/env python
"""
Pull together the NCES data and the Segregation calculator to produce
general reports on segregation in the USA.
"""
import sys
import argparse
import operator

from segcalc import SegCalc
from nces_parser import NCESParser
from fips import fips_to_st

from xlwt import Workbook

# ==============================================================================
# Constants
# ==============================================================================
# Maximum number of rows to report in an output file.
MAX_RECORD = 1000

# ==============================================================================
# Functions
# ==============================================================================
def calc_idxes(segcalc):
    """
    Call down to get all the various measures calculated
    """
    print "Calculating Dissimilarity Index"
    dis_idx = segcalc.calc_dis_idx()
    print "Calculating Exposure Index"
    exp_idx = segcalc.calc_exp_idx()
    print "Calculating Isolation Index"
    iso_idx = segcalc.calc_iso_idx()
    print "Calculating Total Minority Students"
    min_idx = segcalc.calc_totals('MINORITY')
    print "Calculating Total Student Count"
    tot_idx = segcalc.calc_totals()
    print "Calculating Proportion of Students in the Minority"
    mper_idx = segcalc.calc_proportion(idx='MINORITY')
    print "Calculating Proportion of Students in a Magnet"
    mag_idx = segcalc.calc_dependant_totals(sum_idx='MEMBER', dep_idx='MAGNET')
    pmag_idx = segcalc.calc_prop(mag_idx, tot_idx)
    print "Calculating Proportion of Students in a Charter"
    chr_idx = segcalc.calc_dependant_totals(sum_idx='MEMBER', dep_idx='CHARTR')
    pchr_idx = segcalc.calc_prop(chr_idx, tot_idx)
    print "Calculating Proportion of Students in a Magnet or Charter"
    chc_idx = segcalc.calc_dependant_totals(sum_idx='MEMBER', dep_idx='CHARTR', sec_dep_idx='MAGNET')
    pchc_idx = segcalc.calc_prop(chc_idx, tot_idx)
    print "Done with Calculations"
    return (dis_idx, exp_idx, iso_idx, min_idx, tot_idx, mper_idx, pmag_idx, pchr_idx, pchc_idx)

# -------------------------------------
def save_report(year_range, idxes, count, category_list, category_txt, category_txt2, filename):
    """
    Write out a bunch of report data to a spreadsheet report.
    Report will be a 2D matrix:
        - X-Axis = school year
        - Y-Axis = 'Category' (FIPS Code, District, etc...)

    Notes:
        - idxes contains the data
        - worksheets is a list of XLS worksheets, one per report in idxes
    """
    wb = Workbook()
    dws = wb.add_sheet('Dissimilarity Index')
    ews = wb.add_sheet('Exposure Index')
    iws = wb.add_sheet('Isolation Index')
    min = wb.add_sheet('Minority Student Count')
    tot = wb.add_sheet('Student Count')
    mper = wb.add_sheet('Minority Proportion')
    pmag = wb.add_sheet('Magnet Proportion')
    pchr = wb.add_sheet('Charter Proportion')
    pchc = wb.add_sheet('Choice Proportion')

    worksheets = [dws, ews, iws, min, tot, mper, pmag, pchr, pchc]

    # Create the headers/labels row/col
    for ws in worksheets:
        ws.write(0, 0, "Agency Name")
        for j, st in enumerate(category_list):
            if j < count:
                if len(category_txt[st]) == 2: # Don't change caps for State abbr.
                    ws.write(j+1, 0, category_txt[st])
                else:
                    ws.write(j+1, 0, category_txt[st].title())
        offset = 1

    if category_txt2:
        for ws in worksheets:
            ws.write(0, 1, "State")
            for j, st in enumerate(category_list):
                if j < count:
                    ws.write(j+1, 1, fips_to_st[category_txt2[st]][0])
        offset = 2

    # Print out the data
    for i, year in enumerate(year_range):
        print "Write Report for:  %d" % year
        for ws in worksheets:
            ws.write(0, i+offset, year)
        for j, st in enumerate(category_list):
            if j < count:
                for k, idx in enumerate(idxes):
                    try:
                        if k <= 5 and idx[i][st] < 0.001:
                            worksheets[k].write(j+1, i+offset, "")
                        else:
                            worksheets[k].write(j+1, i+offset, idx[i][st])
                    except KeyError:
                        worksheets[k].write(j+1, i+offset, "")
    wb.save(filename)

# -------------------------------------
# Parse the command line options
# -------------------------------------
def main(argv):
    parser = argparse.ArgumentParser(description='Segregation Report Generator')
    parser.add_argument('--outfile', action='store', dest='outfile', required=True,
            help='Report Filename')
    parser.add_argument('--category', action='store', dest='category', required=False,
            help='Which Category do we sort the results by?')
    parser.add_argument('--match_idx', action='store', dest='match_idx', required=False,
            help='Only use data points that match some criterion')
    parser.add_argument('--match_val', action='store', dest='match_val', required=False,
            help='Value to match when using --match_idx')
    parser.add_argument('--minority', action='store', dest='minority', required=False,
            help='Override the default list of Minority Groups')
    parser.add_argument('--sec_minority', action='store', dest='sec_minority', required=False,
            help='Override the default list of Secondary Minority Groups')
    parser.add_argument('--majority', action='store', dest='majority', required=False,
            help='Override the default list of Majority Groups')
    parser.add_argument('--year', action='store', dest='year', required=False, type=int,
            help='Override the default list of years to report on')
    parser.add_argument('--max_record', action='store', dest='max_record', required=False,
            help='Override the default number of items to report')
    parser.add_argument('-debug', action='store_true', dest='debug', required=False,
            help='Debug Mode')
    args = parser.parse_args()

    if args.category:
        category = args.category
    else:
        category = 'LEAID'

    # Lets calculate all the data first
    if args.debug:
        year_range = range(2009,2011)
        minorities = ['BLACK']
        sec_minorities = [None]
        majorities = ['WHITE']
        filenames = ['blacks_white']
    else:
        year_range = range(1987, 2011)
        minorities     = ['BLACK', 'HISP', 'BLACK', 'HISP', 'FRELCH', 'FRELCH']
        sec_minorities = [None, None, 'HISP', None, None, 'REDLCH']
        majorities     = ['WHITE', 'WHITE', 'WHITE', 'BLACK', None, None]
        filenames      = ['blacks_white', 'hisp_white', 'minorities_white', 'hisp_black', 'free_lunch', 'free_red_lunch']

    # Override the default years/groups per command line requests
    if args.year:
        year_range = [args.year]
    if args.minority:
        minorities = [args.minority]
        filenames = [""]
    if args.sec_minority:
        sec_minorities = [args.sec_minorities]
    if args.majority:
        majorities = [args.majority]

    # Print out more or fewer records than the default
    if args.max_record:
        report_count = int(args.max_record)
    else:
        report_count = MAX_RECORD

    # Default search query
    idx = {
        'MINORITY': 'BLACK',
        'MAJORITY': 'WHITE',
        'TOTAL': 'MEMBER',
        'CATEGORY': category,
        'SUB_CAT': 'LEAID',
    }
    if args.match_idx:
        idx['MATCH_IDX'] = args.match_idx
        idx['MATCH_VAL'] = args.match_val

    for i, group in enumerate(minorities):
        idx['MINORITY'] = minorities[i]
        idx['SEC_MINORITY'] = sec_minorities[i]
        idx['MAJORITY'] = majorities[i]
        print "*" * 80
        print "Running all calculations with the following parameters"
        print "*" * 80
        print idx
        print "*" * 80
        DATASETS = 9
        datasets = [[] for _ in range(DATASETS)]

        for year in year_range:
            print "Loading NCES Data from:  %d" % year
            nces = NCESParser(year=year)
            schools = nces.parse(make_dict=True)
            print "Finished Loading NCES Data from:  %d" % year
            if args.debug:
                # print schools
                pass
            # Get our data query ready
            segcalc = SegCalc(schools, idx)
            if category == 'LEAID':
                category_lut = segcalc.get_idxed_val('LEAID', 'LEANM')
                category_lut2 = segcalc.get_idxed_val('LEAID', 'FIPS')
            elif category == 'FIPS':
                category_lut = dict(zip(fips_to_st.keys(), [fips_to_st[key][0] for key in fips_to_st.keys()]))
                category_lut2 = None

            print "Performing Calculations on Data from:  %d" % year
            dataset = calc_idxes(segcalc)
            print "Finished Performing Calculations on Data from:  %d" % year

            print "Appending Yearly Data"
            for j in range(DATASETS):
                datasets[j].append(dataset[j])

        print "Sorting By Size of the last year"
        category_by_size = sorted(dataset[4].iteritems(), key=operator.itemgetter(1), reverse=True)
        category_list = []
        for category, total in category_by_size:
            category_list.append(category)
        if args.debug:
            print "dist_dict = {"
            for cat in category_list:
                print "    '%s': '%s'," % (cat, category_lut[cat].title())
            print "}"

        print "Generating Report"
        save_report(
                year_range,
                datasets,
                report_count,
                category_list,
                category_lut,
                category_lut2,
                filenames[i] + '_' + args.outfile
            )

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



