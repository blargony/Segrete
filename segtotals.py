#!/usr/bin/env python
"""
Pull some totals and percentages out of the NCES data
"""
import sys
import argparse
import operator

from segcalc import SegCalc
from nces_parser import NCESParser

from xlwt import Workbook
from fips import fips_to_st

# ==============================================================================
# Constants
# ==============================================================================
# Maximum number of rows to report in an output file.
MAX_RECORD = 100

# ==============================================================================
# Functions
# ==============================================================================
def calc_totals(segcalc):
    """
    Call down to get all the various measures calculated
    """
    print "Calculating School Population Percentages"
    percentages = segcalc.calc_percentages()
    return percentages

# -------------------------------------
def save_totals(
    year_range,
    totals,
    entry_list,
    count,
    category_list,
    category_txt,
    category_txt2,
    filename
):
    """
    Write out a bunch of report data to a spreadsheet report.
    Report will be a 2D matrix:
        - X-Axis = school year
        - Y-Axis = 'Category' (FIPS Code, District, etc...)

    Notes:
        - idxes contains the data
        - worksheets is a list of XLS worksheets, one per report in idxes

    Arguments:
        year_range - list of years for the given totals
        totals - data set
        entry_list - entries per datum row
        count - how many of the datum to output
        category_list - list of groupings (district IDs, state FIPS numbers, etc...)
        category_txt - txt for groupings (district names, state names, etc...)
        category_txt2 - additional txt for the groups (district state, etc...)
        filename - output filename
    """
    wb = Workbook()
    percentages = wb.add_sheet('Student Percentages')

    worksheets = [percentages]

    y_offset=2
    # Create the headers/labels row/col
    for ws in worksheets:
        ws.write(0, 0, "Agency Name")
        for j, st in enumerate(category_list):
            if j < count:
                if len(category_txt[st]) == 2: # Don't change caps for State abbr.
                    ws.write(j+y_offset, 0, category_txt[st])
                else:
                    ws.write(j+y_offset, 0, category_txt[st].title())
        x_offset = 1

    if category_txt2:
        for ws in worksheets:
            ws.write(0, 1, "State")
            for j, st in enumerate(category_list):
                if j < count:
                    ws.write(j+y_offset, 1, fips_to_st[category_txt2[st]][0])
        x_offset = 2

    # Print out the data
    for i, year in enumerate(year_range):
        print "Write Report for:  %d" % year
        for ws in worksheets:
            ws.write_merge(0, 0, (i*len(entry_list))+x_offset, ((i+1)*len(entry_list))+x_offset-1, year)
            for j, entry in enumerate(entry_list):
                ws.write(1, (i*len(entry_list))+j+x_offset, entry)

        for j, st in enumerate(category_list):
            if j < count:
                for k, total in enumerate([totals]):
                    for l, entry in enumerate(entry_list):
                        try:
                            if totals[i][st][entry] < 0.001:
                                worksheets[k].write(j+y_offset, i*len(entry_list)+l+x_offset, "")
                            else:
                                worksheets[k].write(j+y_offset, i*len(entry_list)+l+x_offset, totals[i][st][entry])
                        except KeyError:
                            worksheets[k].write(j+y_offset, i+x_offset, "")
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
        category = 'FIPS'

    # Lets calculate all the data first
    if args.debug:
        year_range = range(1987, 1990)
    else:
        year_range = range(1987, 2011)

    # Override the default years/groups per command line requests
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

    totals = []
    for year in year_range:
        print "Loading NCES Data from:  %d" % year
        nces = NCESParser(year=year)
        schools = nces.parse(make_dict=True)
        print "Finished Loading NCES Data from:  %d" % year
        # Get our data query ready
        segcalc = SegCalc(schools, idx)
        if category == 'LEAID':
            category_lut = segcalc.get_idxed_val('LEAID', 'LEANM')
            category_lut2 = segcalc.get_idxed_val('LEAID', 'FIPS')
        elif category == 'FIPS':
            category_lut = dict(zip(fips_to_st.keys(), [fips_to_st[key][0] for key in fips_to_st.keys()]))
            category_lut2 = None

        print "Performing Calculations on Data from:  %d" % year
        totals.append(calc_totals(segcalc))
        print "Finished Performing Calculations on Data from:  %d" % year

    print "Sorting By Size of the last year"
    category_by_size = sorted([(key, value['MEMBER']) for key,value in totals[-1].iteritems()], key=operator.itemgetter(1), reverse=True)
    category_list = [category for category,total in category_by_size]

    print "Generating Report"
    save_totals(
            year_range,
            totals,
            ['WHITE', 'BLACK', 'HISP', 'ASIAN', 'AM'],
            report_count,
            category_list,
            category_lut,
            category_lut2,
            args.outfile
        )

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



