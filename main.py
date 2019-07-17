''''
@author: majid
'''

from pm4py.objects.log.importer.xes import factory as xes_importer_factory
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from pp_role_mining.privacyPreserving import privacyPreserving
from pp_role_mining.evaluation import evaluation
from pp_role_mining.Utilities import Utilities
import pandas as pd



#for fixed_value technique
NoSubstitutions = 2
#for selective technique
MinMax = [True, True] #if you want to perturb both lower and upper bound
#for frequency_based technique
FixedValue = 0 #to combine the fixed_value techniue with the frequency_based technique (FixedValue=0 is only frequency_based without any fixed value added to the number of substitutions)

show_final_result = False

event_log = "sample_log.xes"
technique = 'selective'  # fixed_value, selective, frequency_based
resource_aware = True #true if we want to consider resources while allocating activity substitutions. Otherwise it is False
hashedActivities = False #if you want to produce hash of activities
exportPrivacyAwareLog = True #if you want to export the log with the perturbed activities
privacy_aware_log_path = "pp_" + event_log

pp = privacyPreserving(event_log)
pp.apply_privacyPreserving(technique, resource_aware, exportPrivacyAwareLog, show_final_result, hashedActivities, NoSubstitutions=NoSubstitutions, MinMax=MinMax, FixedValue=FixedValue, privacy_aware_log_path=privacy_aware_log_path, event_attribute2remove=["time:timestamp"], case_attribute2remove=["REG_DATE"])


#directly call result maker-----------------
# Event_log_type = 'original' #original or modified (privacy_aware)
# pp.result_maker(Event_log_type, True, True, 0.2, False, log_path = event_log)


#Evaluation -> accuracy analysis--------------
# df_original = pd.read_csv(".\original_intermediate_results\RscRscMatrix_original.csv")
# df_modified = pd.read_csv(".\modified_intermediate_results\RscRscMatrix_modified.csv")
# original_adjacentMatrix = df_original.iloc[:,1:]
# modified_adjacentMatrix = df_modified.iloc[:,1:]
# threshold_scale = 0.1 # for which steps of threshold of similarity, you want to do the accuracy analysis
# eval = evaluation()
# eval.accuracy_analysis(original_adjacentMatrix, modified_adjacentMatrix, threshold_scale)


#Evaluation -> privacy analysis--------------
# original_frequency = pd.read_csv('.\original_intermediate_results\original_act_frq.csv')  
# modified_frequency = pd.read_csv('.\modified_intermediate_results\modified_act_frq.csv')  
# alpha = 0.5 # to set the importance of bound of frequencies
# eval = evaluation()
# eval.privacy_analysis(original_frequency, modified_frequency, alpha)





