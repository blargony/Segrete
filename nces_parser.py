#!/usr/bin/env python
"""
Parse the NCES Data File Format Doc and create parsing instructions for the main file
"""

import argparse
import re
import os
import csv
import pickle

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
saved_datafile_name = "nces%02d-%02d.csv"
pickle_datafile_name = "nces%02d-%02d.pk"
formatfile_name = "nces%02d-%02d_layout.txt"

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
            "LEAID",
            "LEANM",
            "SCHNAM",
            "CITY",
            "ST",
            "BLACK",
            "HISP",
            "ASIAN",
            "AM",
            "WHITE",
            "MEMBER",
            "FRELCH",
            "GSHI",
            "GSLO"
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
    def get_saved_datafile_name(self):
        return self.get_filename(saved_datafile_name)

    # --------------------------------------
    def get_pickle_datafile_name(self):
        return self.get_filename(pickle_datafile_name)

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
            if col_name == "LEAID":
                type = 'AN'

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
        return self.headers

    # --------------------------------------
    def get_idx(self, col_name):
        try:
            return self.name_idx_dict[col_name]
        except AttributeError:
            self.name_idx_dict = {}
            for i, name in enumerate(self.headers):
                self.name_idx_dict[name] = i
            return self.name_idx_dict[col_name]

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
                field = field.strip()    # Otherwise clean up the string
            entry.append(field)

        return entry

    # --------------------------------------
    def parse_orig(self, datafile="", make_dict=False):
        if datafile:
            fname = datafile
        else:
            fname = self.get_datafile_name()

        fh = open(fname, 'rb')
        if self.index_mode:
            fh = csv.reader(fh, dialect='excel-tab')
            line = fh.next() # Pop the header line

        skip_count = 0
        self.schools = []
        for line in fh:
            if make_dict:
                school = self.make_dict(self.parse_line(line))
                if int(school['FIPS']) in fips_to_st.keys():
                    self.schools.append(school)
                else:
                    skip_count += 1
            else:
                school = self.parse_line(line)
                if int(school[self.get_idx('FIPS')]) in fips_to_st.keys():
                    self.schools.append(school)
                else:
                    skip_count += 1

        if self.debug:
            print "Found %d Schools" % len(self.schools)
            print "Skipped %d Schools" % skip_count
        return self.schools


    # --------------------------------------
    def parse_saved(self, make_dict=False):

        saved_fname = self.get_saved_datafile_name()
        fh = open(saved_fname, 'rb')

        if make_dict:
            cfh = csv.DictReader(fh, quoting=csv.QUOTE_NONNUMERIC)
            self.headers = cfh.fieldnames
        else:
            cfh = csv.reader(fh, quoting=csv.QUOTE_NONNUMERIC)
            self.headers = cfh.next()

        self.schools = []
        for line in cfh:
            self.schools.append(line)

        if self.debug:
            print len(self.schools)
        return self.schools


    # --------------------------------------
    def parse(self, datafile="", make_dict=False, forced_orig=False):
        if forced_orig or datafile:
            return self.parse_orig(datafile, make_dict)
        else:
            pickle_fname = self.get_pickle_datafile_name()
            try:
                fh = open(pickle_fname, 'rb')
                print "Loading Pickled Data Set"
                self.schools = pickle.load(fh)
                return self.schools
            except IOError:
                pass

            saved_fname = self.get_saved_datafile_name()
            try:
                open(saved_fname, 'rb')
                print "Loading Previously Saved CSV Data Set"
                return self.parse_saved(make_dict)
            except IOError:
                print "Parsing the NCES Data Set"
                return self.parse_orig(datafile, make_dict)

    # --------------------------------------
    def make_dict(self, school):
        if self.debug:
            print school
        return dict(zip(self.headers, school))

    # --------------------------------------
    def save_parsed_data(self):
        """
        Save out the parsed data
        """
        fname = self.get_saved_datafile_name()

        fh = open(fname, 'wb')
        cfh = csv.writer(fh, quoting=csv.QUOTE_NONNUMERIC)
        cfh.writerow(self.get_headers())

        print "Saving %d Entries to CSV File %s" % (len(self.schools), fname)
        for school in self.schools:
            if self.debug:
                print school
            cfh.writerow(school)

    # --------------------------------------
    def pickle_data(self):
        """
        Save out the parsed data
        """
        fname = self.get_pickle_datafile_name()
        fh = open(fname, 'wb')
        print "Pickling %d Entries to .pk File %s" % (len(self.schools), fname)
        pickle.dump(self.schools, fh, pickle.HIGHEST_PROTOCOL)
        fh.close()

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
    parser.add_argument('-update_csv', action='store_true', dest='update_csv', required=False,
            help='Save a reduced CSV of the NCES Data File')
    parser.add_argument('-update_pk', action='store_true', dest='update_pk', required=False,
            help='Cache the parsed dataset to disk')
    parser.add_argument('-debug', action='store_true',
            help='Print Debug Messages')
    args = parser.parse_args()
    # print args

    # -------------------------------------
    # Actually do the work we intend to do here
    # -------------------------------------
    if args.update_csv:
        for year in range(1987, 2011):
            print "=" * 80
            print "Saving out a reduced dataset for %d" % year
            print "=" * 80
            parse = NCESParser(year=year, debug=args.debug)
            parse.parse(forced_orig=True)
            parse.save_parsed_data()
    elif args.update_pk:
        for year in range(1987, 2011):
            print "=" * 80
            print "Saving out a reduced dataset for %d" % year
            print "=" * 80
            parse = NCESParser(year=year, debug=args.debug)
            parse.parse(forced_orig=True)
            parse.pickle_data()
    else:
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


