# School Segregation Data Analysis Tools

Writen in support of the following paper:

    http://gradworks.umi.com/36/09/3609993.html

The tools provide a way to dig through NCES data on student enrollment at public
schools and measure the level of segregation at the district or state level over time.

# Installation
I haven't packaged it yet, so just clone the repo

    git clone https://github.com/blargony/segrete


# Overview

The toolset isn't very organized, but here is a quick summary to get you started.

First thing, run this script:
* data/nces_get.py - Downloads data files from the NCES.

Note: It may need to be updated if the NCES changed the latest version of it's data
and if new years of data are available.   After running the script, you will have a
local copy of the available NCES data (School level common core dataset)

Next run this script:
* nces_parser.py - Sorts through the NCES Data and creates local caches of a subset of the data.

Depending on the options, you will end up with a reduced set of data that you can use
for running other checks.

These scripts and others allow various reports to be generated:
* segrete.py - generates a variety of segregation reports
* segcalc.py - does the heavy lifting on the math (not exactly heavy mind you)
