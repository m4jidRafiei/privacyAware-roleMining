'''
Created on Jul 1, 2019

@author: majid
'''

from pm4py.objects.log.importer.xes import factory as xes_importer_factory
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from PP.Utilities import Utilities
from PP.SNCreator import SNCreator
import numpy as np
import pandas as pd


Dataset_name = 'Sn_Artificial.xes'
log = xes_importer_factory.apply(Dataset_name)

utils = Utilities(log)
    
snFull_DF, resourceList, activityList = utils.create_full_matrix_next(log)

resource_aware = True

activity_substitutions = utils.make_activitySubstitutions_general(snFull_DF, 'fixed_value', resource_aware, NoSubstitutions=2, MinMax=[True, True], FixedValue=0, hashedActivities=False)

log_withoutFreq = utils.frequency_elimination(activity_substitutions, resource_aware)

xes_exporter.export_log(log_withoutFreq, "privacy_aware_log_" + Dataset_name )





#Draw the network---------------------------------------------------------------------------------------------------

# snFull_DF_withoutFreq, resourceList, activityList_decomposed = utils.create_full_matrix_next(log_withoutFreq)
# snCrt_Full = SNCreator(resourceList, activityList_decomposed, snFull_DF_withoutFreq)
# 
# # snCrt_Full = SNCreator(resourceList, activityList, snFull_
# RscActMatrix_jointactivities = snCrt_Full.makeJointActivityMatrix_next() 
# 
# RscActMatrix_jointactivities_pd = pd.DataFrame(RscActMatrix_jointactivities, index=resourceList, columns=activityList_decomposed)
# RscActMatrix_jointactivities_pd.to_csv("RscActMatrix_jointactivities_external.csv", sep=',', encoding='utf-8') 
# 
# RscRscMatrix_jointactivities = snCrt_Full.convertRscAct2RscRsc(RscActMatrix_jointactivities, "pearson")
# # convert triangular to symmetric
# i_lower = np.tril_indices(RscRscMatrix_jointactivities.shape[0], -1)
# RscRscMatrix_jointactivities[i_lower] = RscRscMatrix_jointactivities.T[i_lower]  # make the matrix symmetric
# 
# RscRscMatrix_jointactivities_pd = pd.DataFrame(RscRscMatrix_jointactivities, index=resourceList, columns=resourceList)
# RscRscMatrix_jointactivities_pd.to_csv("RscRscMatrix_external.csv", sep=',', encoding='utf-8')
# 
# 
# first_act_frq = snFull_DF.groupby(['activity']).size().reset_index(name='counts')
# first_act_frq.to_csv("first_act_frq.csv", sep=',', encoding='utf-8')
# second_act_frq = snFull_DF_withoutFreq.groupby(['activity']).size().reset_index(name='counts')
# second_act_frq.to_csv("second_act_frq.csv", sep=',', encoding='utf-8')
# 
# snCrt_Full.drawRscRscGraph_advanced(RscRscMatrix_jointactivities, 0.2, False, False)    
# 
# print("done!!!")