#!/usr/bin/env python
"""
Calculate several measures of segregation in a given data set.

The assumption is that the dataset will be a dictionary-like object
that we can index for one of several parameters to get the required
data.
"""
import sys

# ==============================================================================
# Constants
# ==============================================================================

# ==============================================================================
# Utility Functions
# ==============================================================================

# ==============================================================================
class SegCalc(object):
    """
    A segregation calculating object.
    """
    def __init__(self, data_iter, index_dict):
        """
        Set a dataset iterator object that we can step through
        and a dictionary of indexes for extracting the information
        from the dataobjects turned off by the dataset iterator
        """
        self.data_iter = data_iter
        self.y_group_idx = index_dict['Y_GROUP']  # Minority Group Student Count
        self.z_group_idx = index_dict['Z_GROUP']  # Majority Group Student Count
        self.total_idx = index_dict['TOTAL']    # Total Student Count
        self.cat_idx = index_dict['CATEGORY']     # Index to Categorize along (state, district, etc)
        self.sub_cat_idx = index_dict['SUB_CAT']  # Index to Sub Categorize along (grades, district, zip, etc)

    # ======================================
    # Segragation Calculations
    # ======================================
    def calc_exp_idx(self):
        """
        Calculate the Exposure Index - how much exposure does the minority group
        get to the majority group?

            Sum(yi/Y * zi/ti) over schools in the category/subcategory

        yi = Students in minority group in a School
        Y = Sum of students in the minority group in the given category/subcat
        zi = Students in majority group in a School
        ti = Total Students in the School

        The plan is to add up all of the terms while keeping track of Y and then divide
        Y out of the sum at the end.
        """
        Y = {}
        Sum = {}
        for school in self.data_iter:
            yi = school[self.y_group_idx]
            zi = school[self.z_group_idx]
            ti = school[self.total_idx]
            try:
                Y[school[self.cat_idx]] += yi
            except KeyError:
                Y[school[self.cat_idx]] = yi
            try:
                Sum[school[self.cat_idx]] += float(yi*zi)/ti
            except KeyError:
                Sum[school[self.cat_idx]] = float(yi*zi)/ti

        for cat in Sum.keys():
            Sum[cat] = Sum[cat] / Y[cat]

        return Sum

    # ======================================
    def calc_iso_idx(self):
        """
        Calculate the Isolation Index - How much does a group encounter only
        others from the same group?

            Sum(yi/Y * yi/ti) over schools in the category/subcategory

        yi = Students in a group in a School
        Y = Sum of students in a group in the given category/subcat
        ti = Total Students in the School

        The plan is to add up all of the terms while keeping track of Y and then divide
        Y out of the sum at the end.
        """
        Y = {}
        Sum = {}
        for school in self.data_iter:
            yi = school[self.y_group_idx]
            ti = school[self.total_idx]
            try:
                Y[school[self.cat_idx]] += yi
            except KeyError:
                Y[school[self.cat_idx]] = yi
            try:
                Sum[school[self.cat_idx]] += float(yi*yi)/ti
            except KeyError:
                Sum[school[self.cat_idx]] = float(yi*yi)/ti

        for cat in Sum.keys():
            Sum[cat] = Sum[cat] / Y[cat]

        return Sum

    # ======================================
    def calc_dis_idx(self):
        """
        Calculate the Dissimilarity Index - Current Segregation divided by
        the maximum possible segregation given the actual population demographics

        This consists of two terms, first the calculated segregation.  In this case
        we will calculate how many students must change schools for school demographics
        to match the population at large:

            Sum(i)Sum(y) |(giy - Py*ti)|  (Note Absolute Value, we need the delta from the ideal)

        Py is percentage of students in Y_GROUP in the Category population (state/district/etc)
        ti is the total students in the school
        Py*ti is the number of students in school i that should be in the Y_GROUP
        giy is the Y_GROUP students actually in a given school


        """
        # TODO: Repeat for the second group (Z_GROUP)
        P_temp = {}
        for school in self.data_iter:
            giy = school[self.y_group_idx]
            ti = school[self.total_idx]

            try:
                P_temp[school[self.cat_idx]][0] += giy
                P_temp[school[self.cat_idx]][1] += ti
            except KeyError:
                P_temp[school[self.cat_idx]] = [giy, ti]

        P = {}
        for cat in P_temp.keys():
            P[cat] = P_temp[cat][0] / P_temp[cat][1]

        # TODO: Repeat for the second group (Z_GROUP)
        # Now we have P, we can calculate the numerator
        Num = {}
        for school in self.data_iter:
            giy = school[self.y_group_idx]
            ti = school[self.total_idx]

            try:
                Num[school[self.cat_idx]] += abs(giy - P[self.cat_idx] * ti)
            except KeyError:
                Num[school[self.cat_idx]] = abs(giy - P[self.cat_idx] * ti)

        # Now calculate the Demoninator
        # Iterate over the two or more groups
        Den = {}
        for school in self.data_iter:
            giy = school[self.y_group_idx]
            ti = school[self.total_idx]


# *****************************************************************************
# -------------------------------------
# Print the Usage
# -------------------------------------
def usage():
    print __doc__  # oh python, you are so self documenting

# -------------------------------------
# Parse the command line options
# -------------------------------------
def main(argv):
    # Lets do a quick test, normally this isn't run at the command line
    # Short list for now
    sl = [
        {'BLACK': 5, 'WHITE': 10, 'TOTAL': 25, 'FIPS': 01, 'LEA': 011},
        {'BLACK': 5, 'WHITE': 10, 'TOTAL': 25, 'FIPS': 01, 'LEA': 011},
        {'BLACK': 5, 'WHITE': 10, 'TOTAL': 25, 'FIPS': 01, 'LEA': 011},
        {'BLACK': 5, 'WHITE': 10, 'TOTAL': 25, 'FIPS': 01, 'LEA': 011},
        {'BLACK': 5, 'WHITE': 10, 'TOTAL': 25, 'FIPS': 02, 'LEA': 011},
        {'BLACK': 5, 'WHITE': 10, 'TOTAL': 25, 'FIPS': 02, 'LEA': 011},
        {'BLACK': 5, 'WHITE': 10, 'TOTAL': 25, 'FIPS': 02, 'LEA': 011},
        {'BLACK': 5, 'WHITE': 10, 'TOTAL': 25, 'FIPS': 02, 'LEA': 011}
    ]
    idx = {'Y_GROUP': 'BLACK', 'Z_GROUP': 'WHITE', 'TOTAL': 'TOTAL', 'CATEGORY': 'FIPS', 'SUB_CAT': 'LEA'}

    sg = SegCalc(sl, idx)
    print sg.calc_exp_idx()

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



