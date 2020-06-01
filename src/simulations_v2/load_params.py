import yaml
from subdivide_severity import subdivide_severity
import os
import numpy as np
from analysis_helpers import poisson_waiting_function

# upper bound on how far the recursion can go in the yaml-depency tree
MAX_DEPTH=5

# yaml-keys which share the same key as the simulation parameter, and
# can be copied over one-to-one
COPY_DIRECTLY_YAML_KEYS = ['exposed_infection_p', 'expected_contacts_per_day', 
                            'perform_contact_tracing', 'contact_tracing_delay', 
                            'cases_isolated_per_contact', 'cases_quarantined_per_contact',
            'use_asymptomatic_testing', 'contact_trace_testing_frac', 'days_between_tests',
            'test_population_fraction','test_protocol_QFNR','test_protocol_QFPR',
            'initial_ID_prevalence', 'population_size']

DEFAULT_ZERO_PARAMS = ['initial_E_count',
                        'initial_pre_ID_count',
                        'initial_ID_count',
                        'initial_SyID_mild_count',
                        'initial_SyID_severe_count']

def update_sev_prevalence(curr_prevalence_dist, new_asymptomatic_pct):
    new_dist = [new_asymptomatic_pct]
    remaining_mass = sum(curr_prevalence_dist[1:])

    # need to scale so that param_val + x * remaning_mass == 1
    scale = (1 - new_asymptomatic_pct) / remaining_mass
    idx = 1
    while idx < len(curr_prevalence_dist):
        new_dist.append(curr_prevalence_dist[idx] * scale)
        idx += 1
    assert(np.isclose(sum(new_dist), 1))
    return np.array(new_dist)


def load_age_sev_params(param_file):
    with open(param_file) as f:
        age_sev_params = yaml.load(f)

    subparams = age_sev_params['prob_severity_given_age']
    prob_severity_given_age = np.array([
        subparams['agegroup1'],
        subparams['agegroup2'],
        subparams['agegroup3'],
        subparams['agegroup4'],
        subparams['agegroup5'],
    ])

    prob_infection = np.array(age_sev_params['prob_infection_by_age'])
    prob_age = np.array(age_sev_params['prob_age'])
    return subdivide_severity(prob_severity_given_age, prob_infection, prob_age)


# reads stochastic-simulation parameters from a yaml config file
# supports depence between config files, so that one param file
# can point to another file and params from the pointed-to-file
# are loaded first
def load_params(param_file, param_file_stack=[]):
    with open(param_file) as f:
        params = yaml.load(f)
    
    # go through params that point to other directories: start by changing
    # the current working directory so that relative file paths can be parsed
    cwd = os.getcwd()

    nwd = os.path.dirname(os.path.realpath(param_file))
    os.chdir(nwd)

    if '_inherit_config' in params:
        if len(param_file_stack) >= MAX_DEPTH:
            raise(Exception("yaml config dependency depth exceeded max depth"))
        param_file_stack.append(param_file)
        new_param_file = params['_inherit_config']
        scenario_name, base_params = load_params(new_param_file, param_file_stack)
    else:
        scenario_name = None
        base_params = {}

    if '_age_severity_config' in params:
        age_sev_file = params['_age_severity_config']
        severity_dist = load_age_sev_params(age_sev_file)
        base_params['severity_prevalence'] = severity_dist
    else:
        severity_dist = None

    if '_scenario_name' in params:
        scenario_name = params['_scenario_name']
    else:
        raise(Exception("need to specify a _scenario_name value"))
    
    # change working-directory back
    os.chdir(cwd)

    # process the main params loaded from yaml, and store them in base_params 
    for yaml_key, val in params.items():
        # skip the meta-params
        if yaml_key[0] == '_': 
            continue

        if yaml_key == 'ID_time_params':
            assert(len(val)==2)
            mean_time_ID = val[0]
            max_time_ID = val[1]
            base_params['max_time_ID'] = max_time_ID
            base_params['ID_time_function'] = poisson_waiting_function(max_time_ID, mean_time_ID)

        elif yaml_key == 'E_time_params':
            assert(len(val) == 2)
            base_params['max_time_exposed'] = val[1]
            base_params['exposed_time_function'] = poisson_waiting_function(val[1], val[0])

        elif yaml_key == 'Sy_time_params':
            assert(len(val) == 2)
            base_params['max_time_SyID_mild'] = val[1]
            base_params['SyID_mild_time_function'] = poisson_waiting_function(val[1], val[0])
            base_params['max_time_SyID_severe'] = val[1]
            base_params['SyID_severe_time_function'] = poisson_waiting_function(val[1], val[0])

        elif yaml_key == 'asymptomatic_daily_self_report_p':
            base_params['mild_symptoms_daily_self_report_p'] = val

        elif yaml_key == 'symptomatic_daily_self_report_p':
            base_params['severe_symptoms_daily_self_report_p'] = val

        elif yaml_key == 'daily_leave_QI_p':
            base_params['sample_QI_exit_function'] = (lambda n: np.random.binomial(n, val))

        elif yaml_key == 'daily_leave_QS_p':
            base_params['sample_QS_exit_function'] = (lambda n: np.random.binomial(n, val))

        elif yaml_key == 'asymptomatic_pct_mult':
            if 'severity_prevalence' not in base_params:
                raise(Exception("encountered asymptomatic_pct_mult with no corresponding severity_dist to modify"))
            new_asymptomatic_p = val * base_params['severity_prevalence'][0]
            base_params['severity_prevalence'] = update_sev_prevalence(base_params['severity_prevalence'], 
                                                                            new_asymptomatic_p)

        elif yaml_key in COPY_DIRECTLY_YAML_KEYS:
            base_params[yaml_key] = val

        else:
            raise(Exception("encountered unknown parameter {}".format(yaml_key)))



    # the pre-ID state is not being used atm so fill it in with some default params here
    if 'max_time_pre_ID' not in base_params:
        base_params['max_time_pre_ID'] = 4
        base_params['pre_ID_time_function'] = poisson_waiting_function(max_time=4, mean_time=0)

    # the following 'initial_count' variables are all defaulted to 0
    for paramname in DEFAULT_ZERO_PARAMS:
        if paramname not in base_params:
            base_params[paramname] = 0

    if 'pre_ID_state' not in base_params:
        base_params['pre_ID_state'] = 'detectable'

    if 'mild_severity_levels' not in base_params:
        base_params['mild_severity_levels'] = 1

    return scenario_name, base_params
