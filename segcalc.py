#!/usr/bin/env python
"""
Calculate several measures of segregation in a given data set.

The assumption is that the dataset will be a dictionary-like object
that we can index for one of several parameters to get the required
data.
"""
import sys
import operator

from nces_parser import NCESParser

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
    def __init__(self, data_list, index_dict):
        """
        Set a dataset iterator object that we can step through
        and a dictionary of indexes for extracting the information
        from the dataobjects turned off by the dataset iterator
        """
        self.debug = 0
        self.data = data_list
        self.y_group_idx = index_dict['Y_GROUP']  # Minority Group Student Count
        self.z_group_idx = index_dict['Z_GROUP']  # Majority Group Student Count
        self.total_idx = index_dict['TOTAL']      # Total Student Count
        self.cat_idx = index_dict['CATEGORY']     # Index to Categorize along (state, district, etc)
        self.sub_cat_idx = index_dict['SUB_CAT']  # Index to Sub Categorize along (grades, district, zip, etc)

        # Skip items that don't match item[idx] == val
        try:
            self.match = True
            self.match_idx = index_dict['MATCH_IDX']
            self.match_val = index_dict['MATCH_VAL']
        except KeyError:
            self.match = False

    # ======================================
    # Support Functions
    # ======================================
    @property
    def filtered_data(self):
        """
        Filter the data per the requested matching
        data index and value.  Cache the results for
        later use
        """
        if self.match == False:
            return self.data
        else:
            if self.match_val.isdigit():
                match_int_val = int(self.match_val)
            try:
                return self._filtered_data
            except AttributeError:
                self._filtered_data = []
                for data in self.data:
                    if data[self.match_idx] == self.match_val:
                        self._filtered_data.append(data)
                    if data[self.match_idx] == match_int_val:
                        self._filtered_data.append(data)
                return self._filtered_data

    # ======================================
    def get_idxed_val(self, idx_x, idx_y):
        """
        Get a dictionary mapping one index to another
        """
        Mapping = {}
        for school in self.filtered_data:
            try:
                x = school[idx_x]
                y = school[idx_y]
            except KeyError:
                raise Exception("Problem School:",school.__repr__())

            Mapping[x] = y
        return Mapping

    # ======================================
    def calc_totals(self, idx=None):
        """
        Get a report on the total student count and so forth
        """
        if idx == 'Y_GROUP':
            local_idx = self.y_group_idx
        elif idx == 'Z_GROUP':
            local_idx = self.z_group_idx
        else:
            local_idx = self.total_idx

        Total = {}
        for school in self.filtered_data:
            try:
                ti = school[local_idx]
            except KeyError:
                raise Exception("Problem School:",school.__repr__())

            # Make sure the datastructure exists
            try:
                test = Total[school[self.cat_idx]]
            except KeyError:
                Total[school[self.cat_idx]] = 0

            # Negative numbers mean missing data.
            if ti >= 0:
                Total[school[self.cat_idx]] += ti

        return Total

    # ======================================
    def calc_proportion(self, idx=None):
        """
        Get a report on the total student count and so forth
        """
        if idx == 'Y_GROUP':
            local_idx = self.y_group_idx
        elif idx == 'Z_GROUP':
            local_idx = self.z_group_idx
        else:  # Assume minority group
            local_idx = self.y_group_idx

        Proportion = {}
        Total = {}
        for school in self.filtered_data:
            try:
                cnt = int(school[local_idx])
                ti = int(school[self.total_idx])
            except KeyError:
                raise Exception("Problem School:",school.__repr__())

            # Negative numbers mean missing data
            if cnt < 0 or ti < 0:
                continue

            # Make sure the datastructure exists
            try:
                Proportion[school[self.cat_idx]] += cnt
                Total[school[self.cat_idx]] += ti
            except KeyError:
                Proportion[school[self.cat_idx]] = cnt
                Total[school[self.cat_idx]] = ti

        for cat_idx in Proportion.keys():
            try:
                Proportion[cat_idx] = float(Proportion[cat_idx]) / Total[cat_idx]
            except ZeroDivisionError:
                Proportion[cat_idx] = 0.0

        # import pprint
        # pprint.pprint(Proportion)
        return Proportion

    # ======================================
    def calc_percentages(self):
        """
        Get a report on the total student count and so forth
        """
        Percentages = {}
        for school in self.filtered_data:
            try:
                perc = dict(
                    WHITE=school['WHITE'],
                    BLACK=school['BLACK'],
                    HISP=school['HISP'],
                    ASIAN=school['ASIAN'],
                    AM=school['AM'],
                    MEMBER=school['MEMBER']
                )
            except KeyError:
                raise Exception("Problem School:",school.__repr__())

            # Make sure the datastructure exists
            try:
                test = Percentages[school[self.cat_idx]]
            except KeyError:
                Percentages[school[self.cat_idx]] = dict(WHITE=0, BLACK=0, HISP=0, ASIAN=0, AM=0, MEMBER=0)

            # Negative numbers mean missing data.
            for ethn in perc.keys():
                if perc[ethn] >= 0:
                    Percentages[school[self.cat_idx]][ethn] += perc[ethn]

        for cat_idx in Percentages.keys():
            try:
                ti = Percentages[cat_idx]['MEMBER']
                Percentages[cat_idx]['WHITE'] = float(Percentages[cat_idx]['WHITE'])/ti
                Percentages[cat_idx]['BLACK'] = float(Percentages[cat_idx]['BLACK'])/ti
                Percentages[cat_idx]['HISP'] = float(Percentages[cat_idx]['HISP'])/ti
                Percentages[cat_idx]['ASIAN'] = float(Percentages[cat_idx]['ASIAN'])/ti
                Percentages[cat_idx]['AM'] = float(Percentages[cat_idx]['AM'])/ti
            except ZeroDivisionError:
                Percentages[cat_idx]['WHITE'] = 0.0
                Percentages[cat_idx]['BLACK'] = 0.0
                Percentages[cat_idx]['HISP'] = 0.0
                Percentages[cat_idx]['ASIAN'] = 0.0
                Percentages[cat_idx]['AM'] = 0.0

        # import pprint
        # pprint.pprint(Percentages)
        return Percentages

    # ======================================
    def calc_90(self):
        """
        Percentage of the Group within the Category that are in
        a school w/ 90% or more of that give Group.
        """
        Y = {}
        Sum = {}
        for school in self.filtered_data:
            try:
                yi = school[self.y_group_idx]
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
            if yi < 0 or ti <= 0:
                continue

            # Compute the term to be summed up
            # Test for divide by zero and ignore the data point if it happens
            try:
                per = float(yi)/ti
            except ZeroDivisionError:
                continue

            # Add to the Group Tally if 90% limit is exceeded
            if per > 0.9:
                Y[school[self.cat_idx]] += yi
            # Always add to the Category total
            Sum[school[self.cat_idx]] += ti

        # Convert to a percentage
        for cat in Y.keys():
            try:
                Y[cat] = Y[cat] / Sum[cat]
            except ZeroDivisionError:
                Y[cat] = 0.0

        return Y


 
    # ======================================
    # Segragation Calculations
    # ======================================
    def calc_iso_exp_idx(self, yidx, zidx):
        """
        Calculate the Exposure or Isolation Index
        - Exposure:  How much exposure does one group get to another group?
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
        for school in self.filtered_data:
            try:
                yi = school[yidx]
                zi = school[zidx]
                ti = school[self.total_idx]
                # Special case for Free/Reduced Lunch
                if yidx == 'FRELCH' and zidx != 'FRELCH':
                    zi = ti - yi
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
        # Expose Y Group to Z Group
        return self.calc_iso_exp_idx(self.y_group_idx, self.z_group_idx)

    # ======================================
    def calc_iso_idx(self):
        # Expose a group to itself
        return self.calc_iso_exp_idx(self.y_group_idx, self.y_group_idx)


    # ======================================
    def calc_cat_totals(self):
        """
        For several calculations we need to sum up the total populations
        before hand.  This function sums up:

            Total Number of Students
            Percentage of the Total Student Count that is the Y Group
            Percentage of the Total Student Count that is the Z Group

        Returns a tuple, (T, Py, Pz)
        """
        # Calculate:
        #   Total Student Count
        #   Percentage of Total in Group Y
        #   Percentage of Total in Group Z
        # Remember to keep things grouped by region (category)
        T = {}
        Py = {}
        Pz = {}
        for school in self.filtered_data:
            ti = school[self.total_idx]
            giy = school[self.y_group_idx]
            giz = school[self.z_group_idx]
            if self.y_group_idx == 'FRELCH':
                giz = ti - giy

            # Make sure to create an entry for
            # every school, even if the data is bogus
            try:
                test = T[school[self.cat_idx]]
                test = Py[school[self.cat_idx]]
                test = Pz[school[self.cat_idx]]
            except KeyError:
                T[school[self.cat_idx]] = 0.0
                Py[school[self.cat_idx]] = 0.0
                Pz[school[self.cat_idx]] = 0.0

            # Negative numbers are used to represent missing data, don't
            # include these in the calculations
            if giy < 0 or giz < 0 or ti < 0:
                continue

            T[school[self.cat_idx]] += ti
            Py[school[self.cat_idx]] += giy
            Pz[school[self.cat_idx]] += giz

        for cat in T.keys():
            try:
                Py[cat] = float(Py[cat]) / T[cat]
            except ZeroDivisionError:
                Py[cat] = 0.0

            try:
                Pz[cat] = float(Pz[cat]) / T[cat]
            except ZeroDivisionError:
                Pz[cat] = 0.0

        if self.debug:
            print "=" * 80
            print "Totals and Averages"
            print "=" * 80
            print Py
            print Pz
            print T

        return (T, Py, Pz)

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

        Second the Total Segragation given the population:

            T(Py)(1-Py) + T(Pz)(1-Pz)

        TODO:  Why Py*(1-Py)?

        """
        # Get:
        #   Total Student Count
        #   Percentage of Total in Group Y
        #   Percentage of Total in Group Z
        # Remember to keep things grouped by region (category)
        T, Py, Pz = self.calc_cat_totals()

        # Now we have Py/Pz, we can calculate the numerator
        Num = {}
        for school in self.filtered_data:
            giy = school[self.y_group_idx]
            giz = school[self.z_group_idx]
            ti = school[self.total_idx]

            # Make sure the datastructure exists
            try:
                test = Num[school[self.cat_idx]]
            except KeyError:
                Num[school[self.cat_idx]] = 0.0

            # Negative numbers are used to represent missing data, don't
            # include these in the calculations
            if giy < 0 or giz < 0 or ti < 0:
                continue

            # Add the terms for both groups here
            # Currently we are limited to the dissimilarily between
            # two groups.
            Num[school[self.cat_idx]] += abs(giy - Py[school[self.cat_idx]] * ti)

        if self.debug:
            print "=" * 80
            print "Numerator"
            print "=" * 80
            print Num

        # We also have T and Py/Pz so we can calculate the Denominator
        Den = {}
        for cat in T.keys():
            Den[cat] = 0.0
            Den[cat] += T[cat] * Py[cat] * (1 - Py[cat])
            Den[cat] += T[cat] * Pz[cat] * (1 - Pz[cat])
            Den[cat] *= 2.0

        if self.debug:
            print "=" * 80
            print "Denomenator"
            print "=" * 80
            print Den

        Sum = {}
        for cat in Num.keys():
            try:
                Sum[cat] = Num[cat]/Den[cat]
            except ZeroDivisionError:
                Sum[cat] = 0.0

        return Sum

    # ======================================
    def calc_gini_coef(self):
        """
        Calculate the Gini Coefficient - A measure of inequality or in this case
        segregation (equality of distribution of minority students as compared to
        total minority population in the selected category)

        Calculate the sum of difference between proportions of a minority group
        against all other schools in the category:

            Sum(i)Sum(j) (ti*tj*|pi - pj|)

        Normalization term, the area of an ideally distributed district:

            2*T*T(Py)(1-Py)

        """
        # Sort schools out into lists group by the category index
        schools_by_cat = {}
        for school in self.filtered_data:
            # Make sure the datastructure exists
            try:
                test = schools_by_cat[school[self.cat_idx]]
            except KeyError:
                schools_by_cat[school[self.cat_idx]] = []
            schools_by_cat[school[self.cat_idx]].append(school)

        if self.debug:
            print schools_by_cat.keys()

        Num = {}
        # Now the double sum for the numerator
        for cat in schools_by_cat.keys():
            if self.debug:
                print "Schools in Category %s:  %d" % (cat, len(schools_by_cat[cat]))
            for ischool in schools_by_cat[cat]:
                for jschool in schools_by_cat[cat]:
                    ti = ischool[self.total_idx]
                    gyi = ischool[self.y_group_idx]
                    tj = jschool[self.total_idx]
                    gyj = jschool[self.y_group_idx]

                    # Make sure the datastructure exists
                    try:
                        test = Num[cat]
                    except KeyError:
                        Num[cat] = 0.0

                    # Negative numbers are used to represent missing data, don't
                    # include these in the calculations
                    if gyi < 0 or gyj < 0 or ti <= 0 or tj <= 0:
                        continue

                    # Sum the Term Here:  ti*tj*abs(...)
                    Num[cat] += ti*tj*abs(gyi/ti-gyj/tj)

        if self.debug:
            print "=" * 80
            print "Numerator"
            print "=" * 80
            print Num

        # Get:
        #   Total Student Count
        #   Percentage of Total in Group Y
        #   Percentage of Total in Group Z
        # To calculate the denominator
        T, Py, Pz = self.calc_cat_totals()

        Den = {}
        for cat in Num.keys():
            Den[cat] = 0.0
            Den[cat] += 2 * T[cat] * T[cat] * Py[cat] * (1 - Py[cat])

        if self.debug:
            print "=" * 80
            print "Denomenator"
            print "=" * 80
            print Den

        Gini = {}
        for cat in Num.keys():
            try:
                Gini[cat] = Num[cat]/Den[cat]
            except ZeroDivisionError:
                Gini[cat] = 0.0

        return Gini


    # ======================================
    def calc_gini_coef2(self):
        """
        Calculate the Gini Coefficient - A measure of inequality or in this case
        segregation (equality of distribution of minority students as compared to
        total minority population in the selected category)

        Calculate the sum of difference between proportions of a minority group
        against all other schools in the category:

            Sum(i)Sum(j) (ti*tj*|pi - pj|)

        Normalization term, the area of an ideally distributed district:

            2*T*T(Py)(1-Py)

        """
        # Categorized Totals/Probabilities
        T, Py, Pz = self.calc_cat_totals()

        schools_and_y_group = []
        for school in self.filtered_data:
            giy = school[self.y_group_idx]
            ti = school[self.total_idx]
            try:
                schools_and_y_group.append((giy/ti, giy, ti, school))
            except ZeroDivisionError:
                pass

        schools_by_pi = sorted(schools_and_y_group, key=operator.itemgetter(0))

        B_y_axis = {}
        B = {}
        Count = {}

        for pi, giy, ti, school in schools_by_pi:

            category = school[self.cat_idx]

            # Make sure the datastructure exists
            try:
                test = B[category]
            except KeyError:
                B_y_axis[category] = 0.0
                B[category] = 0.0
                Count[category] = 0

            # Negative numbers are used to represent missing data, don't
            # include these in the calculations

            if giy < 0 or ti <= 0:
                print school
                continue

            # Areas
            if category == '02':
                print "%f vs %f" % (pi, Py['02'])
            B_y_axis[category] += pi
            B[category] += B_y_axis[category]
            Count[category] += 1

        if self.debug:
            import pprint
            print "=" * 80
            print "B"
            print "=" * 80
            pprint.pprint(B)

            import pprint
            print "=" * 80
            print "B_y_axis"
            print "=" * 80
            pprint.pprint(B_y_axis)

            import pprint
            print "=" * 80
            print "Count"
            print "=" * 80
            pprint.pprint(Count)


        Gini = {}
        for cat in B.keys():
            try:
                B[cat] = B[cat] / (Count[cat] * B_y_axis[cat])  # Normalize area to 1
                Gini[cat] = (1 + 1/Count[cat] - 2*B[cat])           # Return Area A
            except ZeroDivisionError:
                Gini[cat] = 0.0

        return Gini



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
        {'BLACK': 5, 'WHITE': 20, 'MEMBER': 25, 'FIPS': 01, 'LEAID': 011},
        {'BLACK': 20, 'WHITE': 5, 'MEMBER': 25, 'FIPS': 01, 'LEAID': 011},
        {'BLACK': 5, 'WHITE': 20, 'MEMBER': 25, 'FIPS': 02, 'LEAID': 011},
        {'BLACK': 5, 'WHITE': 20, 'MEMBER': 25, 'FIPS': 02, 'LEAID': 011},
    ]
    idx = {
            'Y_GROUP': 'BLACK',
            'Z_GROUP': 'WHITE',
            'TOTAL': 'MEMBER',
            'CATEGORY': 'LEAID',
            'SUB_CAT': 'LEAID',
            'MATCH_IDX': 'FIPS',
            'MATCH_VAL': '06'
            }

    # Switch over to real data if interested.
    nces = NCESParser(year=2006)
    schools = nces.parse(make_dict=True)
    sg = SegCalc(schools, idx)
    # sg = SegCalc(sl, idx)

    import pprint
    print "=" * 80
    print "Exposure Index"
    print "=" * 80
    # pprint.pprint(sg.calc_exp_idx())
    print "=" * 80
    print "Isolation Index"
    print "=" * 80
    # pprint.pprint(sg.calc_iso_idx())
    print "=" * 80
    print "Dissimilarity Index"
    print "=" * 80
    pprint.pprint(sg.calc_dis_idx())
    print "=" * 80
    print "Gini Coefficient"
    print "=" * 80
    pprint.pprint(sg.calc_gini_coef())
    print "=" * 80
    print "Gini Coefficient 2"
    print "=" * 80
    pprint.pprint(sg.calc_gini_coef2())


# -------------------------------------
# Drop the script name from the args
# and call our command line parser
# -------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])



