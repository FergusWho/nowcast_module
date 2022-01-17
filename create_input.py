import json

# some parameters 
AU  = 1.5e11        
eo  = 1.6e-19
pi  = 3.141592653589793116
bo  = 2.404e-9       
t_o = 2858068.3
vo  = 52483.25 
co  = 3.0e8
n_0 = 1.0e6




data ={
# Solar Wind parameters
    'nbl': 500,					
    'x1min': 0.05,
    'x1max': 2.0,
    'idtag': 'JH',
    'tlim': 0.5,
    'FCOMP': 'gfortran',
    'gln': 5.0,
    'TinMK': 0.07,
    'glv': 400.0,
    'glb': 5.0,
    'Omega': 2.87e-6,
# CME parameters
	'i_heavy': 2,
	'seed_spec': 3.5,
	'inj_rate': 0.004,
	'run_time': 80.0,
	'cme_speed': 2500.0,
	'cme_width': 120.0,
	'duration': 1.0,
	'n_multi': 4.0,
# Transport Setup
	'p_num': 25,
	't_num': 50,
	'seed_num': 50,
	'if_arrival': 0,
	'r0_e': 1.0,
	'phi_e': 80.0,
	'cturb_au': 0.5,
	'MPI_compiler': 'mpif90',
	'ranks': 10
}

with open('input.json', 'w') as write_file:
    json.dump(data, write_file)
