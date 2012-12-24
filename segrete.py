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


# ==============================================================================
# Functions
# ==============================================================================
def calc_idxes(year_range, idx):
    """
    Call down to get all the various measures calculated
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
def save_report(year_range, idxes, filename):
    # Break out the calculated data
    exp_idx, iso_idx, dis_idx = idxes

    # Now lets format it into a report.
    # Report will be a 2D matrix
    # X-Axis = school year
    # Y-Axis = FIPS Code
    wb = Workbook()
    ews = wb.add_sheet('Exposure Index')
    iws = wb.add_sheet('Isolation Index')
    dws = wb.add_sheet('Dissimilarity Index')

    worksheets = [ews, iws, dws]

    # Create the headers/labels row/col
    for ws in worksheets:
        ws.write(0, 0, "State/Year")
        for j, st in enumerate(fips_to_st):
            ws.write(j+1, 0, fips_to_st[st][0])

    # Print out the data
    for i, year in enumerate(year_range):
        print "Write Report for:  %d" % year
        for ws in worksheets:
            ws.write(0, i+1, year)
        for j, st in enumerate(fips_to_st.keys()):
            if exp_idx[i][st] < 0.001:
                ews.write(j+1, i+1, "")
            else:
                ews.write(j+1, i+1, exp_idx[i][st])

            if iso_idx[i][st] < 0.001:
                iws.write(j+1, i+1, "")
            else:
                iws.write(j+1, i+1, iso_idx[i][st])

            if dis_idx[i][st] < 0.001:
                dws.write(j+1, i+1, "")
            else:
                dws.write(j+1, i+1, dis_idx[i][st])
    wb.save(filename)

# -------------------------------------
# Parse the command line options
# -------------------------------------
def main(argv):
    parser = argparse.ArgumentParser(description='Segregation Report Generator')
    parser.add_argument('--year', action='store', dest='year', required=False, type=int,
            help='NCES Data Year')
    parser.add_argument('--outfile', action='store', dest='outfile', required=False,
            help='Report File')
    args = parser.parse_args()

    # Lets calculate all the data first
    year_range = range(1987, 2011)

    idx = {'Y_GROUP': 'BLACK', 'Z_GROUP': 'WHITE', 'TOTAL': 'MEMBER', 'CATEGORY': 'FIPS', 'SUB_CAT': 'LEAID'}
    idxes = calc_idxes(year_range, idx)
    save_report(year_range, idxes, "black_" + args.outfile)

    idx = {'Y_GROUP': 'HISP', 'Z_GROUP': 'WHITE', 'TOTAL': 'MEMBER', 'CATEGORY': 'FIPS', 'SUB_CAT': 'LEAID'}
    idxes = calc_idxes(year_range, idx)
    save_report(year_range, idxes, "hisp_" + args.outfile)

    idx = {'Y_GROUP': 'ASIAN', 'Z_GROUP': 'WHITE', 'TOTAL': 'MEMBER', 'CATEGORY': 'FIPS', 'SUB_CAT': 'LEAID'}
    idxes = calc_idxes(year_range, idx)
    save_report(year_range, idxes, "asian_" + args.outfile)

    idx = {'Y_GROUP': 'IND', 'Z_GROUP': 'WHITE', 'TOTAL': 'MEMBER', 'CATEGORY': 'FIPS', 'SUB_CAT': 'LEAID'}
    idxes = calc_idxes(year_range, idx)
    save_report(year_range, idxes, "native_amer_" + args.outfile)

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



