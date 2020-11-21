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
ASC_CYCLING	 = Beta('ASC_CYCLING',0,None,None,0)
ASC_DRIVING = Beta('ASC_DRIVING',0,None,None,0)
ASC_PT = Beta('ASC_PT',0,None,None,0)

BETA_COST	 = Beta('BETA_COST',0,None,None,0)
BETA_TIME_WALKING	 = Beta('BETA_TIME_WALKING',0,None,None,0)
BETA_TIME_CYCLING	 = Beta('BETA_TIME_CYCLING',0,None,None,0)
BETA_TIME_DRIVING	 = Beta('BETA_TIME_DRIVING',0,None,None,0)
BETA_TIME_PT	 = Beta('BETA_TIME_PT',0,None,None,0)
BETA_DISTANCE_AGE_WALKING = Beta('BETA_DISTANCE_AGE_WALKING',0,None,None,0)
BETA_DISTANCE_AGE_CYCLING = Beta('BETA_DISTANCE_AGE_CYCLING',0,None,None,0)
BETA_DISTANCE_AGE_DRIVING = Beta('BETA_DISTANCE_AGE_DRIVING',0,None,None,0)
BETA_DISTANCE_AGE_PT = Beta('BETA_DISTANCE_AGE_PT',0,None,None,0)

# parameters relevant to the nests
N_MOTOR = Beta('N_MOTOR',1,1,None, 1)
N_ECO = Beta('N_ECO',1,1,None, 1)

a_MOTOR_Pt = Beta('a_MOTOR_Pt',0.5,0,1,1)
a_MOTOR_DRIVING = Beta('a_MOTOR_DRIVING',0.5,0,1,1)
a_ECO_Pt = Beta('a_ECO_Pt',1,0,1,1)
a_ECO_WALKING = Beta('a_ECO_WALKING',1,0,1,1)
a_ECO_CYCLING = Beta('a_ECO_CYCLING',1,0,1,1)

# Define here arithmetic expressions for name that are not directly available from the data
dur_pt  = DefineVariable('dur_pt',(  dur_pt_access   +  dur_pt_rail   ) +  ( dur_pt_bus + dur_pt_int )  ,database)
cost_driving = DefineVariable ('cost_driving', cost_driving_fuel + cost_driving_ccharge, database)
# car_time  = DefineVariable('car_time', car_ivtt   +  car_walk_time  ,database)
# rate_G2E = DefineVariable('rate_G2E', 0.44378022,database)
# car_cost_euro = DefineVariable('car_cost_euro', car_cost * rate_G2E,database)
# rail_cost_euro = DefineVariable('rail_cost_euro', rail_cost * rate_G2E,database)
# np.math.log(driving_license, 10) [np.math.log(driving_license[i]) for i]

thresholds = [None, 0.5 * pandas.dur_pt.mean(), 0.75 * pandas.dur_pt.mean(), pandas.dur_pt.mean(), 1.25 * pandas.dur_pt.mean(), 1.5 * pandas.dur_pt.mean(), None]
initialBetas = [0,0,0,0,0,0]

# Utilities
Walking = ASC_WALKING  + BETA_TIME_WALKING * dur_walking + BETA_DISTANCE_AGE_WALKING * (distance * age)
Cycling = ASC_CYCLING  + BETA_TIME_CYCLING * dur_cycling + BETA_DISTANCE_AGE_CYCLING * (distance * age)
Driving = ASC_DRIVING  + BETA_COST * cost_driving + BETA_TIME_DRIVING * dur_driving + BETA_DISTANCE_AGE_DRIVING * (distance * age)
Pt = ASC_PT  + BETA_COST * cost_transit + piecewiseFormula(dur_pt, thresholds, initialBetas) + BETA_DISTANCE_AGE_PT * (distance * age)
V = {1: Walking,2: Cycling,3: Pt,4: Driving}
av = {1: 1,2: 1, 3: 1, 4: 1}

#Definitions of nests
alpha_N_MOTOR = {1: 0, 2: 0, 3: a_MOTOR_Pt, 4: a_MOTOR_DRIVING}
alpha_N_ECO = {1: a_ECO_WALKING, 2: a_ECO_CYCLING, 3: a_ECO_Pt, 4: 0}

nest_N_MOTOR = N_MOTOR, alpha_N_MOTOR
nest_N_ECO = N_ECO, alpha_N_ECO

nests = nest_N_MOTOR, nest_N_ECO

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
