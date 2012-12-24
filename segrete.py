#!/usr/bin/env python
"""
Pull together the NCES data and the Segragation index calculator to produce
some reports on segregation in the USA.
"""
import sys
import argparse

from segcalc import SegCalc
from nces_parser import NCESParser

# ==============================================================================
# Constants
# ==============================================================================

# ==============================================================================
# Utility Functions
# ==============================================================================


# -------------------------------------
# Parse the command line options
# -------------------------------------
def main(argv):
    parser = argparse.ArgumentParser(description='Segregation Report Generator')
    parser.add_argument('--year', action='store', dest='year', required=False, type=int,
            help='NCES Data Year')
    parser.add_argument('--output', action='store', dest='output', required=False,
            help='Report File')

    # Get our dataset ready
    nces = NCESParser(year=1998)
    print nces
    schools = nces.parse(make_dict=True)

    # Dig into the dataset based on
    idx = {'Y_GROUP': 'BLACK', 'Z_GROUP': 'WHITE', 'TOTAL': 'MEMBER', 'CATEGORY': 'FIPS', 'SUB_CAT': 'LEAID'}
    sg = SegCalc(schools, idx)
    print sg.calc_exp_idx()
    print sg.calc_iso_idx()

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



