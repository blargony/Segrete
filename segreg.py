#!/usr/bin/env python
"""
Do some linear regression on NCES Data
"""
import sys
import argparse
import operator

from nces_parser import NCESParser
from segcalc import SegCalc
from fips import fips_to_st

from xlwt import Workbook

import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# Constants
# ==============================================================================
# Maximum number of rows to report in an output file.
MAX_RECORD = 100

# ==============================================================================
# Functions
# ==============================================================================

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
            raise KeyError("Problem School:",school.__repr__())

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
def save_sch_report(year_range, results, count, category_lut, filename):
    """
    Report will be a 2D matrix:
        - X-Axis = School Type and Students Served Counts
        - Y-Axis = 'Category' (FIPS Code, District, etc...)

    Notes:
        - idxes contains the data
        - worksheets is a list of XLS worksheets, one per report in idxes
    """
    wb = Workbook()
    sch_types = wb.add_sheet('School Counts')
    pop_perc = wb.add_sheet('Student Percentages')

    worksheets = [sch_types, pop_perc]

    y_offset = 2
    x_offset = 2

    # Create the headers/labels row/col
    sch_types.write(1, 0, "Agency Name")
    sch_types.write(1, 1, "State")

    # Headers
    for i, year in enumerate(year_range):
        print "Write Report for:  %d" % year
        for ws in worksheets:
            ws.write_merge(0, 0, (i*3)+x_offset, (i*3)+2+x_offset, year)

        sch_types.write(1, (i*3)+x_offset, "Regular School")
        sch_types.write(1, (i*3)+1+x_offset, "Charter School")
        sch_types.write(1, (i*3)+2+x_offset, "Magnet School")

        pop_perc.write(1, (i*3)+x_offset, "Regular School")
        pop_perc.write(1, (i*3)+1+x_offset, "Charter School")
        pop_perc.write(1, (i*3)+2+x_offset, "Magnet School")

        # Print out the data
        for j, result in enumerate(results[i]):
            if j < count:
                # Headers only on the first year
                if (i == 0):
                    sch_types.write(y_offset+j, 0, category_lut[result[0]])
                    sch_types.write(y_offset+j, 1, fips_to_st[result[0][:2]][0])
                sch_types.write(y_offset+j, (i*3)+2, result[2])
                sch_types.write(y_offset+j, (i*3)+3, result[4])
                sch_types.write(y_offset+j, (i*3)+4, result[6])

                # Headers only on the first year
                if (i == 0):
                    pop_perc.write(y_offset+j, 0, category_lut[result[0]])
                    pop_perc.write(y_offset+j, 1, fips_to_st[result[0][:2]][0])
                member_count = result[1]
                if member_count > 0:
                    pop_perc.write(y_offset+j, (i*3)+2, float(result[3])/member_count)
                    pop_perc.write(y_offset+j, (i*3)+3, float(result[5])/member_count)
                    pop_perc.write(y_offset+j, (i*3)+4, float(result[7])/member_count)

    wb.save(filename)


# -------------------------------------
# Parse the command line options
# -------------------------------------
def main(argv):
    parser = argparse.ArgumentParser(description='Segregation Linear Regression Generator')
    parser.add_argument('--imgfile', action='store', dest='imgfile', required=True,
            help='Report Filename')
    parser.add_argument('--region', action='store', dest='region', required=False,
            help='Which Category do we sort the results by?')
    parser.add_argument('--filter_idx', action='store', dest='filter_idx', required=False,
            help='Only use data points that filter some criterion')
    parser.add_argument('--filter_list', action='store', dest='filter_list', required=False,
            help='Value to filter when using --filter_idx')
    parser.add_argument('--minority', action='store', dest='minority', required=False,
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

    if args.region:
        region = args.region
    else:
        region = 'LEAID'

    # Override the default years/minorities per command line requests
    if args.minority:
        minorities = [args.minority]
    else:
        minorities = ['BLACK', 'HISP', 'FRELCH']

    if args.year:
        year = args.year
    else:
        year = 2010

    if args.max_record:
        report_count = int(args.max_record)
    else:
        report_count = MAX_RECORD

    # --------------------------------------
    # Load the Dataset
    # --------------------------------------
    nces = NCESParser(year=year)
    schools = nces.parse(make_dict=True)
    segcalc = SegCalc(schools, region, args.filter_idx, [args.filter_list])

    # --------------------------------------
    # Now what we need are:
    #   Proportion of Students that are BLACK
    #   Dissimiliarity index between BLACK and WHITE students
    #    (For 100 largest districts only)
    # --------------------------------------
    # Get 100 largest districts
    total_count = segcalc.calc_total('MEMBER')
    total_by_size = sorted(total_count.iteritems(), key=operator.itemgetter(1), reverse=True)
    big_districts = zip(*total_by_size)[0]
    segcalc.update_filter(region, big_districts[:100])

    # Get AA Proportion and AA/WH dissimilarity
    aa_count = segcalc.calc_total('BLACK')
    aa_prop = segcalc.calc_prop(aa_count, total_count)
    import pprint
    pprint.pprint(aa_prop)

    aa_wh_dis = segcalc.calc_dis_idx('BLACK', 'WHITE', 'MEMBER')
    # import pprint
    # pprint.pprint(aa_wh_dis)

    # -------------------------------------
    # Linear Regressoin - Fit a line
    #  Proportion of Black Students vs Black/White Dissimilarity
    #  y = Black/White Dis
    #  x = Prop Black
    #  y = mx+c - m, c to be computed
    # -------------------------------------
    aa_prop_list = []
    aa_wh_dis_list = []
    for key in aa_prop.keys():
        aa_prop_list.append(aa_prop[key])
        aa_wh_dis_list.append(aa_wh_dis[key])

    x = np.array(aa_prop_list)
    y = np.array(aa_wh_dis_list)
    A = np.vstack([x, np.ones(len(x))]).T
    # print A
    m, c = np.linalg.lstsq(A, y)[0]

    print m
    print c

    fig = plt.figure()
    plot = fig.add_subplot(1,1,1)
    plot.plot(x, y, 'o', label='Original data', markersize=10)
    plot.plot(x, m*x + c, 'r', label='Fitted line')

    plot.set_xlabel('Proportion of Black Students')
    # plt.set_title("")
    plot.set_ylabel('Black/White Dissimilarity Index')
    # plot.legend()
    fig.savefig(args.imgfile)
    # plt.show()

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



