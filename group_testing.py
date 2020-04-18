from math import ceil
import random
import numpy as np

class ThreeStageHierarchicalTest:

    def __init__(self,
            large_group_size,
            small_group_size,
            group_test_participation_rate,
            outer_false_negative_rate,
            inner_false_negative_rate):
        self.large_group_size = large_group_size
        self.small_group_size = small_group_size
        self.group_test_participation_rate = group_test_participation_rate
        self.inner_false_negative_rate = inner_false_negative_rate

        self.outer_group_test = HouseholdGroupTest(large_group_size,
                                                    group_test_participation_rate,
                                                    outer_false_negative_rate)
        self.inner_group_test = HouseholdGroupTest(small_group_size,
                                                    group_test_participation_rate,
                                                    inner_false_negative_rate)
                                                    

    def test(self, population):

        outer_test_results, num_outer_tests = self.outer_group_test.test(population)
        positive_outer_individuals = set([(i,j) for (i,j) in outer_test_results if outer_test_results[(i,j)]])
        
        inner_test_results, num_inner_tests = self.inner_group_test.test(population, 
                                                                test_individuals=positive_outer_individuals)

        positive_inner_individuals = set([(i,j) for (i,j) in inner_test_results if inner_test_results[(i,j)]])
        
        positive_individuals = set()
        num_individual_tests = 0

        if self.small_group_size > 1:
            for (i,j) in positive_inner_individuals:
                num_individual_tests += 1

                if (i,j) in population.infected_individuals:

                    if random.random() >  self.inner_false_negative_rate:
                        positive_individuals.add((i,j))
        else:
            positive_individuals = positive_inner_individuals

        total_tests = num_outer_tests + num_inner_tests + num_individual_tests
        test_results = {(i,j):False for (i,j) in outer_test_results}
        for (i,j) in positive_individuals:
            test_results[(i,j)] = True

        return test_results, total_tests


class HouseholdGroupTest:
    def __init__(self, 
            group_test_size,
            group_test_participation_rate,
            false_negative_rate):
        self.group_test_size = group_test_size
        self.group_test_participation_rate = group_test_participation_rate
        self.false_negative_rate = false_negative_rate

    def test(self, population, test_individuals=None):

        # Make the test groups
        
        if test_individuals == None:
            test_individuals = set()

            for (i,j) in population.population - population.fatality_individuals:
                if (i,j) in population.quarantined_individuals or random.random() < self.group_test_participation_rate:
                    test_individuals.add((i,j))

        number_of_groups = int(ceil(len(test_individuals) / self.group_test_size))
        ordered_test_individuals = list(test_individuals)
        random.shuffle(ordered_test_individuals)
        
        test_groups = {idx:set() for idx in range(number_of_groups)}
        group_idx_counter = 0
        already_grouped_individuals = set()

        for (i,j) in ordered_test_individuals:

            group_idx = group_idx_counter % number_of_groups
            group_idx_counter += 1
            
            if (i,j) not in already_grouped_individuals:

                test_groups[group_idx].add((i,j))
                already_grouped_individuals.add((i,j))

                for j_new in range(population.household_size):
                    if (i,j_new) in test_individuals and j_new != j:
                        assert((i,j_new) not in already_grouped_individuals)
                        test_groups[group_idx].add((i,j_new))
                        already_grouped_individuals.add((i,j_new))
        
        # Test the groups
        #import pdb ; pdb.set_trace() 
        test_results = {}

        for group_idx in test_groups:
            num_in_group_infected = len([(i,j) for (i,j) in test_groups[group_idx] 
                                    if (i,j) in population.infected_individuals])
            if num_in_group_infected == 0:
                test_detected_presence = False
            else:
                false_negative_pct = self.false_negative_rate ** num_in_group_infected
                if random.random() < false_negative_pct:
                    test_detected_presence = False
                else:
                    test_detected_presence = True

            for (i,j) in test_groups[group_idx]:
                test_results[(i,j)] = test_detected_presence

        return test_results, number_of_groups

class EmptyTest:
    def __init__(self, infection_pct_blf=0.01):
        pass
    def test(self, population):
        grp_test_data = {'num_grps': 0,
                        'grp_size': 0,
                        'num_negative_grps': 0}
        test_results = {}
        groups = {}
        return test_results, groups, grp_test_data

class GollierGroupTest:
    def __init__(self, infection_pct_blf=0.01):
        self.infection_pct_blf = infection_pct_blf

    def update_infection_blf(self, infection_blf):
        self.infection_pct_blf = infection_blf

    def test(self, population):
        # TODO: need to update infection_pct_blf each round
        pop_size = population.get_population_size()
        grp_size = -1 / np.log(1-self.infection_pct_blf)

        # for now ignore household correlation
        # grp_size_households = 

        num_grps = int(ceil(pop_size / grp_size))
        
        groups = {}
        for grp_num in range(num_grps):
            groups[grp_num] = []

        individuals = list(population.iter_individuals())
        shuffle(individuals)


        for individual, counter in zip(individuals, range(len(individuals))):
            grp = counter % num_grps
            groups[grp].append(individual)

        test_results = {}
        num_negative_grps = 0
        for group_idx, grp_individuals in groups.items():
            result = population.test_group(grp_individuals)
            test_results[group_idx] = result
            if not result:
                num_negative_grps += 1

        grp_test_data = {'num_grps':num_grps, 'grp_size': grp_size,
                        'num_negative_grps': num_negative_grps}
        
        return test_results, groups, grp_test_data 


