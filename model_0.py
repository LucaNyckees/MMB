# Translated to .py by Yundi Zhang
# Jan 2017
# Adapted to PandasBiogeme by Michel Bierlaire
# Sun Oct 21 22:54:14 2018

import pandas as pd
import biogeme.database as db
import biogeme.biogeme as bio
from biogeme.expressions import Beta, DefineVariable
from biogeme.models import loglogit

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
BETA_TIME	 = Beta('BETA_TIME',0,None,None,0)

# Define here arithmetic expressions for name that are not directly available from the data
dur_pt  = DefineVariable('dur_pt',(  dur_pt_access   +  dur_pt_rail   ) +  ( dur_pt_bus + dur_pt_int )  ,database)
cost_driving = DefineVariable ('cost_driving', cost_driving_fuel + cost_driving_ccharge, database)
# car_time  = DefineVariable('car_time', car_ivtt   +  car_walk_time  ,database)
# rate_G2E = DefineVariable('rate_G2E', 0.44378022,database)
# car_cost_euro = DefineVariable('car_cost_euro', car_cost * rate_G2E,database)
# rail_cost_euro = DefineVariable('rail_cost_euro', rail_cost * rate_G2E,database)

# Utilities
Walking = ASC_WALKING  + BETA_TIME * dur_walking
Cycling = ASC_CYCLING  + BETA_TIME * dur_cycling
Driving = ASC_DRIVING  + BETA_COST * cost_driving + BETA_TIME * dur_driving
Pt = ASC_PT  + BETA_COST * cost_transit + BETA_TIME * dur_pt
V = {1: Walking,2: Cycling,3: Pt,4: Driving}
av = {1: 1,2: 1, 3: 1, 4: 1}

# The choice model is a logit, with availability conditions
logprob = loglogit(V,av,travel_mode)
biogeme  = bio.BIOGEME(database,logprob)
biogeme.modelName = "Model0_lpmc14"
results = biogeme.estimate()
# Get the results in a pandas table
pandasResults = results.getEstimatedParameters()
print(pandasResults)
print(f"Nbr of observations: {database.getNumberOfObservations()}")
print(f"LL(0) =    {results.data.initLogLike:.3f}")
print(f"LL(beta) = {results.data.logLike:.3f}")
print(f"rho bar square = {results.data.rhoBarSquare:.3g}")
print(f"Output file: {results.data.htmlFileName}")