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
    def calc_iso_exp_idx(self, yidx, zidx):
        """
        Calculate the Exposure or Isolation Index
        - Exposure:  How much exposure does the minority group get to the majority group?
        - Isolation:  How much exposure does a minority group get to itself?

        Exposure:
            Sum(yi/Y * zi/ti) over schools in the category/subcategory

        yi = Students in minority group in a School
        Y = Sum of students in the minority group in the given category/subcat
        zi = Students in majority group in a School
        ti = Total Students in the School

        Isolation is the same, but with zi replaced with yi - again how
        much exposure does the group in interest get to itself?

        The plan is to add up all of the terms while keeping track of Y and then divide
        Y out of the sum at the end.
        """
        Y = {}
        Sum = {}
        for school in self.data_iter:
            try:
                yi = school[yidx]
                zi = school[zidx]
                ti = school[self.total_idx]
            except KeyError:
                raise Exception("Problem School:",school.__repr__())

            # Make sure the datastructure exists
            try:
                test = Sum[school[self.cat_idx]]
            except KeyError:
                Sum[school[self.cat_idx]] = 0.0

            # Now sum up all the members of Group Y to divided
            # out of the final sum
            try:
                test = Y[school[self.cat_idx]]
            except KeyError:
                Y[school[self.cat_idx]] = 0.0

            # Negative numbers are used to represent missing data, don't
            # include these in the calculations
            if yi < 0 or zi < 0 or ti < 0:
                continue

            # Compute the term to be summed up
            # Test for divide by zero and ignore the data point if it happens
            try:
                sum = float(yi*zi)/ti
            except ZeroDivisionError:
                continue

            # No divided by zero, so add to the sum
            try:
                Sum[school[self.cat_idx]] += sum
            except KeyError:
                Sum[school[self.cat_idx]] = sum

            # Now sum up all the members of Group Y to divided
            # out of the final sum
            try:
                Y[school[self.cat_idx]] += yi
            except KeyError:
                Y[school[self.cat_idx]] = yi

        # import pprint
        # pprint.pprint(Sum)
        # pprint.pprint(Y)
        for cat in Sum.keys():
            if Sum[cat] > 0.1:
                Sum[cat] = Sum[cat] / Y[cat]

        return Sum

    # ======================================
    def calc_exp_idx(self):
        return self.calc_iso_exp_idx(self.y_group_idx, self.z_group_idx)

    # ======================================
    def calc_iso_idx(self):
        return self.calc_iso_exp_idx(self.y_group_idx, self.y_group_idx)


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
        # Calculate:
        #   Total Student cout
        #   Percentage of Group Y
        #   Percentage of Group Z
        # Remember to keep them grouped by our geographic region (category)
        Py = {}
        Pz = {}
        T = {}
        for school in self.data_iter:
            giy = school[self.y_group_idx]
            giz = school[self.z_group_idx]
            ti = school[self.total_idx]

            try:
                Py[school[self.cat_idx]] += giy
                Pz[school[self.cat_idx]] += giz
                T[school[self.cat_idx]] += ti
            except KeyError:
                Py[school[self.cat_idx]] = giy
                Pz[school[self.cat_idx]] = giz
                T[school[self.cat_idx]] = ti

        for cat in Py.keys():
            Py[cat] = Py[cat] / T[cat]
            Pz[cat] = Pz[cat] / T[cat]

        # Py/Pz now represent a set of percentages of the student population in
        # a given group that are in Group Y and Group Z

        # TODO: Repeat for the second group (Z_GROUP)
        # Now we have P, we can calculate the numerator
        Num = {}
        for school in self.data_iter:
            giy = school[self.y_group_idx]
            ti = school[self.total_idx]

            try:
                Num[school[self.cat_idx]] += abs(giy - Py[self.cat_idx] * ti)
            except KeyError:
                Num[school[self.cat_idx]] = abs(giy - Py[self.cat_idx] * ti)

        # Now calculate the Demoninator
        # Iterate over the two or more groups
        Den = 0
        for cat in T.keys():
            Den += T[cat] * Py[cat] * (1 - Py[cat])
            Den += T[cat] * Pz[cat] * (1 - Pz[cat])


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
    print sg.calc_iso_idx()

# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



