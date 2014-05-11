#!/usr/bin/env python
"""
Download all the NCES Data and the file format information and merge it into 
UTF-8 txt files.

Usage:
   ./nces_get.py

"""
from subprocess import call

# ==============================================================================
# Filelist
# See the filelist here:
#    http://nces.ed.gov/ccd/pubschuniv.asp
#
# Note that the files are split and later files have a version in the filename
# ==============================================================================
web_addr = "http://nces.ed.gov/ccd/data/zip/"
layout_web_addr = "http://nces.ed.gov/ccd/data/txt/"
splits = ['ai', 'kn', 'ow']

zip_ext = "_dat.zip"
new_zip_ext = "_txt.zip"
txt_ext = ".txt"
dat_ext = ".DAT"

old_format = "psu%02d%s"
old_layout_format = "psu%02dlay.txt"
split_old_format_years = range(86, 98)

new_format = "sc%02d%s%s"
new_layout_format = "psu%02d%slay.txt"
split_new_format_years = [98, 99, 0, 1, 2, 3, 4, 5, 6]
split_new_format_ver = ['1c', '1b', '1a', '1a', '1a', '1a', '1b', '1a', '1c']

new_format_years = range(7, 12)
new_format_ver = ['1b', '1b', '2a', '2a', '1a']

special_years = [94, 95, 96, 97, 2, 3]
special_filenames = {
        94:    ['SCH94AI.DAT', 'SCH94KN.DAT', 'SCH94OW.DAT'],
        95:    ['SCHL95AI.DAT', 'SCHL95KN.DAT', 'SCHL95OW.DAT'],
        96:    ['sch96ai.dat', 'sch96kn.dat', 'sch96ow.dat'],
        97:    ['PSU97AI.DAT', 'PSU97KN.DAT', 'PSU97OW.DAT'],
        2:     ['Sc021aai.txt', 'Sc021akn.txt', 'Sc021aow.txt'],
        3:     ['sc031aai.txt', 'sc031akn.txt', 'sc031aow.txt']
    }


# ==============================================================================
# Download the files
# ==============================================================================
# --------------------------------------
# Call wget
# --------------------------------------
def download(addr):
    call(["wget", addr])

# --------------------------------------
# Unzip
# --------------------------------------
def unzip(filename):
    """
    Unzip and remove the zip file
    """
    call(["unzip", filename])
    call(["rm", filename])

# --------------------------------------
# Construct the final filename
# --------------------------------------
def get_unzip_filenames(year, filenames):
    if year in special_filenames.keys():
        return special_filenames[year]
    else:
        return filenames

# --------------------------------------
# Merge
# --------------------------------------
def merge(year, filenames, dest):
    filenames = get_unzip_filenames(year, filenames)
    try:
        fout = open(dest, 'wb')
        for file in filenames:
            fin = open(file, 'rb')
            for line in fin:
                fout.write(line.decode('latin1').encode('utf-8'))
            fin.close()
        fout.close()

        # Delete the split files
        call(["rm"] + filenames)
    except IOError:
        print "Cannot find files: ", filenames

# --------------------------------------
# Rename
# --------------------------------------
def utf8_encode(src, dest):
    """
    For non-split datafiles, re-encode to UTF-8 to fit our conventions
    """
    try:
        fin = open(src, 'rb')
        fout = open(dest, 'wb')
        for line in fin:
            fout.write(line.decode('latin1').encode('utf-8'))
        fin.close()
        fout.close()
        call(["rm"] + [src])
    except IOError:
        print "Cannot find file: ", src

# --------------------------------------
# Construct the final filename
# --------------------------------------
def std_data_filename(year):
    return "nces%02d-%02d.txt" % (year, (year+1)%100)

def std_layout_filename(year):
    return "nces%02d-%02d_layout.txt" % (year, (year+1)%100)

# --------------------------------------
# Download and Process Routines
# --------------------------------------
def get_layout_files():
    for year in split_old_format_years:
        layout_filename = old_layout_format % (year)
        download(layout_web_addr + layout_filename)  # Layout file
        utf8_encode(layout_filename, std_layout_filename(year))

    for i, year in enumerate(split_new_format_years):
        if year > 50 or year < 2:
            layout_filename = old_layout_format % (year)
        else:
            layout_filename = new_layout_format % (year, split_new_format_ver[i])
        download(layout_web_addr + layout_filename)
        utf8_encode(layout_filename, std_layout_filename(year))

    for i, year in enumerate(new_format_years):
        layout_filename = new_layout_format % (year, new_format_ver[i])
        download(layout_web_addr + layout_filename)
        utf8_encode(layout_filename, std_layout_filename(year))

# --------------------------------------
# Download the files
# --------------------------------------
def get_data_files():
    for year in split_old_format_years:
        for split in splits:
            filename = old_format % (year, split)
            download(web_addr + filename + zip_ext)

    for i, year in enumerate(split_new_format_years):
        for split in splits:
            filename = new_format % (year, split_new_format_ver[i], split)
            download(web_addr + filename + zip_ext)

    for i, year in enumerate(new_format_years):
        filename = new_format % (year, new_format_ver[i], "")
        download(web_addr + filename + new_zip_ext)

# --------------------------------------
# Unzip, Encode and Rename the files
# --------------------------------------
def cleanup_files():
    for year in split_old_format_years:
        filenames = []
        for split in splits:
            filename = old_format % (year, split)
            filenames.append(filename + txt_ext)
            unzip(filename + zip_ext)
        merge(year, filenames, std_data_filename(year))

    for i, year in enumerate(split_new_format_years):
        filenames = []
        for split in splits:
            filename = new_format % (year, split_new_format_ver[i], split)
            filenames.append(filename + dat_ext)
            unzip(filename + zip_ext)
        merge(year, filenames, std_data_filename(year))

    for i, year in enumerate(new_format_years):
        filename = new_format % (year, new_format_ver[i], "")
        unzip(filename + new_zip_ext)
        utf8_encode(filename + txt_ext, std_data_filename(year))

# *****************************************************************************
# -------------------------------------
# Print the Usage
# -------------------------------------
def usage():
    print __doc__

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    get_layout_files()
    get_data_files()
    cleanup_files()
