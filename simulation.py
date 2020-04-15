class Simulation:

    def __init__(self, population, grptest, test_freq):
        self.population = population
        self.grptest = grptest
        self.test_freq = test_freq
        self.current_day = 0
        self.last_test_day = 0

    def step(self):
        if self.current_day == 0 or self.current_day - self.last_test_day >= self.test_freq:
            test_results, groups, grp_test_data = self.grptest.test(self.population)
            self.population.update_quarantine_status(test_results, groups)
            self.last_test_day = self.current_day
        else:
            grp_test_data = None

        self.current_day += 1
        self.population.step()

        sim_data = {
                'total_infected': self.population.get_num_infected(),
                'individuals_quarantined': self.population.get_num_quarantined(),
                'households_quarantined': self.population.get_num_households_quarantined(),
                'grp_test_data': grp_test_data,
            }

        return sim_data



