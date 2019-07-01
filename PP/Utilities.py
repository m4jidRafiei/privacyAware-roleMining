'''
Created on Oct 5, 2018

@author: majid
'''

import pandas as pd
import hashlib
from Crypto.Cipher import AES
import math
import statistics
import matplotlib.pyplot as plt
from _collections import defaultdict
import numpy as np


class Utilities():
    '''
    classdocs
    '''
    
    def __init__(self, log):
        self.log = log
        self.resourceSet = set()
        self.activitySet = set()
        self.resourceList = list()
        self.activityList = list()
        
    
    def setResourceSetList(self, snMatrix):
        unique_resources = snMatrix['resource'].unique()
        self.resourceSet = set(unique_resources)
        self.resourceList = list(self.resourceSet)
        self.resourceList.sort() 
     
    def setActivitySetList(self, snMatrix):
        unique_activities = snMatrix['activity'].unique()
        self.activitySet = set(unique_activities)
        self.activityList = list(self.activitySet)
        self.activityList.sort() 
        
    
    def getResourceSet(self):
        return self.resourceSet
    
    def getActivitySet(self):
        return self.activitySet
    
    def getResourceList(self):
        return self.resourceList
    
    def getActivityList(self):
        return self.activityList
        
    
    def create_basic_matrix(self):
        snBasicList = [];
        for case_index, case in enumerate(self.log):
            for event_index, event in enumerate(case):
                if(len(snBasicList) > 0 and case_index == snBasicList[len(snBasicList) - 1]['trace_id']):
                    try:
                        snBasicList[len(snBasicList) - 1]['next_resource'] = event["org:resource"]
                    except KeyError:
                        snBasicList[len(snBasicList) - 1]['next_resource'] = ":None:"
                    # else: 
                    
                if(event_index == len(case) - 1):  # if it is the last event of the case, we will ignore it. 
                    continue  # because we need just the resource of it which is accessed by the previous statement                                           
                
                sndict = {};
                try:
                    sndict['resource'] = event["org:resource"]
                except KeyError:
                    sndict['resource'] = ":None:"
                    
                sndict['next_resource'] = ""
                sndict['relation_depth'] = "1"
                sndict['trace_length'] = len(case)
                sndict['trace_id'] = case_index
                snBasicList.append(sndict)
        
        basic_df = pd.DataFrame(snBasicList)     
        Utilities.setResourceSetList(self, basic_df)
           
        return basic_df, self.resourceList;
    
    def create_full_matrix_next(self, event_log):
        snFullList = []
        main_counter = 0
        for case_index, case in enumerate(event_log):
            for event_index, event in enumerate(case):
                sndict = {}
                     
                try:
                    sndict['activity'] = event["concept:name"]
                except KeyError:
                    sndict['activity'] = ":None:"
                
                try:
                    sndict['resource'] = event["org:resource"]
                except KeyError:
                    sndict['resource'] = ":None:"
               
                
                if(event_index == len(case) - 1):  #last event
                    sndict['next_activity'] = ":End:"
                    sndict['next_resource'] = ":End:"
                else:
                    
                    try:
                        sndict['next_activity'] = case[event_index+1]["concept:name"]
                    except KeyError:
                        sndict['next_activity'] = ":None:"
                        
                    try:
                        sndict['next_resource'] = case[event_index+1]["org:resource"]
                    except KeyError:
                        sndict['next_resource'] = ":None:"
                        
                sndict['relation_depth'] = "1"
                sndict['trace_length'] = len(case)
                sndict['trace_id'] = case_index
                
                snFullList.append(sndict)
                
                main_counter += 1
                
        
        full_df = pd.DataFrame(snFullList)  
        Utilities.setResourceSetList(self, full_df)   
        Utilities.setActivitySetList(self, full_df)
        
        return full_df, self.resourceList, self.activityList
    
    def frequency_elimination(self, activity_substitutions, resource_aware):
        
        if(resource_aware == True):
            log_withoutfreq= self.remove_frequency_wrt_resource(activity_substitutions)
        else:
            log_withoutfreq = self.remove_frequency(activity_substitutions)
        
        return log_withoutfreq
    
    
    def remove_frequency(self,activity_substitutions):
        log_withoutfreq = self.log
        
        for case_index, case in enumerate(self.log):
            for event_index, event in enumerate(case):
                     
                try:
                    log_withoutfreq[case_index][event_index]['concept:name'] = self.find_substitution_ordered(activity_substitutions, event["concept:name"])
                    print(case_index)
                except KeyError:
                    print('There is no activity in your even log!')

                
        return log_withoutfreq
    
    def remove_frequency_wrt_resource(self,activity_substitutions):
        log_withoutfreq = self.log
        
        for case_index, case in enumerate(self.log):
            for event_index, event in enumerate(case): 
                try:
                    log_withoutfreq[case_index][event_index]['concept:name'] = self.find_substitution_ordered_wrt_resource(activity_substitutions, event["concept:name"],  event["org:resource"])
                    print(case_index)
                except KeyError as e:
                    s = str(e)
                    if "org:resource" in s: 
                        log_withoutfreq[case_index][event_index]['concept:name'] = self.find_substitution_ordered_wrt_resource(activity_substitutions, event["concept:name"],  ":None:")
                        print(case_index)
                    else:
                        print(s)

                
        return log_withoutfreq

    def make_hash(self, value):
        m = hashlib.sha256()                      
        value = value.encode('utf-8')
        m.update(value)
        hexvalue = m.hexdigest()
        return hexvalue
    
    def get_activity_frequency(self, snFullDF):
        
        activity_frequencyDF = snFullDF.groupby(['activity']).size().reset_index(name='counts')
        next_activity_frequencyDF = snFullDF.groupby(['next_activity']).size().reset_index(name='counts')
        next_activity_frequencyDF = next_activity_frequencyDF.rename(columns={'next_activity':'activity'})
        
        #previous version all, all the similarity experiments are based on this
        final_activity_fequency = pd.concat([activity_frequencyDF, next_activity_frequencyDF]).drop_duplicates(subset='activity', keep="first").reset_index(drop=True) 
        
        return final_activity_fequency
    
    def get_activity_frequency_next(self, snFullDF):
        
        activity_frequencyDF = snFullDF.groupby(['activity']).size().reset_index(name='counts')
        
        return activity_frequencyDF
        
    
    
    def getFrequenciesPerResourceActivity(self, snFull_DF):
        
        all_resource_activity = snFull_DF[['resource','activity']]
        groupedbyresource = all_resource_activity.groupby(['resource'])
        resource_activity_dict = defaultdict(list)
        for resource, group in groupedbyresource:
            resource_activity_dict[resource].append(group['activity'].unique())
        #unique resource unique activity dataframe
        uRuA_list = []
        for key,value in resource_activity_dict.items():
            for val in value[0]:
                uRuA_list_disct = {}
                uRuA_list_disct['resource'] = key
                uRuA_list_disct['activity'] = val     
                uRuA_list.append(uRuA_list_disct)
        uRuA_df = pd.DataFrame(uRuA_list)  
        
        #add frequencies
        uRuA_df['counts'] = pd.Series(np.zeros(len(uRuA_df['activity'])), index=uRuA_df.index) # add column
        activity_frequencyDF = snFull_DF.groupby(['activity']).size().reset_index(name='counts')
        for index, row in activity_frequencyDF.iterrows():
            uRuA_df.loc[uRuA_df['activity'] == row['activity'], 'counts'] = row['counts']
        
        return uRuA_df
        
    def getFrequenciesPerActivity(self, snFull_DF):   
        activity_frequencyDF = snFull_DF.groupby(['activity']).size().reset_index(name='counts')
        return activity_frequencyDF
    
    
    #
    def make_activitySubstitutions_general(self, snFull_DF , method, resource_aware, **keyword_parameters):
        
        ''' This is the general function which is responsible to pick the right function best on the parameters 
        method = fixed_value, selective, frequency_based
        keyword_parameters = NoSubstitutions, MinMax, FixedValue'''

        unique_frequencies_resource = Utilities.getFrequenciesPerResourceActivity(self, snFull_DF) 
        unique_frequencies_activity = Utilities.getFrequenciesPerActivity(self, snFull_DF)
        
        hashedActivities = keyword_parameters['hashedActivities']
        
        if(method == 'fixed_value' and resource_aware == True):
            number_substitutions = keyword_parameters['NoSubstitutions']
            activity_substitutions = Utilities.make_activitySubstitutions_FixedValue(self, unique_frequencies_resource, number_substitutions, hashedActivities)
        elif(method == 'fixed_value' and resource_aware == False):
            number_substitutions = keyword_parameters['NoSubstitutions']
            activity_substitutions = Utilities.make_activitySubstitutions_FixedValue(self, unique_frequencies_activity, number_substitutions, hashedActivities)
        elif(method == 'selective' and resource_aware == True):
            min = keyword_parameters['MinMax'][0]
            max = keyword_parameters['MinMax'][1]
            activity_substitutions = Utilities.make_activitySubstitutions_Selective(self, unique_frequencies_resource, unique_frequencies_activity, min, max, hashedActivities)
        elif(method == 'selective' and resource_aware == False):
            min = keyword_parameters['MinMax'][0]
            max = keyword_parameters['MinMax'][1]
            activity_substitutions = Utilities.make_activitySubstitutions_Selective(self, unique_frequencies_activity, unique_frequencies_activity, min, max, hashedActivities)
        elif(method == 'frequency_based' and resource_aware ==True):
            fixed_value = keyword_parameters['FixedValue']
            activity_substitutions = Utilities.make_activitySubstitutions_FrequencyBased(self, unique_frequencies_resource, unique_frequencies_activity, fixed_value, hashedActivities)
        elif(method == 'frequency_based' and resource_aware ==False):
            fixed_value = keyword_parameters['FixedValue']
            activity_substitutions = Utilities.make_activitySubstitutions_FrequencyBased(self, unique_frequencies_activity, unique_frequencies_activity, fixed_value, hashedActivities)
        return activity_substitutions
    
    def make_activitySubstitutions_FixedValue(self, unique_frequencies, num_sub, hashedActivities):
        
        activity_substitutions = unique_frequencies     
        activity_substitutions = activity_substitutions.sort_values('counts')
        
        num_substitution = []
        substitution_list = []
        substitution_list_count = []
    
        for index, row in activity_substitutions.iterrows():
            if(row['counts'] == 1):
                num_substitution.append(1)
                sub_list = []
                sub_list_count = []
                for sub in range(1):
                    if(hashedActivities == True):
                        hash_sub = Utilities.make_hash(self, row.values[0]+str(sub))
                        sub_list.append(hash_sub)
                    else:                        
                        sub_list.append(row.values[0]+str(sub))
                    sub_list_count.append(0)
                    
                substitution_list.append(sub_list)
                substitution_list_count.append(sub_list_count)
                
                continue
                
            num_substitution.append(num_sub)
            sub_list = []
            sub_list_count = []
            for sub in range(num_sub):
                if(hashedActivities == True):
                    hash_sub = Utilities.make_hash(self, row.values[0]+str(sub))
                    sub_list.append(hash_sub)
                else:                        
                    sub_list.append(row.values[0]+str(sub))
                sub_list_count.append(0)
                
            substitution_list.append(sub_list)
            substitution_list_count.append(sub_list_count)
            
        activity_substitutions['num_substitution'] = num_substitution
        activity_substitutions['substitution_list'] = substitution_list
        activity_substitutions['substitution_list_count'] = substitution_list_count
        
        
        return activity_substitutions
    
    
    def make_activitySubstitutions_Selective(self, unique_frequencies_resource, unique_frequencies_activity, min, max, hashedActivities):
        
        final_activity_fequency = unique_frequencies_activity.sort_values('counts')
        final_activity_fequency = final_activity_fequency.reset_index(drop=True)
        
        uRuA_df = unique_frequencies_resource.sort_values('counts')
        uRuA_df = uRuA_df.reset_index(drop=True)
        
        activity_substitutions = uRuA_df
        
        median_frequency = statistics.median(final_activity_fequency['counts'].values)
        min_frequency = min(final_activity_fequency['counts'].values)
        
        B=plt.boxplot(final_activity_fequency['counts'].values)
        whiskers = [item.get_ydata()[0] for item in B['whiskers']]
        whisker_lower = whiskers[0]
        whisker_upper = whiskers[1]
        
        num_substitution = []
        substitution_list = []
        substitution_list_count = []
    
        for index, row in uRuA_df.iterrows():
            
            if(row['activity']==final_activity_fequency.iloc[1]['activity'] and min == True):
                num_substitution.append(math.ceil(row['counts']/min_frequency))
                sub_list = []
                sub_list_count = []
                for sub in range(math.ceil(row['counts']/min_frequency)):
                    if(hashedActivities == True):
                        hash_sub = Utilities.make_hash(self, row.values[0]+str(sub))
                        sub_list.append(hash_sub)
                    else:                        
                        sub_list.append(row.values[0]+str(sub))
                    sub_list_count.append(0)
                    
                substitution_list.append(sub_list)
                substitution_list_count.append(sub_list_count)
                
            elif(row['activity']== final_activity_fequency.iloc[final_activity_fequency.shape[0]-1]['activity'] and max == True):
                num_substitution.append(math.ceil(row['counts']/median_frequency))
                sub_list = []
                sub_list_count = []
                for sub in range(math.ceil(row['counts']/median_frequency)):
                    if(hashedActivities == True):
                        hash_sub = Utilities.make_hash(self, row.values[0]+str(sub))
                        sub_list.append(hash_sub)
                    else:                        
                        sub_list.append(row.values[0]+str(sub))
                    sub_list_count.append(0)
                    
                substitution_list.append(sub_list)
                substitution_list_count.append(sub_list_count)
                 
            else:
                num_substitution.append(1)
                sub_list = []
                sub_list_count = []
                for sub in range(1):
                    if(hashedActivities == True):
                        hash_sub = Utilities.make_hash(self, row.values[0]+str(sub))
                        sub_list.append(hash_sub)
                    else:                        
                        sub_list.append(row.values[0]+str(sub))
                    sub_list_count.append(0)
                    
                substitution_list.append(sub_list)
                substitution_list_count.append(sub_list_count)

            
        activity_substitutions['num_substitution'] = num_substitution
        activity_substitutions['substitution_list'] = substitution_list
        activity_substitutions['substitution_list_count'] = substitution_list_count
        
        
        return activity_substitutions
    
    def make_activitySubstitutions_FrequencyBased(self, unique_frequencies_resource, unique_frequencies_activity, fixed_value, hashedActivities):
        
        uRuA_df = unique_frequencies_resource.sort_values('counts')
        
        uRuA_df = uRuA_df.reset_index(drop=True)
        
        activity_substitutions = uRuA_df
        
        sum_frequency = sum(unique_frequencies_activity['counts'].values)
        
    
        num_substitution = []
        substitution_list = []
        substitution_list_count = []
    

        for index, row in uRuA_df.iterrows():
            
            number_subs = math.ceil(row['counts']/sum_frequency * 100) + fixed_value
            num_substitution.append(number_subs)
            sub_list = []
            sub_list_count = []
            for sub in range(number_subs):
                if(hashedActivities == True):
                    hash_sub = Utilities.make_hash(self, row.values[0]+str(sub))
                    sub_list.append(hash_sub)
                else:                        
                    sub_list.append(row.values[0]+str(sub))
                sub_list_count.append(0)
     
            substitution_list.append(sub_list)
            substitution_list_count.append(sub_list_count)

    
        activity_substitutions['num_substitution'] = num_substitution
        activity_substitutions['substitution_list'] = substitution_list
        activity_substitutions['substitution_list_count'] = substitution_list_count
        
        
        return activity_substitutions

    
    def find_substitution(self,activity_substitutions,activity):
        
        if(activity == ':End:'):
            sub_value_activity = ':End:'
            return
        rowSub = activity_substitutions.loc[activity_substitutions['activity'] == activity]
        allSubstitutions = rowSub['substitution_list'].values
        allSubstitutions_count = rowSub['substitution_list_count'].values
                
        for index, substitution in enumerate(allSubstitutions[0]):   
            if(allSubstitutions_count[0][index] < rowSub['counts'].values[0]/ rowSub['num_substitution'].values[0]):  
                sub_value_activity = substitution
                activity_substitutions.loc[activity_substitutions['activity'] == activity,'substitution_list_count'].iloc[0][index] +=1
                break
        return sub_value_activity
    
   
    def find_substitution_ordered(self,activity_substitutions,activity):
        
        if(activity == ':End:'):
            sub_value_activity = ':End:'
            return
        rowSub = activity_substitutions.loc[activity_substitutions['activity'] == activity]
        allSubstitutions = rowSub['substitution_list'].values
        allSubstitutions_count = rowSub['substitution_list_count'].values
                
        for index, substitution in enumerate(allSubstitutions[0]):   
            if(allSubstitutions_count[0][index] == 0):  
                sub_value_activity = substitution
                activity_substitutions.loc[activity_substitutions['activity'] == activity,'substitution_list_count'].iloc[0][index] = 1
                
                # rest to zero
                if(index != len(allSubstitutions_count[0]) - 1):
                    break
                else:
                    for index, substitution in enumerate(allSubstitutions[0]):
                        activity_substitutions.loc[activity_substitutions['activity'] == activity,'substitution_list_count'].iloc[0][index] = 0
                      
               
            
        return sub_value_activity
    
    def find_substitution_ordered_wrt_resource(self,activity_substitutions,activity, resource):
        
        if(activity == ':End:'):
            sub_value_activity = ':End:'
            return
        rowSub = activity_substitutions.loc[(activity_substitutions['activity'] == activity) & (activity_substitutions['resource'] == resource)]
        allSubstitutions = rowSub['substitution_list'].values[0]
        allSubstitutions_count = rowSub['substitution_list_count'].values[0]
        allSubstitutions.sort()
        for index, substitution in enumerate(allSubstitutions):   
            if(allSubstitutions_count[index] == 0):  
                sub_value_activity = substitution
                activity_substitutions.loc[(activity_substitutions['activity'] == activity) & (activity_substitutions['resource'] == resource), 'substitution_list_count'].iloc[0][index] = 1
                
                # rest to zero
                if(index != len(allSubstitutions_count) - 1):
                    break
                else:
                    for index, substitution in enumerate(allSubstitutions):
                        activity_substitutions.loc[(activity_substitutions['activity'] == activity) & (activity_substitutions['resource'] == resource), 'substitution_list_count'].iloc[0][index] = 0
                      
               
            
        return sub_value_activity
    
    
    def removeFrequency_full_matrix_next(self, snFullDF,type_sn):
        
        final_activity_fequency = self.get_activity_frequency_next(snFullDF)
        activity_substitutions = Utilities.make_activitySubstitutions_next(self, 2, final_activity_fequency)
       
        snFullDF_withoutFreq =  snFullDF.copy()
        next_activity_isset = False
        for indexFull, rowFull in snFullDF.iterrows():
                
            #find random sub for activity
            if(next_activity_isset == False):
                sub_value_activity = self.find_substitution(activity_substitutions,rowFull['activity'])
                snFullDF_withoutFreq.loc[indexFull,'activity'] = sub_value_activity
                
            
            
            #find random sub for nex_activty
            sub_value_activity = self.find_substitution(activity_substitutions,rowFull['next_activity'])
#             random_sub_value_next_activity = allSubstitutions[0][0]
        
            
            # if case if of the next row is the same, we should keep the same random for the activity as the random of next_activity!!!
            if(indexFull +1 < snFullDF.shape[0]): #if it is not the last row
                if(snFullDF.loc[indexFull +1 ,'activity'] == snFullDF.loc[indexFull,'next_activity'] and
                    snFullDF.loc[indexFull +1 ,'trace_id'] == snFullDF.loc[indexFull ,'trace_id']):
                    next_activity_isset = True
                    snFullDF_withoutFreq.loc[indexFull+1,'activity'] = sub_value_activity
                else:
                    next_activity_isset = False
                   
            snFullDF_withoutFreq.loc[indexFull,'next_activity'] = sub_value_activity
            
            print(snFullDF_withoutFreq.loc[indexFull])
        
        
        #activity_frequency_after_decompose = self.get_activity_frequency(snFullDF_final)

        Utilities.setResourceSetList(self, snFullDF_withoutFreq)   
        Utilities.setActivitySetList(self, snFullDF_withoutFreq)
        return snFullDF_withoutFreq, activity_substitutions , self.resourceList, self.activityList
    
    
    def AES_ECB_Encrypt(self, data):
        key = 'M4J!DPASSWORD!!!'
        cipher = AES.new(key.encode('utf8'), AES.MODE_ECB)
        length = 16 - (len(data) % 16)
        data += bytes([length])*length
        msg = cipher.encrypt(data)
        result = msg.hex()
        return result
    
    def AES_ECB_Decrypt(self, enc_data):
        key = 'M4J!DPASSWORD!!!'
        decipher = AES.new(key.encode('utf8'), AES.MODE_ECB)
        msg_dec = decipher.decrypt(bytes.fromhex(enc_data))
        msg_dec = msg_dec[:-msg_dec[-1]]
        return msg_dec.decode('utf-8')
    
    def resourceEncryption(self, snDF):
        for indexDF, rowDF in snDF.iterrows():
            print("-----------", rowDF)
            snDF.loc[indexDF,'resource'] = Utilities.AES_ECB_Encrypt(self, snDF.loc[indexDF,'resource'].encode('utf-8'))
            snDF.loc[indexDF,'next_resource'] = Utilities.AES_ECB_Encrypt(self, snDF.loc[indexDF,'next_resource'].encode('utf-8'))
        
        Utilities.setResourceSetList(self, snDF)   
        return snDF, self.resourceList
    
    def resourceEncryption_connector(self, snDF):
        for indexDF, rowDF in snDF.iterrows():
            print("-----------", rowDF)
            snDF.loc[indexDF,'resource'] = Utilities.AES_ECB_Encrypt(self, snDF.loc[indexDF,'resource'].encode('utf-8'))
            snDF.loc[indexDF,'prev_resource'] = Utilities.AES_ECB_Encrypt(self, snDF.loc[indexDF,'prev_resource'].encode('utf-8'))
        
        Utilities.setResourceSetList_previous(self, snDF)    
        return snDF, self.resourceList
    
    def resourceDecryption(self, resourceList):
        
        Decrypted_resourceList = list()
        for resource in resourceList:
            print("-----------", resource)
            Decrypted_resourceList.append(Utilities.AES_ECB_Decrypt(self, resource))
            
        return Decrypted_resourceList
            
    
    def addFrequency_full_matrix(self, snFullDF_withoutFreq, activity_substitutions):
        
        snFullDF = snFullDF_withoutFreq.copy()
        for indexFull, rowFull in snFullDF_withoutFreq.iterrows():
            for indexSub, rowSub in activity_substitutions.iterrows():
                if(rowFull['activity'] in rowSub['substitution_list']):
                    snFullDF.loc[indexFull ,'activity'] = rowSub['activity']
                if(rowFull['next_activity'] in rowSub['substitution_list']):
                    snFullDF.loc[indexFull ,'next_activity'] = rowSub['activity']
        
        Utilities.setResourceSetList(self, snFullDF)   
        Utilities.setActivitySetList(self, snFullDF)
        return snFullDF, self.resourceList, self.activityList      
        

        
