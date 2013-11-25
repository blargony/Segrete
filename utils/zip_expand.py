#!/usr/bin/env python
import sys
import argparse

# ==============================================================================
# Constants
# ==============================================================================

# -------------------------------------
# Parse the command line options
# -------------------------------------
def main(argv):
    parser = argparse.ArgumentParser(description='Expand a List of ZIP Codes [12345-23455, 12355, ...]')
    parser.add_argument('--ziplist', action='store', dest='ziplist', required=True,
            help='Report Filename')
    parser.add_argument('-debug', action='store_true', dest='debug', required=False,
            help='Debug Mode')
    args = parser.parse_args()

    fh = open(args.ziplist, 'rb')
    
    zip_list = fh.readlines()
    zip_list = ''.join(zip_list)
    udata=zip_list.decode("utf-8")
    zip_list=udata.encode("ascii","replace")
    print zip_list

    zips = []
    for zip in zip_list.split(','):
        zip = zip.strip()
        if '?' in zip:
            first, last = zip.split('?')
            first = first.strip()
            last = last.strip()
            for i in range(int(first), int(last)):
                zips.append(i)
        else:
            zips.append(int(zip))
    print zips

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



