# Translated to .py by Yundi Zhang
# Jan 2017
# Adapted to PandasBiogeme by Michel Bierlaire
# Sun Oct 21 22:54:14 2018

import numpy as np
import pandas as pd
import biogeme.database as db
import biogeme.biogeme as bio
from biogeme.expressions import Beta, DefineVariable, log
from biogeme.models import loglogit, lognested, loglogit, logcnl_avail, piecewiseFormula

pandas = pd.read_table("lpmc14.dat")
database = db.Database("lpmc14",pandas)
pd.options.display.float_format = '{:.3g}'.format

globals().update(database.variables)

#exclude = sp != 0
#database.remove(exclude)

# Parameters to be estimated
# Arguments:
#   1  Name for report. Typically, the same as the variable
#   2  Starting value
#   3  Lower bound
#   4  Upper bound
#   5  0: estimate the parameter, 1: keep it fixed
ASC_WALKING		 = Beta('ASC_WALKING',0,None,None,1)
ASC_CYCLING	 = Beta('ASC_CYCLING',-4.41,None,None,0)
ASC_DRIVING = Beta('ASC_DRIVING',-1.48,None,None,0)
ASC_PT = Beta('ASC_PT',-2.89,None,None,0)

BETA_COST	 = Beta('BETA_COST',0,None,None,0)
BETA_TIME_WALKING	 = Beta('BETA_TIME_WALKING',0,None,None,0)
BETA_TIME_CYCLING	 = Beta('BETA_TIME_CYCLING',0,None,None,0)
BETA_TIME_DRIVING	 = Beta('BETA_TIME_DRIVING',0,None,None,0)
BETA_TIME_PT	 = Beta('BETA_TIME_PT',0,None,None,0)
BETA_DISTANCE_AGE_WALKING = Beta('BETA_DISTANCE_AGE_WALKING',0,None,None,0)
BETA_DISTANCE_AGE_CYCLING = Beta('BETA_DISTANCE_AGE_CYCLING',0,None,None,1)
BETA_DISTANCE_AGE_DRIVING = Beta('BETA_DISTANCE_AGE_DRIVING',0,None,None,0)
BETA_DISTANCE_AGE_PT = Beta('BETA_DISTANCE_AGE_PT',0,None,None,0)

# parameters relevant to the nests
N_1 = Beta('N_1',1,1.15,None, 0)
N_2 = Beta('N_2',1,1.16,None, 0)

a_N_1_WALKING = Beta('a_N_1_WALKING',1,0,1,1)
#a_N_1_CYCLING = Beta('a_N_1_CYCLING',1,0,1,1)
a_N_1_Pt = Beta('a_N_1_Pt',1,0,1,1)
a_N_1_DRIVING = Beta('a_N_1_DRIVING',0.5,0,1,1)

#a_N_2_WALKING = Beta('a_N_2_WALKING',1,0,1,1)
a_N_2_CYCLING = Beta('a_N_2_CYCLING',1,0,1,1)
#a_N_2_Pt = Beta('a_N_2_Pt',0.5,0,1,1)
a_N_2_DRIVING = Beta('a_N_2_DRIVING',0.5,0,1,1)

#a_N_3_WALKING = Beta('a_N_3_WALKING',1,0,1,1)
#a_N_1_CYCLING = Beta('a_N_3_CYCLING',1,0,1,1)
#a_N_3_Pt = Beta('a_N_3_Pt',0.5,0,1,1)
#a_N_3_DRIVING = Beta('a_N_3_DRIVING',1,0,1,1)


# Define here arithmetic expressions for name that are not directly available from the data
dur_pt  = DefineVariable('dur_pt',(  dur_pt_access   +  dur_pt_rail   ) +  ( dur_pt_bus + dur_pt_int )  ,database)
cost_driving = DefineVariable ('cost_driving', cost_driving_fuel + cost_driving_ccharge, database)
bool_age =  DefineVariable ('bool_age',bool(age>50) , database)
# car_time  = DefineVariable('car_time', car_ivtt   +  car_walk_time  ,database)
# rate_G2E = DefineVariable('rate_G2E', 0.44378022,database)
# car_cost_euro = DefineVariable('car_cost_euro', car_cost * rate_G2E,database)
# rail_cost_euro = DefineVariable('rail_cost_euro', rail_cost * rate_G2E,database)
# np.math.log(driving_license, 10) [np.math.log(driving_license[i]) for i]

thresholds = [None, 0.5 * pandas.dur_pt.mean(), 0.75 * pandas.dur_pt.mean(), pandas.dur_pt.mean(), 1.25 * pandas.dur_pt.mean(), 1.5 * pandas.dur_pt.mean(), None]
initialBetas = [0,0,0,0,0,0]

# Utilities
Walking = ASC_WALKING  + BETA_TIME_WALKING * dur_walking + BETA_DISTANCE_AGE_WALKING * (distance * bool_age)
Cycling = ASC_CYCLING  + BETA_TIME_CYCLING * dur_cycling + BETA_DISTANCE_AGE_CYCLING * (distance * bool_age)
Driving = ASC_DRIVING  + BETA_COST * cost_driving + BETA_TIME_DRIVING * dur_driving + BETA_DISTANCE_AGE_DRIVING * (distance * bool_age)
Pt = ASC_PT  + BETA_COST * cost_transit + piecewiseFormula(dur_pt, thresholds, initialBetas) + BETA_DISTANCE_AGE_PT * (distance * bool_age)
V = {1: Walking,2: Cycling,3: Pt,4: Driving}
av = {1: 1,2: 1, 3: 1, 4: 1}

#Definitions of nests
alpha_N_1 = {1: a_N_1_WALKING, 2: 0, 3: a_N_1_Pt, 4: a_N_1_DRIVING}
alpha_N_2 = {1: 0, 2: a_N_2_CYCLING, 3: 0, 4: a_N_2_DRIVING}

NEST1 = N_1, alpha_N_1
NEST2 = N_2, alpha_N_2
#NEST3 = N_3, alpha_N_3

nests = NEST1, NEST2

# CNL with fixed alphas
logprob = logcnl_avail(V, av, nests, travel_mode)
biogeme  = bio.BIOGEME(database,logprob)
biogeme.modelName = "MAGIC_CNL_fix"
results = biogeme.estimate()

# Get the results in a pandas table
pandasResults = results.getEstimatedParameters()
display(pandasResults)
print(f"Nbr of observations: {database.getNumberOfObservations()}")
print(f"LL(0) =    {results.data.initLogLike:.3f}")
print(f"LL(beta) = {results.data.logLike:.3f}")
print(f"rho bar square = {results.data.rhoBarSquare:.3g}")
print(f"Output file: {results.data.htmlFileName}")
