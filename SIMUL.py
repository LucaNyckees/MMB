# Translated to .py by Yundi Zhang
# Jan 2017
# Adapted to PandasBiogeme by Michel Bierlaire
# Sun Oct 21 22:54:14 2018

import numpy as np
import pandas as pd
import biogeme.database as db
import biogeme.biogeme as bio
from biogeme.expressions import Beta, DefineVariable, log, Derive
from biogeme.models import logit, loglogit, lognested, loglogit, logcnl_avail, piecewiseFormula
import biogeme.results as res

pandas = pd.read_table("lpmc14.dat")
database = db.Database("lpmc14",pandas)
pd.options.display.float_format = '{:.3g}'.format

#number of people in the sample
S = len(pandas['trip_id'])
#Number of male under 40 in the sample
S_1 = 0
#Number of male over 40 in the sample
S_2 = 0
#Number of female under 40 in the sample
S_3 = 0
#Number of female under 40 in the sample
S_4 = 0

for i in range(S):
    if (pandas['female'][i] == 0):
        if (pandas['age'][i] > 40):
            S_2 += 1
        else:
            S_1 += 1
    else:
        if (pandas['age'][i] > 40):
            S_4 += 1
        else:
            S_3 += 1

#Number of male under 40 in the population
N_1 = 2676249
#Number of male over 40 in the population
N_2 = 1633263
#Number of female under 40 in the population
N_3 = 2599058
#Number of female under 40 in the population
N_4 = 1765143
#Number of individuals in the population
N = N_1 + N_2 + N_3 + N_4

w_1 = N_1*S/(N*S_1)
w_2 = N_2*S/(N*S_2)
w_3 = N_3*S/(N*S_3)
w_4 = N_4*S/(N*S_4)

l=[]
i = 0
for i in range(S):
    if (pandas['female'][i] == 0):
        if (pandas['age'][i] > 40):
            l.append(w_2)
        else:
            l.append(w_1)
    else:
        if (pandas['age'][i] > 40):
            l.append(w_4)
        else:
            l.append(w_3)

Weights = pd.Series(l)

globals().update(database.variables)

#WEIGHT NORMALIZATION
#sumWeights = database.data['Weights'].sum()
sumWeights = Weights.sum()
S= database.getSampleSize()
sampleNormalizedWeight = Weights * S / sumWeights

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
a_N_1_Pt = Beta('a_N_1_Pt',1,0,1,1)
a_N_1_DRIVING = Beta('a_N_1_DRIVING',0.5,0,1,1)
a_N_2_CYCLING = Beta('a_N_2_CYCLING',1,0,1,1)
a_N_2_DRIVING = Beta('a_N_2_DRIVING',0.5,0,1,1)

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

"""#Definitions of nests
alpha_N_1 = {1: a_N_1_WALKING, 2: 0, 3: a_N_1_Pt, 4: a_N_1_DRIVING}
alpha_N_2 = {1: 0, 2: a_N_2_CYCLING, 3: 0, 4: a_N_2_DRIVING}

NEST1 = N_1, alpha_N_1
NEST2 = N_2, alpha_N_2

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
print(f"Output file: {results.data.htmlFileName}")"""

#SIMULATION
prob_Walking = logit(V,av,1)
prob_Cycling = logit(V,av,2)
prob_Pt = logit(V,av,3)
prob_Driving = logit(V,av,4)
VOT_Driving = Derive(Driving,'dur_driving')/Derive(Driving,'cost_driving')
VOT_Pt = Derive(Pt,'dur_pt')/Derive(Pt,'cost_transit')

elast_Driving_cost = Derive(prob_Driving,'cost_driving') / prob_Driving * dur_driving
elast_Pt_cost = Derive(prob_Pt,'cost_transit') / prob_Pt * dur_pt

simulate = {
'Weighted prob. driving': sampleNormalizedWeight * prob_Driving,
'Weighted prob. pt': sampleNormalizedWeight * prob_Pt,
'Weighted prob. cycling': sampleNormalizedWeight * prob_Cycling,
'Weighted prob. walking': sampleNormalizedWeight * prob_Walking,
'Prob. driving': prob_Driving,
'Prob. pt': prob_Pt,
'Prob. cycling': prob_Cycling,
'Prob. walking': prob_Walking,
'VOT driving': VOT_Driving,
'Weighted VOT car': sampleNormalizedWeight * VOT_Driving,
'VOT pt': VOT_Pt,
'Weighted VOT pt': sampleNormalizedWeight * VOT_Pt,
'elast_driving_cost': elast_Driving_cost,
'elast_pt_cost': elast_Pt_cost
} 

biogeme = bio.BIOGEME(database, simulate)
biogeme.modelName = "London_Simul"
betas = biogeme.freeBetaNames
results = res.bioResults(pickleFile = 'MAGIC_CNL.pickle')
betaValues = results.getBetaValues()

simulatedValues = biogeme.simulate(betaValues)

normalization_driving = simulatedValues['Weighted prob. driving'].sum()
agg_elast_driving_cost = (simulatedValues['Weighted prob. driving'] * simulatedValues['elast_driving_cost'] / normalization_driving).sum()
normalization_pt = simulatedValues['Weighted prob. pt'].sum()
agg_elast_pt_cost = (simulatedValues['Weighted prob. pt'] * simulatedValues['elast_pt_cost'] / normalization_pt).sum()


marketShare_driving = 100 * simulatedValues['Weighted prob. driving'].mean()
marketShare_pt = 100 * simulatedValues['Weighted prob. pt'].mean()
marketShare_cycling = 100 * simulatedValues['Weighted prob. cycling'].mean()
marketShare_walking = 100 * simulatedValues['Weighted prob. walking'].mean()

#Aggregate market shares (Question 3)
print('Market share driving: {} %'.format(marketShare_driving))
print('Market share pt: {} %'.format(marketShare_pt))

# average VOTs (Question 5)
print('Average value of time for driving: {} %'.format(simulatedValues['Weighted VOT driving'].mean()))
print('Average value of time for pt: {} %'.format(simulatedValues['Weighted VOT pt'].mean()))

"""simulatedValues['simulated choice'] = simulatedValues.apply(lambda row: int(row['Prob. rail'] > 0.5), axis = 1)
diff = simulatedValues['simulated choice'] - pandas.choice
    
sim_car_real_rail = 100*len(diff[diff < 0].index)/S
sim_rail_real_car = 100*len(diff[diff > 0].index)/S
    
print('Share of users choosing car with a higher probability for rail: {} %'.format(sim_rail_real_car))
print('Share of users choosing rail with a higher probability for car: {} %'.format(sim_car_real_rail))"""

#Aggregate cost elasticities (Question 6)
print('Aggregate Cost Elasticity of driving alternative: {} %'.format(agg_elast_driving_cost))
print('Aggregate Cost Elasticity of pt alternative: {} %'.format(agg_elast_pt_cost))
