#!/usr/bin/env python
"""
Pull together the NCES data and the Segragation index calculator to produce
some reports on segregation in the USA.
"""
import sys
import argparse

from segcalc import SegCalc
from nces_parser import NCESParser

from xlwt import Workbook

# ==============================================================================
# Constants
# ==============================================================================
fips_to_st = {
    1: ('AL', 'Alabama'),
    2: ('AK', 'Alaska'),
    4: ('AZ', 'Arizona'),
    5: ('AR', 'Arkansas'),
    6: ('CA', 'California'),
    8: ('CO', 'Colorado'),
    9: ('CT', 'Connecticut'),
    10: ('DE', 'Delaware'),
    11: ('DC', 'District of Columbia'),
    12: ('FL', 'Florida'),
    13: ('GA', 'Georgia'),
    15: ('HI', 'Hawaii'),
    16: ('ID', 'Idaho'),
    17: ('IL', 'Illinois'),
    18: ('IN', 'Indiana'),
    19: ('IA', 'Iowa'),
    20: ('KS', 'Kansas'),
    21: ('KY', 'Kentucky'),
    22: ('LA', 'Louisiana'),
    23: ('ME', 'Maine'),
    24: ('MD', 'Maryland'),
    25: ('MA', 'Massachusetts'),
    26: ('MI', 'Michigan'),
    27: ('MN', 'Minnesota'),
    28: ('MS', 'Mississippi'),
    29: ('MO', 'Missouri'),
    30: ('MT', 'Montana'),
    31: ('NE', 'Nebraska'),
    32: ('NV', 'Nevada'),
    33: ('NH', 'New Hampshire'),
    34: ('NJ', 'New Jersey'),
    35: ('NM', 'New Mexico'),
    36: ('NY', 'New York'),
    37: ('NC', 'North Carolina'),
    38: ('ND', 'North Dakota'),
    39: ('OH', 'Ohio'),
    40: ('OK', 'Oklahoma'),
    41: ('OR', 'Oregon'),
    42: ('PA', 'Pennsylvania'),
    44: ('RI', 'Rhode Island'),
    45: ('SC', 'South Carolina'),
    46: ('SD', 'South Dakota'),
    47: ('TN', 'Tennessee'),
    48: ('TX', 'Texas'),
    49: ('UT', 'Utah'),
    50: ('VT', 'Vermont'),
    51: ('VA', 'Virginia'),
    53: ('WA', 'Washington'),
    54: ('WV', 'West Virginia'),
    55: ('WI', 'Wisconsin'),
    56: ('WY', 'Wyoming')
}


# Maximum number of rows to report in an output file.
MAX_RECORD = 100

# ==============================================================================
# Functions
# ==============================================================================
def calc_idxes(segcalc):
    """
    Call down to get all the various measures calculated
    """
    print "Calculating Exposure Index"
    exp_idx = segcalc.calc_exp_idx()
    print "Calculating Isolation Index"
    iso_idx = segcalc.calc_iso_idx()
    print "Calculating Dissimilarity Index"
    dis_idx = segcalc.calc_dis_idx()
    print "Calculating Total Minority Students"
    min_idx = segcalc.calc_totals(idx='Y_GROUP')
    print "Calculating Total Student Count"
    tot_idx = segcalc.calc_totals()
    print "Done with Calculations"
    return (exp_idx, iso_idx, dis_idx, min_idx, tot_idx)

# --------------------------------------
def calc_idxes_range(year_range, idx):
    """
    Get all the results over the years
    """
    exp_idx = []
    iso_idx = []
    dis_idx = []
    for year in year_range:
        print "Working on NCES Data from:  %d" % year
        # Get our dataset ready
        nces = NCESParser(year=year)
        schools = nces.parse(make_dict=True)
        sg = SegCalc(schools, idx)
        exp_idx.append(sg.calc_exp_idx())
        iso_idx.append(sg.calc_iso_idx())
        dis_idx.append(sg.calc_dis_idx())
    return (exp_idx, iso_idx, dis_idx)

# -------------------------------------
def save_report(year_range, idxes, count, category_list, category_txt, filename):
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

    worksheets = [ews, iws, dws, min, size]

    # Create the headers/labels row/col
    for ws in worksheets:
        ws.write(0, 0, "LEA/Year")
        for j, st in enumerate(category_list):
            if j < count:
                if len(category_txt[st]) == 2: # Don't change caps for State abbr.
                    ws.write(j+1, 0, category_txt[st])
                else:
                    ws.write(j+1, 0, category_txt[st].title())

    # Print out the data
    for i, year in enumerate(year_range):
        print "Write Report for:  %d" % year
        for ws in worksheets:
            ws.write(0, i+1, year)
        for j, st in enumerate(category_list):
            if j < count:
                for k, idx in enumerate(idxes):
                    try:
                        if idx[i][st] < 0.001:
                            worksheets[k].write(j+1, i+1, "")
                        else:
                            worksheets[k].write(j+1, i+1, idx[i][st])
                    except KeyError:
                        worksheets[k].write(j+1, i+1, "")
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
        category = 'FIPS'

    # Lets calculate all the data first
    if args.debug:
        year_range = range(1987,1990)
        groups = ['BLACK']
    else:
        year_range = range(1987, 2011)
        # year_range = range(1987,1990)
        groups = ['BLACK', 'HISP', 'ASIAN', 'AM']

    # Override the default years/groups per command line requests
    if args.group:
        groups = [args.group]
    if args.year:
        year_range = [args.year]
    if args.max_record:
        report_count = int(args.max_record)
        print report_count
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
        idxes = [[], [], [], [], []]
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
            elif category == 'FIPS':
                category_lut = dict(zip(fips_to_st.keys(), [fips_to_st[key][0] for key in fips_to_st.keys()]))

            print "Performing Calculations on Data from:  %d" % year
            exp,iso,dis,min,tot = calc_idxes(segcalc)
            print "Finished Performing Calculations on Data from:  %d" % year

            print "Appending Yearly Data"
            idxes[0].append(exp)
            idxes[1].append(iso)
            idxes[2].append(dis)
            idxes[3].append(min)
            idxes[4].append(tot)

        print "Sorting By Size of the last year"
        category_by_size = sorted(tot, key=tot.get, reverse=True)
        # Filter out keys absent from our report tables.
        category_by_size = [i for i in category_by_size if i in category_lut.keys()]
        print "Generating Report"
        save_report(
                year_range,
                idxes,
                report_count,
                category_by_size,
                category_lut,
                group.lower() + '_' + args.outfile
            )

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



