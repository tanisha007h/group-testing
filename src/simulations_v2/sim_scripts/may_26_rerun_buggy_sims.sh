
python3 run_sims.py config/asymptomatic_p.yaml june_realistic asymptomatic_p_june_realistic &
python3 run_sims.py config/asymptomatic_p.yaml fall_realistic asymptomatic_p_fall_realistic &
python3 run_sims.py config/asymptomatic_p.yaml fall_realistic_testing asymptomatic_p_fall_realistic_testing &

python3 run_sims.py config/contact_tracing_isolations.yaml june_realistic contact_isolations_june_realistic &
python3 run_sims.py config/contact_tracing_isolations.yaml fall_realistic contact_isolations_fall_realistic &
python3 run_sims.py config/contact_tracing_isolations.yaml fall_realistic_testing contact_isolations_fall_realistic_testing &
