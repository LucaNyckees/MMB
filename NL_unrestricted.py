import pandas as pd
import biogeme.database as db
import biogeme.biogeme as bio
from biogeme.expressions import Beta, DefineVariable
from biogeme.models import log, loglogit, lognested
from biogeme.models import piecewiseFormula

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

BETA_DISTANCE_AGE_WALKING = Beta('BETA_DISTANCE_AGE_WALKING',0,None,None,0)
BETA_DISTANCE_AGE_CYCLING = Beta('BETA_DISTANCE_AGE_CYCLING',0,None,None,1)
BETA_DISTANCE_AGE_DRIVING = Beta('BETA_DISTANCE_AGE_DRIVING',0,None,None,0)
BETA_DISTANCE_AGE_PT = Beta('BETA_DISTANCE_AGE_PT',0,None,None,0)

BETA_TIME_WALKING	 = Beta('BETA_TIME_WALKING',0,None,None,0)
BETA_TIME_CYCLING	 = Beta('BETA_TIME_CYCLING',0,None,None,0)
BETA_TIME_DRIVING	 = Beta('BETA_TIME_DRIVING',0,None,None,0)
BETA_TIME_PT	 = Beta('BETA_TIME_PT',0,None,None,0)

# parameters relevant to the nests
N_ECO = Beta('N_MOTOR',1,1,None, 0)
N_NOTECO = Beta('N_NMOTOR',1,1,None, 0)

#BETA_DISTANCE = Beta('BETA_DISTANCE',0,None,None,0)

# Define here arithmetic expressions for name that are not directly available from the data
dur_pt  = DefineVariable('dur_pt',(  dur_pt_access   +  dur_pt_rail   ) +  ( dur_pt_bus + dur_pt_int )  ,database)
cost_driving = DefineVariable ('cost_driving', cost_driving_fuel + cost_driving_ccharge, database)
bool_age =  DefineVariable ('bool_age',bool(age>50) , database)
# bool_age = 1 si supérieur à 50 ans, 0 sinon
# car_time  = DefineVariable('car_time', car_ivtt   +  car_walk_time  ,database)
# rate_G2E = DefineVariable('rate_G2E', 0.44378022,database)
# car_cost_euro = DefineVariable('car_cost_euro', car_cost * rate_G2E,database)
# rail_cost_euro = DefineVariable('rail_cost_euro', rail_cost * rate_G2E,database)


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
N_NOTECO = N_NOTECO, [4]
N_ECO = N_ECO, [1, 2, 3]

nests = N_NOTECO, N_ECO

# NL
logprob = lognested(V, av, nests, travel_mode)
biogeme  = bio.BIOGEME(database,logprob)
biogeme.modelName = "MAGIC_NL_unrestricted"
results = biogeme.estimate()

# Get the results in a pandas table
pandasResults = results.getEstimatedParameters()
display(pandasResults)
print(f"Nbr of observations: {database.getNumberOfObservations()}")
print(f"LL(0) =    {results.data.initLogLike:.3f}")
print(f"LL(beta) = {results.data.logLike:.3f}")
print(f"rho bar square = {results.data.rhoBarSquare:.3g}")
print(f"Output file: {results.data.htmlFileName}")

# Compare with the logit model
logprob_logit = loglogit(V,av,travel_mode)
biogeme_logit  = bio.BIOGEME(database,logprob_logit)
biogeme_logit.modelName = "GEV_Tel_NL_logit"
results_logit = biogeme_logit.estimate()

ll_logit = results_logit.data.logLike
rhobar_logit = results_logit.data.rhoBarSquare
ll_nested = results.data.logLike
rhobar_nested = results.data.rhoBarSquare

print(f"LL logit:  {ll_logit:.3f}  rhobar: {rhobar_logit:.3f}  Parameters: {results_logit.data.nparam}")
print(f"LL nested: {ll_nested:.3f}  rhobar: {rhobar_nested:.3f}  Parameters: {results.data.nparam}")
lr = -2 * (ll_logit - ll_nested)
print(f"Likelihood ratio: {lr:.3f}")
