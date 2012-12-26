#!/usr/bin/env python
"""
Parse the NCES Data File Format Doc and create parsing instructions for the main file
"""

import argparse
import re
import os
import csv

# Unit testing
import unittest

# ==============================================================================
# Constants and RegEx
# ==============================================================================
re_idx_header = re.compile(r'Name\s+Order\s+Type\s+Description')

# Name    Type   Position  Size  Description
re_definition = re.compile(r'^(\w+)\s+(\w+)\s+(\d+)[-](\d+)\s+(\d+)[*]?\s+(.*)$')
re_sub_definition = re.compile(r'^\s*[+](\w+)\s+(\w+)\s+(\d+)[-](\d+)\s+(\d+)\s+(.*)$')

# Variable    Start   End     Field   Data
# Name        Pos.    Pos.    Length  Type    Description
re_alt_definition = re.compile(r'^(\w+)\s+(\d+)\s+(\d+)\s+(\d+)*?\s+(\w+)\s+(.*)$')
re_alt_sub_definition = re.compile(r'^\s*[+](\w+)\s+(\d+)\s+(\d+)\s+(\d+)*?\s+(\w+)\s+(.*)$')

# Index Data Format
# Variable             Data
# Name          Order  Type   Description
re_idx_definition = re.compile(r'^[+]?(\w+)\s+(\d+)[*]?\s+(\w+)\s+(.*)$')

datafile_name = "nces%02d-%02d.txt"
formatfile_name = "nces%02d-%02d_layout.txt"

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
    def __init__(self, year=None, formatfile="", debug=False):
        self.debug = debug
        self.parse_instr = []
        self.header_count = 0
        self.headers = []
        self.descriptions = {}
        self.index_mode = 0
        self.save_names = [
            "FIPS",
            "BLACK",
            "HISP",
            "ASIAN",
            "AM",
            "WHITE",
            "MEMBER",
            "FRELCH",
            "GSHI",
            "GSLO",
            "LEAID",
            "LEANM"
        ]

        if year:
            self.year = year
            self.formatfile = self.get_formatfile_name()
        else:
            self.formatfile = formatfile
            self.year = 0
        # Load the network
        self.read_formatfile(self.formatfile)

    def __repr__(self):
        results = ""
        for instr in self.parse_instr:
            if self.index_mode:
                results += "Name:  %s, Index: %d\n" % (instr[0], instr[2])
            else:
                results += "Name:  %s, Size: %d\n" % (instr[0], instr[3] - instr[2] + 1)
        return results

    # --------------------------------------
    def get_formatfile_name(self):
        return self.get_filename(formatfile_name)

    # --------------------------------------
    def get_datafile_name(self):
        return self.get_filename(datafile_name)

    # --------------------------------------
    def get_filename(self, name_str):
        """
        Construct a filename from the base name, a year and
        the local directory structure.
        """
        fname = name_str % (self.year%100, (self.year+1)%100)
        this_dir, this_filename = os.path.split(__file__)
        fname = os.path.join(this_dir, 'data', fname)
        return fname

    # ==============================================================================
    # Read the Format file into a usable data structure
    # ==============================================================================
    # --------------------------------------
    def read_formatfile(self, formatfile):
        if self.debug:
            print "=" * 80
            print "Reading Format File:  %s" % formatfile
            print "=" * 80
        fh = open(formatfile, 'rb')

        for line in fh:
            if re_idx_header.search(line):
                if self.index_mode == 0:
                    print "Switching to Index MODE!!!"
                    self.index_mode = 1

            if re_definition.search(line):
                col_name, type, loidx, hiidx, size, description = re_definition.search(line).groups()
            elif re_sub_definition.search(line):
                col_name, type, loidx, hiidx, size, description = re_sub_definition.search(line).groups()
            elif re_alt_definition.search(line):
                col_name, loidx, hiidx, size, type, description = re_alt_definition.search(line).groups()
            elif re_alt_sub_definition.search(line):
                col_name, loidx, hiidx, size, type, description = re_alt_sub_definition.search(line).groups()
            elif self.index_mode and re_idx_definition.search(line):
                col_name, loidx, type, description = re_idx_definition.search(line).groups()
                hiidx = loidx
                size = 0
            else:
                if self.debug:
                    print line
                continue

            # Filter out a problematic NCES year to year changes
            if col_name == "FIPST":
                col_name = "FIPS"
                type = 'N'
            if col_name == "FIPS":
                type = 'N'
            if col_name == "FRE%02d" % (self.year%100):
                col_name = "FRELCH"
            if col_name == ("IND%02d" % (self.year%100)):
                col_name = "AM"
            elif col_name == "IND":
                col_name = "AM"

            self.add_instr(col_name, type, loidx, hiidx, size, description)

        if self.debug:
            print "=" * 80
            print "Format File Parsing Complete"
            print "=" * 80
            import pprint
            pprint.pprint(self.parse_instr)
            print "=" * 80
            print "\n"

    # --------------------------------------
    def add_instr(self, col_name, type, loidx, hiidx, size, description):
        if self.debug:
            print "Found Column:  %s - %s" % (col_name, size)

        # Strip the year off the column if it is present
        # We store the year in the main data object
        if col_name[-2:].isdigit():
            col_name = col_name[:-2]

        # Is it a number?
        if type == 'N':
            pass

        if col_name in self.save_names:
            self.parse_instr.append((col_name, type, int(loidx)-1, int(hiidx), description.strip()))
            self.add_column(col_name, description)

    # --------------------------------------
    def add_column(self, col_name, description):
        self.headers.append(col_name)
        desc = description.strip().split('\t')[0]   # Filter out any Tab characters
        self.descriptions[col_name] = desc
        self.header_count += 1

    # --------------------------------------
    def get_headers(self):
        return ",".join(self.header.keys())

    # --------------------------------------
    def get_idx(self, col_name):
        for i, name in enumerate(self.headers):
            if name == col_name:
                return i
        raise Exception("Invalid Column Name:  %s" % col_name)

    # --------------------------------------
    def get_descriptions(self):
        return ",".join(self.descriptions)

    # --------------------------------------
    def parse_line(self, line):
        entry = []
        for instr in self.parse_instr:
            if self.index_mode:
                field = line[instr[2]]
            else:
                field = line[instr[2]:instr[3]]   # Python array slicing rules  low_idx : high_idx + 1
            if self.debug:
                print field
            if instr[1] == 'N':   # Number Type
                try:
                    field = int(field)
                except ValueError:
                    field = 0    # Squash invalid values to 0 for fields of type 'Number'
            else:
                field.strip()    # Otherwise clean up the string
            entry.append(field)

        return entry

    # --------------------------------------
    def parse(self, datafile="", make_dict=False):

        if datafile:
            fname = datafile
        else:
            fname = self.get_datafile_name()
        fh = open(fname, 'rb')
        if self.index_mode:
            fh = csv.reader(fh, dialect='excel-tab')
            line = fh.next() # Pop the header line

        self.schools = []
        for line in fh:
            if make_dict:
                self.schools.append(self.make_dict(self.parse_line(line)))
            else:
                self.schools.append(self.parse_line(line))

        if self.debug:
            print len(self.schools)
        return self.schools

    # --------------------------------------
    def make_dict(self, school):
        if self.debug:
            print school
        return dict(zip(self.headers, school))

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
    parser = argparse.ArgumentParser(description='NCES Data File Parser')
    parser.add_argument('--year', action='store', dest='year', required=False, type=int,
            help='NCES Data Year - Standard filenames assumed')
    parser.add_argument('--formatfile', action='store', dest='formatfile', required=False,
            help='NCES Data File Record Layout')
    parser.add_argument('--datafile', action='store', dest='datafile', required=False,
            help='NCES Data File')
    parser.add_argument('-debug', action='store_true',
            help='Print Debug Messages')
    args = parser.parse_args()
    # print args

    # -------------------------------------
    # Actually do the work we intend to do here
    # -------------------------------------
    if args.year:
        parse = NCESParser(year=args.year, debug=args.debug)
    elif args.formatfile:
        parse = NCESParser(formatfile=args.formatfile, debug=args.debug)
    else:
        raise Exception("Please select a year or an NCES Record Layout file name")

    print "=" * 80
    print parse
    print "=" * 80
    print parse.get_idx('GSHI')

    if args.year:
        schools = parse.parse()
    elif args.formatfile:
        schools = parse.parse(args.datafile)
    else:
        raise Exception("Please define a year when constructing or specify an NCES Datefile Layout file name")

    print "=" * 80
    print len(schools)

    print "=" * 80
    print schools[0]
    print schools[22000]
    import pprint
    pprint.pprint(parse.make_dict(schools[22000]))

    print "=" * 80
    print "Headers"
    print "=" * 80
    print parse.headers

    print "=" * 80
    print "Descriptions"
    print "=" * 80
    pprint.pprint(parse.descriptions)



# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main()


