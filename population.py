import numpy as np
import random
from math import log

class Population:

    """ This class describes a population of people and their infection status, optionally including information about their
    household organization and the ability to simulate infection status in an correlated way across households.
    It has methods for simulating infection status forward in time """
    
    def __init__(self, n_households, 
                    household_size, 
                    initial_prevalence, 
                    disease_length,
                    time_until_symptomatic,
                    non_quarantine_alpha,
                    daily_secondary_attack_rate,
                    fatality_pct,
                    daily_outside_infection_pct,
                    outside_symptomatic_prob,
                    initial_quarantine
                   ):
        # Initialize a population with non-trivial households
        # n_households:         the number of households in the population
        # household_size_dist:  a numpy array that should sum to 1, where household_size_dist[i] gives the fraction of
        #                       households with size i+1
        # prevalence:           prevalence of the disease in the population, used to simulate initial infection status
        # SAR:                  secondary attack rate, used for simulating initial infection status and for simulating
        #                       forward in time; SAR is defined as the probability that an infection occurs among
        #                       susceptible people within a household related to a confirmed case
        #

        self.n_households = n_households
        self.household_size = household_size
        self.initial_prevalence = initial_prevalence
        self.daily_secondary_attack_rate = daily_secondary_attack_rate
        self.non_quarantine_alpha = non_quarantine_alpha
        self.disease_length = disease_length
        self.time_until_symptomatic = time_until_symptomatic
        self.fatality_pct = fatality_pct
        self.daily_outside_infection_pct = daily_outside_infection_pct
        self.outside_symptomatic_prob = outside_symptomatic_prob

        # Reset the population and create an initial infection
        self.reset()

    def reset(self):
        # Resets the population to its initial state, including creation of an initial infection

        self.population = set([(i,j) for i in range(n_households) for j in range(household_size)]) 
        self.households = set([i for i in range(n_households)])

        if initial_quarantine:
            self.quarantined_individuals = set([(i,j) for i in range(n_households) for j in range(household_size)])
            self.unquarantined_individuals = set()
        else:
            self.unquarantined_individuals = set([(i,j) for i in range(n_households) for j in range(household_size)])
            self.quarantined_individuals = set()

        self.fatality_individuals = set()
        self.recovered_individuals = set()

        self.days_infected_so_far = {(i,j):0 for (i,j) in self.population}
        self.infected_individuals = set([])

        self.cumulative_infected_individuals = set()
        self.infections_from_inside = 0

        self.days_halted = 0
        self.currently_operating = True

        # infect initial population
        for (i,j) in self.population:
            if random.random() < self.initial_prevalence:
                self.infected_individuals.add((i,j))
                self.cumulative_infected_individuals.add((i,j))

    def halt_operations(self):
        self.currently_operating = False

    def resume_operations(self):
        self.currently_operating = True

    def is_symptomatic(self, individual):
        return self.days_infected_so_far[individual] >= self.time_until_symptomatic or random.random() < self.outside_symptomatic_prob

    def get_symptomatic_individuals(self):
        symptomatic = set([(i,j) for (i,j) in self.population if self.is_symptomatic((i,j))])
        return symptomatic

    def step(self):
        # Simulate one step forward in time
        # Simulate how infectious individuals infect each other
        # Unquarantined susceptible people become infected w/ probability = alpha*current prevalence


        # First simulate new primary cases
        current_prevalence = self.get_current_prevalence()

        if self.currently_operating:
            probability_new_infection = log(self.non_quarantine_alpha) * current_prevalence
        else:
            probability_new_infection = 0
            self.days_halted += 1

        for (i,j) in self.unquarantined_individuals:
            if (i,j) not in self.cumulative_infected_individuals:
                if random.random() < probability_new_infection:
                    self.infections_from_inside += 1
                    self.infected_individuals.add((i,j))
                    self.cumulative_infected_individuals.add((i,j))

                elif random.random() < self.daily_outside_infection_pct:
                    self.infected_individuals.add((i,j))
                    self.cumulative_infected_individuals.add((i,j))

        # Next simulate secondary cases
        for i in self.households:
            if any([(i,j) in self.infected_individuals for j in range(self.household_size)]):
                for j in range(self.household_size): 
                    if (i,j) not in self.cumulative_infected_individuals:
                        if random.random() < self.daily_secondary_attack_rate:
                            self.infected_individuals.add((i,j))
                            self.cumulative_infected_individuals.add((i,j))

        individuals_to_resolve = set()
        # update infection counts
        for (i,j) in self.infected_individuals:
            self.days_infected_so_far[(i,j)] += 1

            # see if the disease has lasted its course 
            if self.days_infected_so_far[(i,j)] >= self.disease_length:
                individuals_to_resolve.add((i,j))

        for (i,j) in individuals_to_resolve:

                self.infected_individuals.discard((i,j)) 

                if random.random() < self.fatality_pct:
                    self.fatality_individuals.add((i,j))
                else:
                    self.recovered_individuals.add((i,j))
   

    def get_current_prevalence(self):
        total_unquarantined_infected = len(self.infected_individuals.intersection(self.unquarantined_individuals))
        total_unquarantined = len(self.unquarantined_individuals)

        if total_unquarantined == 0:
            return 0
        else:
            return total_unquarantined_infected / total_unquarantined

   
    def quarantine_household(self, i):
        for j in range(self.household_size):
            self.unquarantined_individuals.discard((i,j))
            self.quarantined_individuals.add((i,j))


    def unquarantine_household(self, i):
        for j in range(self.household_size):
            self.quarantined_individuals.discard((i,j))
            self.unquarantined_individuals.add((i,j))

   
