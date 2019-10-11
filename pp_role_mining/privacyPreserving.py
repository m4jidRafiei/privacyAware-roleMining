'''
@author: majid
'''

from pp_role_mining.Utilities import Utilities
from pm4py.objects.log.importer.xes import factory as xes_importer_factory
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from pp_role_mining.SN_Tools import SNCreator
import pandas as pd
import numpy as np
import tempfile
from pp_role_mining.PrivacyExtension import PrivacyExtension

class privacyPreserving(object):
    '''
    Applying privacy preserving technique and/or see the reults
    '''

    def __init__(self, log):
        '''
        Constructor
        '''
        if type(log) is str:
            self.log = xes_importer_factory.apply(log)
        else:
            self.log = log

    def apply_privacyPreserving(self, technique, resource_aware, expotPrivacyAwareLog, show_final_result,
                                hashedActivities, **keyword_param):

        utils = Utilities(self.log)

        snFull_DF, resourceList, activityList = utils.create_full_matrix_next(self.log, relation_depth=False,
                                                                              trace_length=False, trace_id=True)

        activity_substitutions = utils.make_activitySubstitutions_general(snFull_DF, technique, resource_aware,
                                                                          NoSubstitutions=keyword_param[
                                                                              'NoSubstitutions'],
                                                                          MinMax=keyword_param['MinMax'],
                                                                          FixedValue=keyword_param['FixedValue'],
                                                                          hashedActivities=hashedActivities)

        event_attribute2remove = keyword_param['event_attribute2remove'] if 'event_attribute2remove' in keyword_param else []
        case_attribute2remove = keyword_param[
            'case_attribute2remove'] if 'case_attribute2remove' in keyword_param else []

        log_withoutFreq = utils.frequency_elimination(activity_substitutions, resource_aware, True, True,
                                                      event_attribute2remove=event_attribute2remove,
                                                      case_attribute2remove=case_attribute2remove)

        ##adding privacy extension here....

        privacy = PrivacyExtension(log_withoutFreq)

        eventAttributes = {}
        for key in event_attribute2remove:
            eventAttributes[key] = 'removed'

        if(hashedActivities == True):
            eventAttributes['concept:name'] = 'hashed'

        if('concept:name' in eventAttributes):
            eventAttributes['concept:name'] += ',perturbed'

        traceAttributes = {}
        for key in case_attribute2remove:
            traceAttributes[key] = 'removed'

        privacy.set_privacy_tracking()
        privacy.set_methods(method='pa_roleMining', abstraction=True,
                            desiredAnalyses=['Role Mining'])
        privacy.set_statistics(noModifiedTraces=len(log_withoutFreq) , noModifiedEvents=sum([len(trace) for trace in log_withoutFreq]))
        privacy.set_modification_meta(logAttributes={}, traceAttributes=traceAttributes,
                                      eventAttributes=eventAttributes)
        privacy.set_modification_data(controlflowPers={},
                                      organizationalPers={}, timePers={}, casePers={})


        #End of adding extension

        if (expotPrivacyAwareLog):
            xes_exporter.export_log(log_withoutFreq, keyword_param['privacy_aware_log_path'])

        if (show_final_result):
            read_external_log = False
            Event_log_type = 'modified'  # original or modified (privacy_aware)
            export_intermediate_results = True
            threshold = 0.2
            encrypted_network = False

            self.result_maker(Event_log_type, read_external_log, export_intermediate_results, threshold,
                              encrypted_network,
                              log_path=keyword_param['privacy_aware_log_path'],
                              internal_log=log_withoutFreq)

    def result_maker(self, Event_log_type, read_external_log, export_intermediate_results, threshold, encrypted_network,
                     **keyword_param):

        if (read_external_log):
            log_path = keyword_param['log_path']
            log = xes_importer_factory.apply(log_path)
        else:
            log = keyword_param['internal_log']

        temp1 = tempfile.NamedTemporaryFile(suffix='.csv')
        temp2 = tempfile.NamedTemporaryFile(suffix='.csv')
        temp3 = tempfile.NamedTemporaryFile(suffix='.csv')
        temp1.close()
        temp2.close()
        temp3.close()

        if (Event_log_type == 'original'):


            Resource_Activity_Matrix = temp1.name
            Resource_Resource_Matrix = temp2.name
            Activity_Frequency = temp3.name
        else:
            Resource_Activity_Matrix = temp1.name
            Resource_Resource_Matrix = temp2.name
            Activity_Frequency = temp3.name

        utils = Utilities(log)

        snFull_DF, resourceList, activityList = utils.create_full_matrix_next(log, relation_depth=False,
                                                                              trace_length=False, trace_id=True)

        snCrt_Full = SNCreator(resourceList, activityList, snFull_DF)

        RscActMatrix_jointactivities = snCrt_Full.makeJointActivityMatrix_next()

        RscActMatrix_jointactivities_pd = pd.DataFrame(RscActMatrix_jointactivities, index=resourceList,
                                                       columns=activityList)
        RscActMatrix_jointactivities_pd.to_csv(Resource_Activity_Matrix, sep=',', encoding='utf-8')

        RscRscMatrix_jointactivities = snCrt_Full.convertRscAct2RscRsc(RscActMatrix_jointactivities, "pearson")
        # convert triangular to symmetric
        i_lower = np.tril_indices(RscRscMatrix_jointactivities.shape[0], -1)
        RscRscMatrix_jointactivities[i_lower] = RscRscMatrix_jointactivities.T[i_lower]  # make the matrix symmetric

        RscRscMatrix_jointactivities_pd = pd.DataFrame(RscRscMatrix_jointactivities, index=resourceList,
                                                       columns=resourceList)
        RscRscMatrix_jointactivities_pd.to_csv(Resource_Resource_Matrix, sep=',', encoding='utf-8')

        first_act_frq = snFull_DF.groupby(['activity']).size().reset_index(name='counts')
        first_act_frq.to_csv(Activity_Frequency, sep=',', encoding='utf-8')

        snCrt_Full.drawRscRscGraph_advanced(RscRscMatrix_jointactivities, threshold, False, encrypted_network)
