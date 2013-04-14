#!/usr/bin/env python
"""
Do some linear regression on NCES Data
"""
import sys
import argparse
import operator

from nces_parser import NCESParser
from segcalc2 import SegCalc

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

# ==============================================================================
# Constants
# ==============================================================================
# Maximum number of rows to report in an output file.
MAX_RECORD = 1000

# ==============================================================================
# Functions
# ==============================================================================
def find_big_dist():
    pass

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
        minority = args.minority
    else:
        minority = 'BLACK'

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
    segcalc = SegCalc(schools, region)
    if args.filter_idx:
        segcalc.add_filter('cmdline', args.filter_idx, [args.filter_list])

    # --------------------------------------
    # Now what we need are:
    #   Proportion of Students that are BLACK
    #   Dissimiliarity index between BLACK and WHITE students
    #    (For 100 largest districts only)
    #
    #   List of districts with high levels of 'choice'
    # --------------------------------------
    # Get 100 largest districts
    total_count = segcalc.calc_total('MEMBER')
    total_by_size = sorted(total_count.iteritems(), key=operator.itemgetter(1), reverse=True)
    big_districts = zip(*total_by_size)[0]
    # segcalc.add_filter('bigdistrict', region, big_districts[:MAX_RECORD])

    total = 0.0
    for dist in big_districts[:MAX_RECORD]:
        total += total_count[dist]
    print "Total Students Covered by %d Districts:   %d" % (MAX_RECORD, total)

    # --------------------------------------
    # Urban vs Rural Test - we want Urban
    # --------------------------------------
    urbanicity_totals = {}
    for school in schools:
        # if school[region] in big_districts[:MAX_RECORD]:
        local = school['ULOCAL']
        if local[0] == '1':
            try:
                urbanicity_totals[school[region]] += 1
            except KeyError:
                urbanicity_totals[school[region]] = 1

    for key in urbanicity_totals.keys():
        if urbanicity_totals[key] < 10:
            urbanicity_totals.pop(key)
    import pprint
    pprint.pprint(urbanicity_totals)
    print len(urbanicity_totals)
    segcalc.add_filter('citydistrict', region, urbanicity_totals.keys())

    # --------------------------------------
    # Get districts with lots of 'choice'
    # --------------------------------------
    choice_total = {}
    for school in schools:
        # if school[region] in big_districts[:MAX_RECORD]:
        if school[region] in urbanicity_totals.keys():
            if (
                school['CHARTR'] == '1' or
                school['MAGNET'] == '1'
            ):
                head_count = int(school['MEMBER'])
                if head_count < 0:
                    head_count = 0
            else:
                head_count = 0
            try:
                choice_total[school[region]] += head_count
            except KeyError:
                choice_total[school[region]] = head_count

    total_count = segcalc.calc_total('MEMBER')
    print len(total_count)
    choice_prop = segcalc.calc_prop(choice_total, total_count)
    print len(choice_prop)

    # --------------------------------------
    # Get Minority Proportion and Minority/WH dissimilarity
    # min_count = segcalc.calc_total(minority)
    aa_count = segcalc.calc_total('BLACK')
    hisp_count = segcalc.calc_total('HISP')
    min_count = segcalc.calc_sum (aa_count, hisp_count)

    min_prop = segcalc.calc_prop(min_count, total_count)
    print len(min_prop)
    # Dissimilarity index call
    min_wh_dis = segcalc.calc_dis_idx(minority, 'WHITE', 'MEMBER')

    # -------------------------------------
    # Linear Regression - Fit a line
    #  Proportion of Black Students vs Black/White Dissimilarity
    #  y = Black/White Dis
    #  x = Prop Black
    #  y = mx+c - m, c to be computed
    # -------------------------------------
    min_prop_list = []
    min_wh_dis_list = []
    choice_min_prop_list = []
    choice_min_wh_dis_list = []
    for key in min_prop.keys():
        if choice_prop[key] < 0.3:
            min_prop_list.append(min_prop[key])
            min_wh_dis_list.append(min_wh_dis[key])
        else:
            choice_min_prop_list.append(min_prop[key])
            choice_min_wh_dis_list.append(min_wh_dis[key])
            print min_prop[key]

    x = np.array(min_prop_list)
    y = np.array(min_wh_dis_list)
    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y)[0]

    choice_x = np.array(choice_min_prop_list)
    choice_y = np.array(choice_min_wh_dis_list)
    choice_A = np.vstack([choice_x, np.ones(len(choice_x))]).T
    choice_m, choice_c = np.linalg.lstsq(choice_A, choice_y)[0]
    print m
    print c

    fig = plt.figure()
    plot = fig.add_subplot(1,1,1)
    plot.plot(x, y, 'bo', label='Original data', markersize=3)
    plot.plot(choice_x, choice_y, 'r+', label='Original data', markersize=5)
    plot.plot(x, m*x + c, 'b', label='Fitted line')
    plot.plot(choice_x, choice_m*choice_x + choice_c, 'r', label='Fitted line')

    """
    plot.annotate(
        'Detroit City District', xy=(0.09, 0.69), xytext=(0.14, 0.65),
        arrowprops=dict(facecolor='black', shrink=0.1, width=1, headwidth=4),
    )
    """
    minority = "Black/Hisp"
    plot.set_xlabel('Proportion of %s Students' % minority.title())
    # plt.set_title("")
    plot.set_ylabel('%s/White Dissimilarity Index' % minority.title())
    # plot.legend()
    fig.savefig(args.imgfile)
    plt.show()

    # slope, intercept, r_value, p_value, std_err = sp.stats.linregress(x,y)
    print stats.linregress(x,y)

    min_prop_list = []
    choice_list = []
    for key in min_prop.keys():
        if choice_prop[key] > 0.01:
            min_prop_list.append(min_prop[key])
            choice_list.append(choice_prop[key])

    x = np.array(min_prop_list)
    y = np.array(choice_list)
    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y)[0]

    fig = plt.figure()
    plot = fig.add_subplot(1,1,1)
    plot.plot(x, y, 'bo', label='Original data', markersize=3)
    plot.plot(x, m*x + c, 'b', label='Fitted line')
    plot.set_xlabel('Proportion of %s Students' % minority.title())
    # plt.set_title("")
    plot.set_ylabel('Proportion of Students Enrolled in Charter/Magnet Schools')
    # plot.legend()
    fig.savefig(args.imgfile)
    plt.show()


 
# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



