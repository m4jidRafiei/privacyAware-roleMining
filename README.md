## Introduction
This project implements the decomposition method proposed in the paper [Mining Roles From Event Logs While Preserving Privacy](https://www.researchgate.net/publication/334290646_Mining_Roles_From_Event_Logs_While_Preserving_Privacy). 

## Python package
The implementation has been published as a standard Python package. Use the following command to install the corresponding Python package:

```shell
pip install pp-role-mining
```

## Usage

```python
from pp_role_mining.privacyPreserving import privacyPreserving

#for fixed_value technique
NoSubstitutions = 2
#for selective technique
MinMax = [True, True] #if you want to perturb both lower and upper bound
#for frequency_based technique
FixedValue = 0 #to combine the fixed_value techniue with the frequency_based technique (FixedValue=0 is only frequency_based without any fixed value added to the number of substitutions)

show_final_result = False

event_log = "running_example.xes"
# event_log = "pp_running_example.xes"
technique = 'fixed_value'  # fixed_value, selective, frequency_based
resource_aware = True #true if we want to consider resources while allocating activity substitutions. Otherwise it is False
hashedActivities = True #if you want to produce hash of activities
exportPrivacyAwareLog = True #if you want to export the log with the perturbed activities
privacy_aware_log_path = "pp_" + event_log
#
pp = privacyPreserving(event_log)
pp.apply_privacyPreserving(technique, resource_aware, exportPrivacyAwareLog, show_final_result, hashedActivities, NoSubstitutions=NoSubstitutions, MinMax=MinMax,
                           FixedValue=FixedValue, privacy_aware_log_path=privacy_aware_log_path, event_attribute2remove=["Activity", "Resource", "Costs"], case_attribute2remove=["creator"])

```
