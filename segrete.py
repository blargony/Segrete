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
MAX_RECORD = 100

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
    min_idx = segcalc.calc_totals(idx='Y_GROUP')
    print "Calculating Total Student Count"
    tot_idx = segcalc.calc_totals()
    print "Calculating Proportion of Students in the Minority"
    mper_idx = segcalc.calc_proportion(idx='Y_GROUP')
    print "Done with Calculations"
    return (dis_idx, exp_idx, iso_idx, min_idx, tot_idx, mper_idx)

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
    ews = wb.add_sheet('Exposure Index')
    iws = wb.add_sheet('Isolation Index')
    dws = wb.add_sheet('Dissimilarity Index')
    min = wb.add_sheet('Minority Student Count')
    size = wb.add_sheet('Student Count')
    mper = wb.add_sheet('Minority Student Proportion')

    worksheets = [ews, iws, dws, min, size, mper]

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
                        if idx[i][st] < 0.001:
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
    parser.add_argument('--group', action='store', dest='group', required=False,
            help='Override the default list of Minority Groups')
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
        groups = ['BLACK']
    else:
        year_range = range(1987, 2011)
        # year_range = range(1987,1990)
        groups = ['BLACK', 'HISP', 'WHITE', 'FRELCH']

    # Override the default years/groups per command line requests
    if args.group:
        groups = [args.group]
    if args.year:
        year_range = [args.year]
    if args.max_record:
        report_count = int(args.max_record)
    else:
        report_count = MAX_RECORD

    # Default search query
    idx = {
        'Y_GROUP': 'BLACK',
        'Z_GROUP': 'WHITE',
        'TOTAL': 'MEMBER',
        'CATEGORY': category,
        'SUB_CAT': 'LEAID',
    }
    if args.match_idx:
        idx['MATCH_IDX'] = args.match_idx
        idx['MATCH_VAL'] = args.match_val

    for group in groups:
        idxes = [[], [], [], [], [], []]
        for year in year_range:
            print "Loading NCES Data from:  %d" % year
            nces = NCESParser(year=year)
            schools = nces.parse(make_dict=True)
            print "Finished Loading NCES Data from:  %d" % year
            if args.debug:
                # print schools
                pass
            # Get our data query ready
            idx['Y_GROUP'] = group
            segcalc = SegCalc(schools, idx)
            if category == 'LEAID':
                category_lut = segcalc.get_idxed_val('LEAID', 'LEANM')
                category_lut2 = segcalc.get_idxed_val('LEAID', 'FIPS')
            elif category == 'FIPS':
                category_lut = dict(zip(fips_to_st.keys(), [fips_to_st[key][0] for key in fips_to_st.keys()]))
                category_lut2 = None

            print "Performing Calculations on Data from:  %d" % year
            exp,iso,dis,min,tot,mper = calc_idxes(segcalc)
            print "Finished Performing Calculations on Data from:  %d" % year

            print "Appending Yearly Data"
            idxes[0].append(exp)
            idxes[1].append(iso)
            idxes[2].append(dis)
            idxes[3].append(min)
            idxes[4].append(tot)
            idxes[5].append(mper)

        print "Sorting By Size of the last year"
        category_by_size = sorted(tot.iteritems(), key=operator.itemgetter(1), reverse=True)

        print "Filtering out Districts with very low minority percentages"
        category_list = []
        for category, total in category_by_size:
            if total > 1000 and min[category]/total > 0.1:
                category_list.append(category)
            else:
                if args.debug:
                    print "Skipping District:  %s, Total Students: %d, Group Students: %d" % (category_lut[category], tot[category], min[category])

        print "Generating Report"
        save_report(
                year_range,
                idxes,
                report_count,
                category_list,
                category_lut,
                category_lut2,
                group.lower() + '_' + args.outfile
            )

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



