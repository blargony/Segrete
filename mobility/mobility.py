#!/usr/bin/env python
"""
Quick script to generate several summaries for a list of cities
"""
from subprocess import call
import fips

cities = [
    (['San Jose'], 'CA'),
    (['San Francisco'], 'CA'),
    (['Washington'], 'DC'),
    (['Seattle'], 'WA'),
    (['Salt Lake City'], 'UT'),
    (['New York'], 'NY'),
    (['Boston'], 'MA'),
    (['San Diego'], 'CA'),
    (['Newark'], 'NJ'),
    (['Machester'], 'NH'),
    (['Cleveland '], 'OH'),
    (['St Louis', 'St. Louis', 'Saint Louis'], 'MO'),
    (['Raleigh'], 'NC'),
    (['Jacksonville'], 'FL'),
    (['Columbus'], 'OH'),
    (['Indianapolis'], 'IN'),
    (['Dayton'], 'OH'),
    (['Atlanta'], 'GA'),
    (['Milwaukee'], 'WI'),
    (['Charlotte'], 'NC')
]

for city_names, state in cities:
    fips_str = fips.st_to_fips[state]

    city_name = city_names[0]

    # Build up a list of possible city names - if there are spelling variations this allows nces_parser to select them all
    match_vals = []
    for city_name in city_names:
        match_vals.append(city_name.upper())

    # Data Update
    args = ['../nces_parser.py', '--match_idx', 'CITY', '--match_val'] + match_vals
    print args
    call(args)

    # Report generation
    # First do the district wide segregation statistics
    args = ['../seg_by_category.py', '--outfile', city_name.lower().replace(' ', '_') + '_seg_report.xls', '--category', 'FIPS', '--match_idx', 'FIPS', '--match_val', fips_str]
    print args
    call(args)

    # Next do the per school reports
    args = ['../chrtr_sch_details.py', '--outfile', city_name.lower().replace(' ', '_') + '_school_report.xls', '--fips', fips_str]
    print args
    call(args)
