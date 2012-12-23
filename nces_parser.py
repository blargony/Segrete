#!/usr/bin/env python
"""
Parse the NCES Data File Format Doc and create parsing instructions for the main file
"""

import argparse
import re
import csv

# Unit testing
import unittest

# ==============================================================================
# Constants and RegEx
# ==============================================================================
# resistor_name ([node_name] [node_name]) resistor r=[resistance_value] c=0
re_definition = re.compile(r'^(\w+)\s+(\w+)\s+(\d+)[-](\d+)\s+(\d+)*?\s+(.*)$')
re_sub_definition = re.compile(r'^\s*[+](\w+)\s+(\w+)\s+(\d+)[-](\d+)\s+(\d+)\s+(.*)$')

# ==============================================================================
# Utility Functions
# ==============================================================================
# --------------------------------------
def strip_comment(line, comment_char='#'):
    """
    Strip inline comments - 
    """
    idx = line.find(comment_char)
    if idx != -1:
        line = line[:idx]
    return line.strip()

# --------------------------------------
def longlines(rawdata):
    """
    Generator to merge lines in a text file that end with a "\"
    """
    lines = []
    for i in rawdata.splitlines():
        if i.endswith("\\"):
            lines.append(i.rstrip("\\"))
        else:
            lines.append(i)
            yield "".join(lines)
            lines = []
    if len(lines) > 0: yield "".join(lines)

# ==============================================================================
# Parser Class
# ==============================================================================
class NCESParser(object):
    """
    Parsing Instructions for an NCES data file.

    The instructions consist of list of columns in the database along
    with information needed to pull the column from the file.  Typically
    it will be a string index:

        [('COLUMN_NAME', idx), ('COLUMN_NAME', idx), ...]

    """
    def __init__(self, formatfile, debug=False):
        self.debug = debug
        self.parse_instr = []
        self.header_count = 0
        self.headers = {}
        self.descriptions = {}

        # Load the network
        self.read_formatfile(formatfile)

    def __repr__(self):
        results = ""
        for instr in self.parse_instr:
            results += "Name:  %s, Size: %d\n" % (instr[0], instr[3] - instr[2] + 1)
        return results

    # ==============================================================================
    # Read the Format file into a usable data structure
    # ==============================================================================
    # --------------------------------------
    def read_formatfile(self, formatfile):
        if self.debug:
            print "=" * 80
            print "Reading Format File:  %s" % formatfile
            print "=" * 80
        netlist = open(formatfile).read()

        for line in longlines(netlist):
            if re_definition.search(line):
                self.add_instr(re_definition.search(line).groups())
            elif re_sub_definition.search(line):
                self.add_instr(re_sub_definition.search(line).groups())
            else:
                print line
                continue

        if self.debug:
            print "=" * 80
            print "Format File Parsing Complete"
            print "=" * 80
            import pprint
            pprint.pprint(self.parse_instr)
            print "=" * 80
            print "\n"

    # --------------------------------------
    def add_instr(self, search_groups):
        col_name, type, loidx, hiidx, size, description = search_groups
        if self.debug:
            print "Found Column:  %s - %s" % (col_name, size)

        # Strip the year off the column if it is present
        # We store the year in the main data object
        if col_name[-2:].isdigit():
            col_name = col_name[:-2]

        # Is it a number?

        self.parse_instr.append((col_name, type, int(loidx)-1, int(hiidx), description.strip()))
        self.add_column(col_name, description)

    # --------------------------------------
    def add_column(self, col_name, description):
        self.headers[col_name] = self.header_count
        desc = description.strip().split('\t')[0]   # Filter out any Tab characters
        self.descriptions[col_name] = desc
        self.header_count += 1

    # --------------------------------------
    def get_header(self):
        return ",".join(self.header.keys())

    # --------------------------------------
    def get_idx(self, col_name):
        return self.headers[col_name]

    # --------------------------------------
    def get_descriptions(self):
        return ",".join(self.descriptions)

    # --------------------------------------
    def parse(self, line):
        if self.debug:
            print line

        entry = {}
        for instr in self.parse_instr:
            sub_str = line[instr[2]:instr[3]]   # Python array slicing rules  low_idx : high_idx + 1
            if self.debug:
                print sub_str
            entry[instr[0]] = sub_str.strip()
        return entry
 
# *****************************************************************************
# Unit Tests
# *****************************************************************************
class TestBasicNetwork(unittest.TestCase):

    def setUp(self):
        self.parse = NCESParser('data/school.test', 'data/school.format')

    def test_old_style(self):
        self.assertEqual(self.parse.something, ["Test"])

# *****************************************************************************
# Program Flow
# *****************************************************************************
# -------------------------------------
# Parse the command line options
# -------------------------------------
def main():
    parser = argparse.ArgumentParser(description='Extracted Parasitic Capacitance netlist analyzer')
    parser.add_argument('--formatfile', action='store', dest='formatfile', required=True,
                        help='Input Netlist File')
    parser.add_argument('--datafile', action='store', dest='datafile', required=True,
                        help='Input Netlist File')
    parser.add_argument('-debug', action='store_true',
                       help='Print Debug Messages')
    args = parser.parse_args()
    # print args

    # -------------------------------------
    # Actually do the work we intend to do here
    # -------------------------------------
    # NetworkX graph library routines
    parse = NCESParser(args.formatfile, args.debug)

    print "=" * 80
    print parse
    print "=" * 80

    fh = open(args.datafile, 'rb')
    line = fh.next()
    school = []
    for line in fh:
        school.append(parse.parse(line))
    print len(school)
    print school[0]
    print school[22000]

    print parse.headers
    print parse.descriptions

    print parse.get_idx('GSLO')


# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main()


