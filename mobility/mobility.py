#!/usr/bin/env python
"""
Quick script to generate several summaries for a list of cities
"""
from subprocess import call
import fips

cities = [
    ('San Jose', 'CA'),
    ('San Francisco', 'CA'),
    ('Washington', 'DC'),
    ('Seattle', 'WA'),
    ('Salt Lake City', 'UT'),
    ('Indianapolis', 'IN'),
    ('Dayton', 'OH'),
    ('Atlanta', 'GA'),
    ('Milwaukee', 'WI'),
    ('Charlotte', 'NC')
]

for city, state in cities:
    fips_str = fips.st_to_fips[state]

    # Data Update
    args = ['../nces_parser.py', '-update_csv', '--match_idx', 'CITY', '--match_val', city.upper()]
    print args
    call(args)

    # Report generation
    # First do the district wide segregation statistics
    args = ['../seg_by_category.py', '--outfile', city.lower().replace(' ', '_') + '_seg_report.xls', '--category', 'FIPS', '--match_idx', 'FIPS', '--match_val', fips_str]
    print args
    call(args)

    # Next do the per school reports
    args = ['../chrtr_sch_details.py', '--outfile', city.lower().replace(' ', '_') + '_school_report.xls', '--fips', fips_str]
    print args
    call(args)
