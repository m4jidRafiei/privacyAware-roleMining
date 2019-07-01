'''
Created on Jul 1, 2019

@author: majid
'''

from PP.Utilities import Utilities
from PP.SN_Tools import SNCreator
import numpy as np
import pandas as pd
from pm4py.objects.log.importer.xes import factory as xes_importer_factory

#set intermediate results

Event_log_type = 'modified' #original or modified (privacy_aware)

if(Event_log_type == 'original'):
    Resource_Activity_Matrix = ".\original_intermediate_results\RscActMatrix_jointactivities_original.csv"
    Resource_Resource_Matrix = ".\original_intermediate_results\RscRscMatrix_original.csv"
    Activity_Frequency = ".\original_intermediate_results\original_act_frq.csv"
else:
    Resource_Activity_Matrix = ".\modified_intermediate_results\RscActMatrix_jointactivities_modified.csv"
    Resource_Resource_Matrix = ".\modified_intermediate_results\RscRscMatrix_modified.csv"
    Activity_Frequency = ".\modified_intermediate_results\modified_act_frq.csv"


log = xes_importer_factory.apply("Sn_Artificial.xes")

utils = Utilities(log)

snFull_DF, resourceList, activityList = utils.create_full_matrix_next(log)

snCrt_Full = SNCreator(resourceList, activityList, snFull_DF)

RscActMatrix_jointactivities = snCrt_Full.makeJointActivityMatrix_next() 
  
RscActMatrix_jointactivities_pd = pd.DataFrame(RscActMatrix_jointactivities, index=resourceList, columns=activityList)
RscActMatrix_jointactivities_pd.to_csv(Resource_Activity_Matrix, sep=',', encoding='utf-8') 

RscRscMatrix_jointactivities = snCrt_Full.convertRscAct2RscRsc(RscActMatrix_jointactivities, "pearson")
#convert triangular to symmetric
i_lower = np.tril_indices(RscRscMatrix_jointactivities.shape[0], -1)
RscRscMatrix_jointactivities[i_lower] = RscRscMatrix_jointactivities.T[i_lower]  # make the matrix symmetric

RscRscMatrix_jointactivities_pd = pd.DataFrame(RscRscMatrix_jointactivities, index=resourceList, columns=resourceList)
RscRscMatrix_jointactivities_pd.to_csv(Resource_Resource_Matrix, sep=',', encoding='utf-8')

first_act_frq = snFull_DF.groupby(['activity']).size().reset_index(name='counts')
first_act_frq.to_csv(Activity_Frequency, sep=',', encoding='utf-8')


snCrt_Full.drawRscRscGraph_advanced(RscRscMatrix_jointactivities, 0.2, False, False)

print('Done!')