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
    def __init__(self, data_list, index_dict, only_hs=False, only_el=False):
        """
        Set a dataset iterator object that we can step through
        and a dictionary of indexes for extracting the information
        from the dataobjects turned off by the dataset iterator
        """
        self.debug = 0
        self.data = data_list
        self.only_high_school = only_hs
        self.only_elementary = only_el
        self.minority_idx = index_dict['MINORITY']  # Minority Group Student Count
        self.majority_idx = index_dict['MAJORITY']  # Majority Group Student Count
        self.total_idx = index_dict['TOTAL']      # Total Student Count
        self.cat_idx = index_dict['CATEGORY']     # Index to Categorize along (state, district, etc)

        # Search for Some optional arguments
        try:
            self.sec_minority_idx = index_dict['SEC_MINORITY']  # Minority Group Student Count
        except KeyError:
            self.sec_minority_idx = None

        # Skip items that don't match item[idx] == val
        try:
            self.match = True
            self.match_idx = index_dict['MATCH_IDX']
            self.match_val = index_dict['MATCH_VAL']
        except KeyError:
            self.match = False

    # ======================================
    # Basic Accessors Functions
    # ======================================
    def get_minority(self, school):
        """
        Return the minority student count for a given school
        Handle a secondary minority group, if requested
        """
        try:
            count = int(school[self.minority_idx])
            if self.sec_minority_idx:
                count += int(school[self.sec_minority_idx])
        except KeyError:
            # raise Exception("Problem School:",school.__repr__())
            return 0
        return count

    # ======================================
    def get_majority(self, school):
        """
        Return the majority student count for a given school
        """
        # Free Lunch Majority is the non-Free Lunch people
        if self.minority_idx == 'FRELCH':
            return self.get_members(school) - self.get_minority(school)
        else:
            try:
                count = int(school[self.majority_idx])
            except KeyError:
                raise Exception("Problem School:",school.__repr__())
            return count

    # ======================================
    def get_members(self, school):
        """
        Return the total student count for a given school
        """
        try:
            count = int(school[self.total_idx])
        except KeyError:
            raise Exception("Problem School:",school.__repr__())
        return count

    # ======================================
    @property
    def filtered_data(self):
        """
        Filter the data per the requested matching
        data index and value.  Cache the results for
        later use
        """
        try:
            return self._filtered_data
        except AttributeError:
            if (
                self.match == False and
                self.only_high_school == False and
                self.only_elementary == False
            ):
                self._filtered_data = self.data
            else:

                self._filtered_data = []

                for data in self.data:
                    append_data = False

                    if self.match:
                        if self.match_val.isdigit():
                            match_int_val = int(self.match_val)
                        if (
                            data[self.match_idx] == self.match_val or
                            data[self.match_idx] == match_int_val
                            ):
                            append_data = True
                    if self.only_high_school and self.is_high_school(data):
                        append_data = True
                    if self.only_elementary and self.is_elementary(data):
                        append_data = True

                    if append_data:
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
    def get_grade(self, school, high=True):
        """
        Get the high or low grade
        """
        if high:
            grade_idx = 'GSHI'
        else:
            grade_idx = 'GSLO'

        try:
            grade = int(school[grade_idx])
        except KeyError:
            raise Exception("Problem School:",school.__repr__())
        except ValueError:
            if (
                school[grade_idx] == 'PK' or
                school[grade_idx] == 'KG'
                ):
                grade = 1
            elif (
                school[grade_idx] == 'UG' or
                school[grade_idx] == 'N' or
                school[grade_idx][0] == '.'
                ):
                grade = 0
            else:
                raise Exception("Unknown Grade: %s" % (school[grade_idx]))
        return grade

    # ======================================
    def is_elementary(self, school):
        """
        Is this school an elementary school?
        """
        high_grade = self.get_grade(school, high=True)

        if high_grade <= 6 and high_grade > 0:
            return True
        else:
            return False

    # ======================================
    def is_high_school(self, school):
        """
        Is this school an elementary school?
        """
        low_grade = self.get_grade(school, high=False)

        if low_grade >= 9:
            return True
        else:
            return False

    # ======================================
    # Calculation Methods
    # ======================================
    # ======================================
    def calc_sum(self, x_dict, y_dict):
        """
        Given two dictionaries that are grouped data entries, calculate
        a new dictionary that is the grouped proportion.
        """
        sum_dict = {}
        for key in x_dict.keys():
            try:
                sum_dict[key] = x_dict[key] + y_dict[key]
            except KeyError:
                raise Exception("Input Dicts didn't have the same keys")
                # Missing Key in Y_dict, just use X_dict value only
                # sum_dict[key] = x_dict[key]
        return sum_dict

    # ======================================
    def calc_prop(self, num_dict, den_dict):
        """
        Given two dictionaries that are grouped data entries, calculate
        a new dictionary that is the grouped proportion.
        """
        prop_dict = {}
        for key in num_dict.keys():
            try:
                prop_dict[key] = float(num_dict[key]) / float(den_dict[key])
            except ZeroDivisionError:
                prop_dict[key] = 0.0
            except KeyError:
                prop_dict[key] = 0.0
                # raise Exception("Numerator and Denominator Dicts didn't have the same keys")
        return prop_dict


    # ======================================
    def calc_totals(self, idx=None):
        """
        Get a report on the total student count and so forth
        """
        Total = {}
        for school in self.filtered_data:
            if idx == 'MINORITY':
                ti = self.get_minority(school)
            elif idx == 'MAJORITY':
                ti = self.get_majority(school)
            else:
                ti = self.get_members(school)

            # Make sure the datastructure exists
            # Negative numbers mean missing data.
            if ti >= 0:
                try:
                    Total[school[self.cat_idx]] += ti
                except KeyError:
                    Total[school[self.cat_idx]] = ti
        return Total

    # ======================================
    def calc_dependant_totals(self, sum_idx, dep_idx, sec_dep_idx=None):
        """
        Get a report on the total student count and so forth
        """
        Total = {}
        for school in self.filtered_data:
            try:
                test = Total[school[self.cat_idx]]
            except KeyError:
                Total[school[self.cat_idx]] = 0

            try:
                dependant_field = school[dep_idx]
            except KeyError:
                dependant_field = 0
            try:
                sec_dependant_field = school[sec_dep_idx]
            except KeyError:
                sec_dependant_field = 0

            if (dependant_field == '1' or
                dependant_field == 1 or
                dependant_field == 'Y' or
                sec_dependant_field == '1' or
                sec_dependant_field == 1 or
                sec_dependant_field == 'Y'):
                ti = school[sum_idx]

                # Make sure the datastructure exists
                # Negative numbers mean missing data.
                if ti >= 0:
                    Total[school[self.cat_idx]] += ti
        return Total

    # ======================================
    def calc_proportion(self, idx='MINORITY'):
        """
        Get a report on the total student count and so forth
        """
        Proportion = self.calc_totals(idx)
        Total = self.calc_totals()

        # Convert the counts to a proportion
        for cat_idx in Proportion.keys():
            try:
                Proportion[cat_idx] = float(Proportion[cat_idx]) / Total[cat_idx]
            except ZeroDivisionError:
                Proportion[cat_idx] = 0.0
            except KeyError:
                Proportion[cat_idx] = 0.0
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
                yi = school[self.minority_idx]
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
    def calc_iso_exp_idx(self, get_min, get_maj):
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
            yi = get_min(school)
            zi = get_maj(school)
            ti = self.get_members(school)

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
        return self.calc_iso_exp_idx(self.get_minority, self.get_majority)

    # ======================================
    def calc_iso_idx(self):
        # Expose a group to itself
        return self.calc_iso_exp_idx(self.get_minority, self.get_minority)

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
            ti = self.get_members(school)
            giy = self.get_minority(school)
            giz = self.get_majority(school)

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
            ti = self.get_members(school)
            giy = self.get_minority(school)
            giz = self.get_majority(school)

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
                    ti = self.get_members(ischool)
                    gyi = self.get_minority(ischool)
                    tj = self.get_members(jschool)
                    gyj = self.get_minority(jschool)

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
            giy = school[self.minority_idx]
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



