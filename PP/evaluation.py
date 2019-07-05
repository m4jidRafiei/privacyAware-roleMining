'''
@author: majid
'''

import numpy as np
import pandas as pd
import statistics
import matplotlib.pyplot as plt


class evaluation(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self = self
    
    
    def accuracy_analysis(self, original_adjacentMatrix, modified_adjacentMatrix, threshold_scale):
    
        for Threshold in np.arange(0.0, 1.0, threshold_scale):  
            print(Threshold)
            print('============================') 
            rows, cols = np.where(original_adjacentMatrix > Threshold)
            list_tuple_original = zip(rows, cols)
            list_tuple_original = list(list_tuple_original)
            
            rows, cols = np.where(modified_adjacentMatrix > Threshold)
            list_tuple_modified = zip(rows, cols)
            list_tuple_modified = list(list_tuple_modified)
            
            counter = 0
            for item in list_tuple_original:
                if(item in list_tuple_modified):
                    counter += 1
            
            original_modified = counter/2
            
            original = len(list_tuple_original) / 2
            
            print('Similarity Connected')
            print(original_modified/original)
            
            #unconnected----------------------------------------------------------
            
            rows, cols = np.where(original_adjacentMatrix <= Threshold)
            list_tuple_original = zip(rows, cols)
            list_tuple_original = list(list_tuple_original)
            
            rows, cols = np.where(modified_adjacentMatrix <= Threshold)
            list_tuple_modified = zip(rows, cols)
            list_tuple_modified = list(list_tuple_modified)
            
            counter = 0
            for item in list_tuple_original:
                if(item in list_tuple_modified):
                    counter += 1
            
            original_modified = counter/2
            
            original = len(list_tuple_original) / 2
            
            print('Similarity unconnected')
            print(original_modified/original)
            
            print('=================================')  
            
    def get_bounds(self, frq_pd):
    
        frq_pd = frq_pd.sort_values('counts')    
        median_frequency = statistics.median(frq_pd['counts'].values)
        min_frequency = min(frq_pd['counts'].values)
            
        B = plt.boxplot(frq_pd['counts'].values)
    
        lower_quartile = B['whiskers'][0].get_ydata()[0]
        lower_whisker = B['whiskers'][0].get_ydata()[1]
        upper_quartile = B['whiskers'][1].get_ydata()[0]
        upper_whisker = B['whiskers'][1].get_ydata()[1]
    
        all_outliers = B['fliers'][0].get_ydata()
    
        index_upper = np.where(frq_pd['counts'].values > upper_quartile)[0]
        index_lower = np.where(frq_pd['counts'].values < lower_quartile)[0]
    
        upper_bound = np.take(frq_pd['counts'].values, index_upper)
        lower_bound = np.take(frq_pd['counts'].values, index_lower)
        
        return upper_bound, lower_bound


    def get_act(self, upper_bound, lower_bound, frq_pd):
    
        upper_activity = []
        lower_activity = []
        for index, row in frq_pd.iterrows():
            for row2 in upper_bound:
                if(row['counts'] == row2):
                    upper_activity.append(row['activity'])
        for index, row in frq_pd.iterrows():
            for row2 in lower_bound:
                if(row['counts'] == row2):
                    lower_activity.append(row['activity']) 
                    
    #     for row in upper_bound:
    #         upper_activity.append(frq_pd.loc[frq_pd['counts'] == row, 'activity'].values[0])
    #     for row1 in lower_bound:
    #         lower_activity.append(frq_pd.loc[frq_pd['counts'] == row1, 'activity'].values[0]) 
        
        return upper_activity, lower_activity


    def get_sub(self, f_upper_sensitive_activities, f_lower_sensitive_activities, frq_pd):
    
        upper_sub = []
        lower_sub = []
        for row in frq_pd['activity'].values:
            for row2 in f_upper_sensitive_activities:
                if(row.__contains__(row2)):
                    upper_sub.append(row)
        for row in frq_pd['activity'].values:
            for row2 in f_lower_sensitive_activities:
                if(row.__contains__(row2)):
                    lower_sub.append(row) 
                     
        return upper_sub, lower_sub
        

    def get_sensitive_frq(self, upper_bound, lower_bound):
        upper_diff = [abs(j - i) for i, j in zip(upper_bound, upper_bound[1:])]
        lower_diff = [abs(j - i) for i, j in zip(lower_bound, lower_bound[1:])]
        
        if(len(upper_diff) < 1):
            upper_diff_limit = 0
        else:
            upper_diff_limit = statistics.mean(upper_diff)
        
        if(len(lower_diff) < 1):
            lower_diff_limit = 0
        else:
            lower_diff_limit = statistics.mean(lower_diff)
    
        upper_sensitive_potential = []
        lower_sensitive_potential = []
        upper_bound_list = upper_bound.tolist()
        upper_bound_list.sort(reverse=True)
    
        for i, j in zip(upper_bound_list, upper_bound_list[1:]):
            if(upper_diff_limit == 0):
                break
            elif(i - j <= upper_diff_limit):
                upper_sensitive_potential.append(i) 
            else:
                upper_sensitive_potential.append(i) 
                break
        # if no big gap is found
        if(len(upper_sensitive_potential) == len(upper_bound) - 1):
            upper_sensitive = []
        else:
            upper_sensitive = upper_sensitive_potential
    
        for i, j in zip(lower_bound, lower_bound[1:]):
            if(lower_diff_limit == 0):
                break
            elif(j - i <= lower_diff_limit):
                lower_sensitive_potential.append(i) 
            else:
                lower_sensitive_potential.append(i) 
                break
    
        # if no big gap is found
        if(len(lower_sensitive_potential) == len(lower_bound) - 1):
            lower_sensitive = []
        else:
            lower_sensitive = lower_sensitive_potential
        
        return upper_sensitive, lower_sensitive


    def recursiveCL(self, bound, l_bound, c, most_frequent):
        sum = 0
        for item in bound[1:]:
            sum += item
        if(most_frequent < c * sum):
            return self.recursiveCL(bound[1:], l_bound + 1, c, most_frequent) 
        else:
            return l_bound


    def find_l(self, bound, c):
        most_frequent = bound[0]
        return self.recursiveCL(bound, 1, c, most_frequent)


    def privacy_analysis(self, original_frequency, modified_frequency, alpha):
     
        f_upper_bound, f_lower_bound = self.get_bounds(original_frequency)
        f_upper_sensitive, f_lower_sensitive = self.get_sensitive_frq(f_upper_bound, f_lower_bound)
        f_upper_sensitive_activities, f_lower_sensitive_activities = self.get_act(f_upper_sensitive, f_lower_sensitive, original_frequency)
     
        upper_bound, lower_bound = self.get_bounds(modified_frequency)
        upper_sensitive, lower_sensitive = self.get_sensitive_frq(upper_bound, lower_bound)
        upper_sensitive_activities, lower_sensitive_activities = self.get_act(upper_sensitive, lower_sensitive, modified_frequency)
        
        upper_sensitive_substitution, lower_sensitive_substitution = self.get_sub(f_upper_sensitive_activities, f_lower_sensitive_activities, modified_frequency)
        
        upper_instersection = set(upper_sensitive_substitution).intersection(set(upper_sensitive_activities))
        lower_instersection = set(lower_sensitive_substitution).intersection(lower_sensitive_activities)
        
        if(len(upper_sensitive_substitution) > 0):
            presence_upper = len(upper_instersection) / len(upper_sensitive_substitution)
        else:
            presence_upper = 0
        
        if(len(lower_sensitive_substitution) > 0):
            presence_lower = len(lower_instersection) / len(lower_sensitive_substitution)
        else:
            presence_lower = 0
            
        upper_sensitive.sort(reverse=True)
        lower_sensitive.sort(reverse=True)
        
        if(len(upper_sensitive) > 0):
            c = 1 + 1 / (len(upper_sensitive))
            l_upper = self.find_l(upper_sensitive, c)
        else:
            l_upper = 0 
            
        if(len(lower_sensitive) > 0):
            c = 1 + 1 / (len(lower_sensitive))
            l_lower = self.find_l(lower_sensitive, c)
        else:
            l_lower = 0
        
        if(l_upper == 0 or presence_upper == 0):
            upperDisclosure = 0
        else:
            # upperDisclosure = (len(upper_sensitive) - l_upper + 1) / len(upper_sensitive)
            upperDisclosure = 1 / len(upper_sensitive)
            
        if(l_lower == 0 or presence_lower == 0):
            lowerDisclosure = 0
        else:
            # lowerDisclosure = (len(lower_sensitive) - l_lower + 1) / len(lower_sensitive)
            lowerDisclosure = 1 / len(lower_sensitive)
                
        up_disclosure = presence_upper * upperDisclosure
        low_disclosure = presence_lower * lowerDisclosure
        
        Disclosure = alpha * up_disclosure + (1 - alpha) * low_disclosure
            
        print("presence upper: " , presence_upper)
        print("presence lower: ", presence_lower)
        
        print("upper DR: " , upperDisclosure)
        print("lower DR: ", lowerDisclosure)
        
        print("upper DR with presence: " , up_disclosure)
        print("lower DR with presence: ", low_disclosure)
        
        print("Disclosure: " , Disclosure)