'''
Created on Jul 1, 2019

@author: majid
'''

from pm4py.objects.log.importer.xes import factory as xes_importer_factory
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from PP.Utilities import Utilities


Dataset_name = 'sample_log.xes'
technique = 'selective'  # fixed_value, selective, frequency_based
resource_aware = True #true if we want to consider resources while allocating activity substitutions. Otherwise it is False
hashedActivities = True #if you want to produce hash of activities
expotPrivacyAwareLog = True #if you want to export the log with the perturbed activities
privacy_aware_log_path = ".\privacy_aware_log\pp_" + Dataset_name

#for fixed_value technique
NoSubstitutions = 2
#for selective technique
MinMax = [True, True] #if you want to perturb both lower and upper bound
#for frequency_based technique
FixedValue = 0 #to combine the fixed_value technique with the frequency_based technique (FixedValue=0 is only frequency_based without any fixed value added to the number of substitutions)


log = xes_importer_factory.apply(Dataset_name)

utils = Utilities(log)
    
snFull_DF, resourceList, activityList = utils.create_full_matrix_next(log)

activity_substitutions = utils.make_activitySubstitutions_general(snFull_DF, technique , resource_aware, NoSubstitutions=NoSubstitutions, MinMax=MinMax, FixedValue=FixedValue, hashedActivities=hashedActivities)

log_withoutFreq = utils.frequency_elimination(activity_substitutions, resource_aware)

if(expotPrivacyAwareLog):
    xes_exporter.export_log(log_withoutFreq, privacy_aware_log_path )

