#!/usr/bin/env python
"""
Pull together the NCES data and the Segragation index calculator to produce
some reports on segregation in the USA.
"""
import sys
import argparse
import operator

from segcalc import SegCalc
from nces_parser import NCESParser

from xlwt import Workbook

# ==============================================================================
# Constants
# ==============================================================================
fips_to_st = {
    '01': ('AL', 'Alabama'),
    '02': ('AK', 'Alaska'),
    '04': ('AZ', 'Arizona'),
    '05': ('AR', 'Arkansas'),
    '06': ('CA', 'California'),
    '08': ('CO', 'Colorado'),
    '09': ('CT', 'Connecticut'),
    '10': ('DE', 'Delaware'),
    '11': ('DC', 'District of Columbia'),
    '12': ('FL', 'Florida'),
    '13': ('GA', 'Georgia'),
    '15': ('HI', 'Hawaii'),
    '16': ('ID', 'Idaho'),
    '17': ('IL', 'Illinois'),
    '18': ('IN', 'Indiana'),
    '19': ('IA', 'Iowa'),
    '20': ('KS', 'Kansas'),
    '21': ('KY', 'Kentucky'),
    '22': ('LA', 'Louisiana'),
    '23': ('ME', 'Maine'),
    '24': ('MD', 'Maryland'),
    '25': ('MA', 'Massachusetts'),
    '26': ('MI', 'Michigan'),
    '27': ('MN', 'Minnesota'),
    '28': ('MS', 'Mississippi'),
    '29': ('MO', 'Missouri'),
    '30': ('MT', 'Montana'),
    '31': ('NE', 'Nebraska'),
    '32': ('NV', 'Nevada'),
    '33': ('NH', 'New Hampshire'),
    '34': ('NJ', 'New Jersey'),
    '35': ('NM', 'New Mexico'),
    '36': ('NY', 'New York'),
    '37': ('NC', 'North Carolina'),
    '38': ('ND', 'North Dakota'),
    '39': ('OH', 'Ohio'),
    '40': ('OK', 'Oklahoma'),
    '41': ('OR', 'Oregon'),
    '42': ('PA', 'Pennsylvania'),
    '44': ('RI', 'Rhode Island'),
    '45': ('SC', 'South Carolina'),
    '46': ('SD', 'South Dakota'),
    '47': ('TN', 'Tennessee'),
    '48': ('TX', 'Texas'),
    '49': ('UT', 'Utah'),
    '50': ('VT', 'Vermont'),
    '51': ('VA', 'Virginia'),
    '53': ('WA', 'Washington'),
    '54': ('WV', 'West Virginia'),
    '55': ('WI', 'Wisconsin'),
    '56': ('WY', 'Wyoming')
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
    print "Calculating High Isolation Students Percentage"
    per_idx = segcalc.calc_90()
    print "Calculating Total Minority Students"
    min_idx = segcalc.calc_totals(idx='Y_GROUP')
    print "Calculating Total Student Count"
    tot_idx = segcalc.calc_totals()
    print "Done with Calculations"
    return (exp_idx, iso_idx, dis_idx, per_idx, min_idx, tot_idx)

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
    per = wb.add_sheet('High Isolation Index')
    min = wb.add_sheet('Minority Student Count')
    size = wb.add_sheet('Student Count')

    worksheets = [ews, iws, dws, per, min, size]

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

# ======================================
def sch_type_report(schools, cat_idx):
    """
    Report on school counts and student population for the various
    school types (Magnet, Charter, etc...)
    """
    counts_dict = {}
    for school in schools:
        try:
            charter = school['CHARTR']
            magnet = school['MAGNET']
            ti = school['MEMBER']
            try:
                ti = int(ti)
            except ValueError:
                ti = 0

            try:
                charter = int(charter)
            except ValueError:
                charter = 0
            try:
                magnet = int(magnet)
            except ValueError:
                magnet = 0
        except KeyError:
            raise Exception("Problem School:",school.__repr__())

        # Make sure the datastructure exists
        try:
            test = counts_dict[school[cat_idx]]
        except KeyError:
            counts_dict[school[cat_idx]] = dict(charter=0, magnet=0, other=0, charter_st=0, magnet_st=0, other_st=0, all=0)

        # Negative numbers mean missing data.
        if ti > 0:
            counts_dict[school[cat_idx]]['all'] += ti
            if int(charter) == 1:
                counts_dict[school[cat_idx]]['charter'] += 1
                counts_dict[school[cat_idx]]['charter_st'] += ti
            elif int(magnet) == 1:
                counts_dict[school[cat_idx]]['magnet'] += 1
                counts_dict[school[cat_idx]]['magnet_st'] += ti
            else:
                counts_dict[school[cat_idx]]['other'] += 1
                counts_dict[school[cat_idx]]['other_st'] += ti

    
    counts = []
    for items in counts_dict.iteritems():
        entry = [items[0]]
        entry.append(items[1]['all'])
        entry.append(items[1]['other'])
        entry.append(items[1]['other_st'])
        entry.append(items[1]['charter'])
        entry.append(items[1]['charter_st'])
        entry.append(items[1]['magnet'])
        entry.append(items[1]['magnet_st'])
        counts.append(entry)
    counts_by_size = sorted(counts, key=operator.itemgetter(1), reverse=True)
    return counts_by_size

# -------------------------------------
def save_sch_report(results, count, category_lut, filename):
    """
    Report will be a 2D matrix:
        - X-Axis = School Type and Students Served Counts
        - Y-Axis = 'Category' (FIPS Code, District, etc...)

    Notes:
        - idxes contains the data
        - worksheets is a list of XLS worksheets, one per report in idxes
    """
    wb = Workbook()
    sch_types = wb.add_sheet('School Types')

    # Create the headers/labels row/col
    sch_types.write(0, 0, "Agency Name")
    sch_types.write(0, 1, "State")
    sch_types.write(0, 2, "Total Students")
    sch_types.write(0, 3, "Regular School Count")
    sch_types.write(0, 4, "Regular School Student Population")
    sch_types.write(0, 5, "Charter School Count")
    sch_types.write(0, 6, "Charter School Student Population")
    sch_types.write(0, 7, "Magnet School Count")
    sch_types.write(0, 8, "Magnet School Student Population")

    # Print out the data
    offset = 1
    for j, result in enumerate(results):
        if j < count:
            sch_types.write(offset+j, 0, category_lut[result[0]])
            sch_types.write(offset+j, 1, fips_to_st[result[0][:2]][0])
            sch_types.write(offset+j, 2, result[1])
            sch_types.write(offset+j, 3, result[2])
            sch_types.write(offset+j, 4, result[3])
            sch_types.write(offset+j, 5, result[4])
            sch_types.write(offset+j, 6, result[5])
            sch_types.write(offset+j, 7, result[6])
            sch_types.write(offset+j, 8, result[7])
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
    parser.add_argument('-sch_count', action='store_true', dest='sch_count', required=False,
            help='Debug Mode')
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

    if args.sch_count:
        # Count of schools and charters and what not
        nces = NCESParser(year=2010)
        schools = nces.parse(make_dict=True)
        results = sch_type_report(schools, category)

        # Get some information for reporting
        segcalc = SegCalc(schools, idx)
        if category == 'LEAID':
            category_lut = segcalc.get_idxed_val('LEAID', 'LEANM')
        elif category == 'FIPS':
            category_lut = dict(zip(fips_to_st.keys(), [fips_to_st[key][0] for key in fips_to_st.keys()]))

        save_sch_report(
            results,
            report_count,
            category_lut,
            'school_type_' + args.outfile
        )

    else:
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
                exp,iso,dis,per,min,tot = calc_idxes(segcalc)
                print "Finished Performing Calculations on Data from:  %d" % year

                print "Appending Yearly Data"
                idxes[0].append(exp)
                idxes[1].append(iso)
                idxes[2].append(dis)
                idxes[3].append(per)
                idxes[4].append(min)
                idxes[5].append(tot)

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



