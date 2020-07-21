from stochastic_simulation import StochasticSimulation
from load_params import load_params
import numpy as np

class SingleDormSimulation(StochasticSimulation):
    def __init__(self,
            dorm_population,
            dorm_test_rate,
            high_alert_dorm_test_rate,
            contacts_per_day,
            high_alert_contacts_per_day,
            initial_cases=1,
            safe_days_to_exit_high_alert=3,
            base_config="/home/jmc678/covid_data/group-testing/src/simulations_v2/"
            "params/june8params/noreopen/nominal_students.yaml"):
        
        self.dorm_test_rate = dorm_test_rate
        self.high_alert_dorm_test_rate = high_alert_dorm_test_rate

        self.contacts_per_day = contacts_per_day
        self.high_alert_contacts_per_day = high_alert_contacts_per_day

        self.high_alert_mode = False
        self.safe_days_to_exit_high_alert = safe_days_to_exit_high_alert
        self.days_since_last_positive = 0

        _, base_params = load_params(base_config)
        base_params['population_size'] = dorm_population
        base_params['use_asymptomatic_testing'] = True
        base_params['test_population_fraction'] = dorm_test_rate
        base_params['initial_ID_prevalence'] = None
        base_params['initial_ID_count'] = initial_cases
        base_params['daily_outside_infection_p'] = 0

        super(SingleDormSimulation, self).__init__(base_params)


    def get_free_infected(self):
        free_infected = 0
        for label, count in zip(self.get_state_vector_labels(), self.get_current_state_vector()):
            if 'E_' in label or 'ID_' in label:
                free_infected += count
        return free_infected

    def get_total_infected(self):
        return self.pop_size - self.S - self.QS
    

    def reset(self):
        self.reset_initial_state()
        self.high_alert_mode = False
        self.days_since_last_positive = 0
        self.test_pop_fraction = self.dorm_test_rate
        self.daily_contacts_lambda = self.contacts_per_day

    

    def update_days_since_last_positive(self):
        if self.new_QI_from_self_reports > 0 or self.new_QI_from_last_test > 0:
            self.days_since_last_positive = 0
        else:
            self.days_since_last_positive += 1


    def update_high_alert_mode(self):
        self.update_days_since_last_positive()
        if self.days_since_last_positive == 0 and not self.high_alert_mode:
            self.high_alert_mode = True
            self.test_pop_fraction = self.high_alert_dorm_test_rate
            self.daily_contacts_lambda = self.high_alert_contacts_per_day
        elif self.days_since_last_positive >= self.safe_days_to_exit_high_alert and self.high_alert_mode:
            self.high_alert_mode = False
            self.test_pop_fraction = self.dorm_test_rate
            self.daily_contacts_lambda = self.contacts_per_day


    def run_until_controlled(self, max_days=112):
        controlled = False
        free_infected_counts = []
        high_alert_statuses = []
        while not controlled and len(free_infected_counts) <= max_days:
            self.step()
            self.update_high_alert_mode()

            free_infected = self.get_free_infected()
            free_infected_counts.append(free_infected)
            high_alert_statuses.append(self.high_alert_mode)

            if free_infected == 0 and not self.high_alert_mode:
                controlled = True

        return controlled, self.get_total_infected(), free_infected_counts, high_alert_statuses
    

    def run_multiple_until_controlled(self, ntrajectories=100):
        total_infections = []
        days_until_controlled = []
        for _ in range(ntrajectories):
            self.reset()
            _, t, f, _ = self.run_until_controlled()
            total_infections.append(t)
            days_until_controlled.append(len(f))
        return total_infections, days_until_controlled
