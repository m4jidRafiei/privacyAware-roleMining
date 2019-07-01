'''
Created on Oct 5, 2018

@author: majid
'''
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import pandas as pd
from _collections import defaultdict
from distributed.utils import resource
from scipy.stats import pearsonr
from pandas.testing import assert_frame_equal
import multiprocessing as mp
import psutil
import math
from math import floor
from _operator import index
from pm4py.visualization.dfg import factory as dfg_vis_factory
from PP.Utilities import Utilities
import time


class SNCreator(object):
    
  

    def __init__(self, resourceList, activityList, snDataFrame):
        
        self.resourceList = resourceList.copy()
        self.activityList = activityList.copy()
        self.snDataFrame = snDataFrame
        
        self.RscRscMatrix = np.zeros([len(self.resourceList), len(self.resourceList)])
    
    def makeEmptyRscRscMatrix(self):
        RscRscMatrix = np.zeros([len(self.resourceList), len(self.resourceList)])  # +1 is just for considering <None>
        return RscRscMatrix;
    
    def makeEmptyActActMatrix(self):
        ActActMatrix = np.zeros([len(self.activityList), len(self.activityList)])  # +1 is just for considering <None>
        return ActActMatrix;
    
    def makeEmptyRscActMatrix(self):
        RscActMatrix = np.zeros([len(self.resourceList), len(self.activityList)])  # +1 is just for considering <None>
        return RscActMatrix;
    
    def makeHandoverMatrix(self):   
        RscRscMatrix = SNCreator.makeEmptyRscRscMatrix(self)
        
        for resource, next_resource in zip(self.snDataFrame['resource'], self.snDataFrame['next_resource']):
            RscRscMatrix[self.resourceList.index(resource)][self.resourceList.index(next_resource)] += 1
            
        return RscRscMatrix 
    
    def makeHandoverMatrix_connector(self):   
        RscRscMatrix = SNCreator.makeEmptyRscRscMatrix(self)
        
        for prev_resource, resource in zip(self.snDataFrame['prev_resource'], self.snDataFrame['resource']):
            if(prev_resource == ":Start:"):
                continue
            RscRscMatrix[self.resourceList.index(prev_resource)][self.resourceList.index(resource)] += 1
            
        return RscRscMatrix 
    
    def makeDFG_connector(self, frequency_threshold, encryption):   
        
        #edges
        groupedbyactivityPairs = self.snDataFrame.groupby(['prev_activity', 'activity']).size().reset_index(name='counts')
        
        #just to return as matrix
        ActActMatrix = SNCreator.makeEmptyActActMatrix(self)
        for prev_activity, activity in zip(self.snDataFrame['prev_activity'], self.snDataFrame['activity']):
            if(prev_activity == ":Start:"):
                continue
            ActActMatrix[self.activityList.index(prev_activity)][self.activityList.index(activity)] += 1
        
        edges_dict = {}
        #edges_list = []
        for index, row in groupedbyactivityPairs.iterrows():
            if(row['prev_activity'] == ":Start:"):
                continue
            #edge_dict = {}  
            edge_list = [] 
            
            if(encryption):
                edge_list.append(Utilities.AES_ECB_Encrypt(self, row['prev_activity'].encode('utf-8'))[0:5])
                edge_list.append(Utilities.AES_ECB_Encrypt(self, row['activity'].encode('utf-8'))[0:5])
            else:
                edge_list.append(row['prev_activity'])
                edge_list.append(row['activity'])
            edge_tuple = tuple(edge_list)
            if(row['counts'] > frequency_threshold):
                edges_dict[edge_tuple] = row['counts']
            #edges_list.append(edge_dict)
            #edges_dict.append(edge_dict)
        

        
        #nodes
        activity_frequencyDF = self.snDataFrame.groupby(['activity']).size().reset_index(name='counts')
        prev_activity_frequencyDF = self.snDataFrame.groupby(['prev_activity']).size().reset_index(name='counts')
        prev_activity_frequencyDF = prev_activity_frequencyDF.rename(columns={'prev_activity':'activity'})
        final_activity_fequency = pd.concat([activity_frequencyDF, prev_activity_frequencyDF]).drop_duplicates(subset='activity', keep="first").reset_index(drop=True) 
        
        
        nodes = final_activity_fequency.set_index('activity').T.to_dict('records')
        nodes[0].pop(':Start:')
        #Making encrypted nodes
        nodes_new = {}
        for key, value in nodes[0].items():
            nodes_new[Utilities.AES_ECB_Encrypt(self, key.encode('utf-8'))[0:5]] = value
        if(encryption):
            gviz = dfg_vis_factory.apply(edges_dict, activities_count=nodes_new, parameters={"format": "pdf"})
        else:
            gviz = dfg_vis_factory.apply(edges_dict, activities_count=nodes[0], parameters={"format": "pdf"})
        print("-----DFG time: " + str(time.clock()))
        dfg_vis_factory.view(gviz)
        dfg_vis_factory.save(gviz, "pm4py.png")
        
        return ActActMatrix

    
    def get_activity_from_substitution(self,activity_substitutions,sub_activity):
        for index, rowSub in activity_substitutions.iterrows():   
            if(sub_activity in rowSub['substitution_list']):
                return  rowSub['activity']
    
    def makeRealHandoverMatrix_afterDecompose(self,dependency_threshold,activity_substitutions):   
        RscRscMatrix = SNCreator.makeEmptyRscRscMatrix(self)
        
        groupedbyactivityPairs = self.snDataFrame.groupby(['activity', 'next_activity']).size().reset_index(name='counts')
        
        new_dataframe = pd.DataFrame(columns=['activity','next_activity','counts'])
    
        for row_index, row in groupedbyactivityPairs.iterrows():
            print("----------", row)
            new_row = {}
            activity_set = False
            next_activity_set = False
            for sub_index, rowSub in activity_substitutions.iterrows():   
                if(row['activity'] in rowSub['substitution_list']):
                    new_row['activity'] = rowSub['activity']
                    activity_set = True
                if(row['next_activity'] in rowSub['substitution_list']):
                    new_row['next_activity'] = rowSub['activity']
                    next_activity_set = True
                    
                if(activity_set and next_activity_set):
                    activity_set = False
                    next_activity_set = False
                    break
                
                        
            #if(new_dataframe.shape[0] > 0):
            if(((new_dataframe['activity'] == new_row['activity']) & (new_dataframe['next_activity'] == new_row['next_activity'])).any()):
                found_index = new_dataframe.index[(new_dataframe['activity'] == new_row['activity']) & (new_dataframe['next_activity'] == new_row['next_activity'])]
                new_dataframe.at[found_index[0], 'counts'] = new_dataframe.loc[found_index[0],'counts'] + row['counts']
            else:
                new_row['counts'] = row['counts']
                new_dataframe = new_dataframe.append(new_row, ignore_index=True)
                
        for index, row in self.snDataFrame.iterrows():
            activity = SNCreator.get_activity_from_substitution(self, activity_substitutions, row['activity'])
            next_activity = SNCreator.get_activity_from_substitution(self, activity_substitutions, row['next_activity'])
            ab = new_dataframe.loc[(new_dataframe['activity'] == activity) & (new_dataframe['next_activity'] == next_activity)]
            if(ab.empty):
                abn = 0
            else:
                abn = ab.iloc[0,2]
            
            ba = new_dataframe.loc[(new_dataframe['next_activity'] == activity) & (new_dataframe['activity'] == next_activity)]
            if(ba.empty):
                ban = 0
            else:
                ban = ab.iloc[0,2]
            if(activity == next_activity):
                dependency = (abn)/ (abn + 1)
            else:
                dependency = (abn - ban)/ (abn + ban + 1)
            
            if(dependency > dependency_threshold):
                RscRscMatrix[self.resourceList.index(row['resource'])][self.resourceList.index(row['next_resource'])] += 1
            
        return RscRscMatrix 
    
    def makeRealHandoverMatrix(self,dependency_threshold):   
        RscRscMatrix = SNCreator.makeEmptyRscRscMatrix(self)
        
        groupedbyactivityPairs = self.snDataFrame.groupby(['activity', 'next_activity']).size().reset_index(name='counts')
        
        
        for index, row in self.snDataFrame.iterrows():
            ab = groupedbyactivityPairs.loc[(groupedbyactivityPairs['activity'] == row['activity']) & (groupedbyactivityPairs['next_activity'] == row['next_activity'])]
            if(ab.empty):
                abn = 0
            else:
                abn = ab.iloc[0,2]
            ba = groupedbyactivityPairs.loc[(groupedbyactivityPairs['next_activity'] == row['activity']) & (groupedbyactivityPairs['activity'] == row['next_activity'])]
            if(ba.empty):
                ban = 0
            else:
                ban = ba.iloc[0,2]
            if(row['activity'] == row['next_activity']):
                dependency = (abn)/ (abn + 1)
            else:
                dependency = (abn - ban)/ (abn + ban + 1)
            
            if(dependency > dependency_threshold):
                RscRscMatrix[self.resourceList.index(row['resource'])][self.resourceList.index(row['next_resource'])] += 1
            
        return RscRscMatrix 
    
    def makeRealHandoverMatrix_connector(self,dependency_threshold):   
        RscRscMatrix = SNCreator.makeEmptyRscRscMatrix(self)
        
        groupedbyactivityPairs = self.snDataFrame.groupby(['prev_activity', 'activity']).size().reset_index(name='counts')
        
        
        for index, row in self.snDataFrame.iterrows():
            if(row['prev_activity'] == ':Start:'):
                continue
            
            ab = groupedbyactivityPairs.loc[(groupedbyactivityPairs['prev_activity'] == row['prev_activity']) & (groupedbyactivityPairs['activity'] == row['activity'])]
            if(ab.empty):
                abn = 0
            else:
                abn = ab.iloc[0,2]
            ba = groupedbyactivityPairs.loc[(groupedbyactivityPairs['activity'] == row['prev_activity']) & (groupedbyactivityPairs['prev_activity'] == row['activity'])]
            if(ba.empty):
                ban = 0
            else:
                ban = ba.iloc[0,2]
            if(row['activity'] == row['prev_activity']):
                dependency = (abn)/ (abn + 1)
            else:
                dependency = (abn - ban)/ (abn + ban + 1)
            
            if(dependency > dependency_threshold):
                RscRscMatrix[self.resourceList.index(row['prev_resource'])][self.resourceList.index(row['resource'])] += 1
                print(index)
            
        return RscRscMatrix 
    
    def makeRealHandoverMatrix_connector_fast(self,dependency_threshold):   
        RscRscMatrix = SNCreator.makeEmptyRscRscMatrix(self)
        
        groupedbyactivityPairs = self.snDataFrame.groupby(['prev_activity', 'activity']).size().reset_index(name='counts')
        
        
        groupedbyresourcePairs = self.snDataFrame.groupby(['prev_resource', 'resource']).apply(lambda x: x.index.tolist()).reset_index(name='indeces')
        
        
        for index_main, row in groupedbyresourcePairs.iterrows():
            if(row['prev_resource'] == ':Start:'):
                continue
            for index in row['indeces']:
                ab = groupedbyactivityPairs.loc[(groupedbyactivityPairs['prev_activity'] == self.snDataFrame.iloc[index]['prev_activity']) & 
                                                (groupedbyactivityPairs['activity'] == self.snDataFrame.iloc[index]['activity'])]
                
                if(ab.empty):
                    abn = 0
                else:
                    abn = ab.iloc[0,2]
                
            
                ba = groupedbyactivityPairs.loc[(groupedbyactivityPairs['activity'] == self.snDataFrame.iloc[index]['prev_activity']) & 
                                                (groupedbyactivityPairs['prev_activity'] == self.snDataFrame.iloc[index]['activity'])]
                if(ba.empty):
                    ban = 0
                else:
                    ban = ba.iloc[0,2]
                if(self.snDataFrame.iloc[index]['activity'] == self.snDataFrame.iloc[index]['prev_activity']):
                    dependency = (abn)/ (abn + 1)
                else:
                    dependency = (abn - ban)/ (abn + ban + 1)
                
                if(dependency > dependency_threshold):
                    RscRscMatrix[self.resourceList.index(row['prev_resource'])][self.resourceList.index(row['resource'])] += 1
                    print(index_main)
                
                
        return RscRscMatrix 
    
    
    def makeRealHandoverMatrix_connector_faster(self,dependency_threshold):   
        #RscRscMatrix = SNCreator.makeEmptyRscRscMatrix(self)
        
        groupedbyactivityPairs = self.snDataFrame.groupby(['prev_activity', 'activity']).size().reset_index(name='counts')
        
        
        groupedbyresourcePairs = self.snDataFrame.groupby(['prev_resource', 'resource']).apply(lambda x: x.index.tolist()).reset_index(name='indeces')
        
        
        #multi-threading
        n_cpus = psutil.cpu_count()
        
        #n_cpus = n_cpus + 8  #just test
        if(groupedbyresourcePairs.shape[0] > n_cpus):
            each_frame_count = floor(groupedbyresourcePairs.shape[0] / n_cpus)
        else:
            each_frame_count = 1
        #remaining_part = snFullDF.shape[0] % n_cpus
        
        list_df = [groupedbyresourcePairs[i:i+each_frame_count] for i in range(0,groupedbyresourcePairs.shape[0],each_frame_count)]
        
        manager = mp.Manager()
        return_list = manager.list()
        jobs = list()
        for i in range(0,len(list_df)):
            if(list_df[i].shape[0] > 0):
                p = mp.Process(target=SNCreator.decompose_worker, args=(self, list_df[i], groupedbyactivityPairs, self.RscRscMatrix, dependency_threshold))
                p.start()  
                jobs.append(p)
        for proc in jobs:
            proc.join()       
            print('joined')
        
            
        return self.RscRscMatrix 
    
    
    def decompose_worker(self, groupedbyresourcePairs, groupedbyactivityPairs, RscRscMatrix, dependency_threshold):
        
        for index_main, row in groupedbyresourcePairs.iterrows():
            if(row['prev_resource'] == ':Start:'):
                continue
            for index in row['indeces']:
                ab = groupedbyactivityPairs.loc[(groupedbyactivityPairs['prev_activity'] == self.snDataFrame.iloc[index]['prev_activity']) & 
                                                (groupedbyactivityPairs['activity'] == self.snDataFrame.iloc[index]['activity'])]
                
                if(ab.empty):
                    abn = 0
                else:
                    abn = ab.iloc[0,2]
                
            
                ba = groupedbyactivityPairs.loc[(groupedbyactivityPairs['activity'] == self.snDataFrame.iloc[index]['prev_activity']) & 
                                                (groupedbyactivityPairs['prev_activity'] == self.snDataFrame.iloc[index]['activity'])]
                if(ba.empty):
                    ban = 0
                else:
                    ban = ba.iloc[0,2]
                if(self.snDataFrame.iloc[index]['activity'] == self.snDataFrame.iloc[index]['prev_activity']):
                    dependency = (abn)/ (abn + 1)
                else:
                    dependency = (abn - ban)/ (abn + ban + 1)
                
                if(dependency > dependency_threshold):
                    RscRscMatrix[self.resourceList.index(row['prev_resource'])][self.resourceList.index(row['resource'])] += 1
                    print(index_main)
        
    
    def makeEmptyActRscMatrix(self):
        ActRscMatrix = np.zeros([len(self.activityList), len(self.resourceList)])  # +1 is just for considering <None>
        return ActRscMatrix;
    
    def makeJointActivityMatrix(self):
           
        allresources = np.concatenate([self.snDataFrame['resource'], self.snDataFrame['next_resource']], axis=0)
        allactivities = np.concatenate([self.snDataFrame['activity'], self.snDataFrame['next_activity']], axis=0)
           
        all_resource_activity = np.concatenate([allresources.reshape(len(allresources), 1), allactivities.reshape(len(allactivities), 1)], axis=1)
        all_resource_activity_df = pd.DataFrame(columns=['resource', 'activity'],
                                                data=all_resource_activity)
        
        groupedbyactivity = all_resource_activity_df.groupby(['resource'])
        resource_activity_dict = defaultdict(list)
        
        for resource, group in groupedbyactivity:
            resource_activity_dict[resource].append(group['activity'].values)  # if I use "values", for some values which are not start or end activities, we will have one more frequency (unique())
        
        RscActMatrix = SNCreator.makeEmptyRscActMatrix(self)
        
        for resource in resource_activity_dict:
            for activity_list in resource_activity_dict[resource]:
                for activity in activity_list:
                    RscActMatrix[self.resourceList.index(resource)][self.activityList.index(activity)] += 1
            
        return RscActMatrix
    
    def makeJointActivityMatrix_next(self):
           
        all_resource_activity = self.snDataFrame[['resource','activity']]
       
        groupedbyactivity = all_resource_activity.groupby(['resource'])
        resource_activity_dict = defaultdict(list)
        
        for resource, group in groupedbyactivity:
            resource_activity_dict[resource].append(group['activity'].values)  # if I use "values", for some values which are not start or end activities, we will have one more frequency (unique())
        
        RscActMatrix = SNCreator.makeEmptyRscActMatrix(self)
        
        for resource in resource_activity_dict:
            for activity_list in resource_activity_dict[resource]:
                for activity in activity_list:
                    RscActMatrix[self.resourceList.index(resource)][self.activityList.index(activity)] += 1
            
        return RscActMatrix
    
    def makeActivityRscMatrix(self):

        allresources = np.concatenate([self.snDataFrame['resource'], self.snDataFrame['next_resource']], axis=0)
        allactivities = np.concatenate([self.snDataFrame['activity'], self.snDataFrame['next_activity']], axis=0)
        
        all_resource_activity = np.concatenate([allresources.reshape(len(allresources), 1), allactivities.reshape(len(allactivities), 1)], axis=1)
        all_resource_activity_df = pd.DataFrame(columns=['resource', 'activity'],
                                                data=all_resource_activity)
        
        groupedbyactivity = all_resource_activity_df.groupby(['activity'])
        resource_activity_dict = defaultdict(list)
        
        for activity, group in groupedbyactivity:
            resource_activity_dict[activity].append(group['resource'].values)  # if I use "values", for some values which are not start or end activities, we will have one more frequency (unique())
        
        ActRscMatrix = SNCreator.makeEmptyActRscMatrix(self)
        
        for activity in resource_activity_dict:
            for resource_list in resource_activity_dict[activity]:
                for resource in resource_list:
                    ActRscMatrix[self.activityList.index(activity)][self.resourceList.index(resource)] += 1
            
        return ActRscMatrix
    
    def makeActivityPairs(self):
        groupedbyactivityPairs = self.snDataFrame.groupby(['activity', 'next_activity']).size().reset_index(name='counts')
        return groupedbyactivityPairs
    
    def compose_worker(self, list_dataframe,new_activityList,activity_substitutions,return_list):
         
        numpy_result = np.zeros([list_dataframe.shape[0],len(new_activityList)])
        count = 0 
        list_indexes = []
        for index_row, row in list_dataframe.iterrows():
            print("----------", row)
            for index_column, column in enumerate(row.values):
                for indexSub, rowSub in activity_substitutions.iterrows():
                    if(self.activityList[index_column] in rowSub['substitution_list']):
                        numpy_result[count][new_activityList.index(rowSub['activity'])] += column
            
            list_indexes.append(self.resourceList.index(index_row))
            count = count + 1 
            
        df_result = pd.DataFrame(numpy_result)
        return_list.append(list_indexes)
        return_list.append(df_result)
        
    
    def convertBack_JointActivityMatrix(self, RscActMatrix_jointactivities, activity_substitutions , new_activityList):
        
        numpy_result = np.zeros([len(self.resourceList),len(new_activityList)])

        for index_row, row in enumerate(RscActMatrix_jointactivities):
            print("----------", row)
            for index_column, column in enumerate(row):
                activity = SNCreator.get_activity_from_substitution(self, activity_substitutions, self.activityList[index_column])
                numpy_result[index_row][new_activityList.index(activity)] += column
            
        return numpy_result

    
    def my_similarity(self, resource_1, resource_2, all_zero):
        if(all_zero == False):
            if(np.count_nonzero(resource_1) == 0 or np.count_nonzero(resource_2) == 0):
                return 0  
        # we just ignore the points where both vectors are zero
        ignores = 0
        for index in range(len(resource_1)):
            if(resource_1[index] == 0 and resource_2[index] == 0):
                ignores += 1
        
        differences = 0
        for index in range(len(resource_1)):
            if((resource_1[index] == 0 and resource_2[index] != 0) or 
               (resource_2[index] == 0 and resource_1[index] != 0)):
                differences += 1
                
        nonZeros = len(resource_1) - ignores
        return 1 - differences / nonZeros
    
        
    
    def hamming(self, resource_1, resource_2, all_zero):
        if(all_zero == False):
            if(np.count_nonzero(resource_1) == 0 or np.count_nonzero(resource_2) == 0):
                return 0  
        
        differences = 0
        for index in range(len(resource_1)):
            if((resource_1[index] == 0 and resource_2[index] != 0) or 
               (resource_2[index] == 0 and resource_1[index] != 0)):
                differences += 1
                
        return 1 - differences / len(resource_1)
    
    def convertRscAct2RscRsc(self, RscActMatrix, method):
        RscRscMatrix = SNCreator.makeEmptyRscRscMatrix(self)
        for index, resouce in enumerate(RscActMatrix):
            for rest in range(index + 1, RscActMatrix.shape[0]):
                main_resource = resouce
                other_resource = RscActMatrix[rest]
                if(method == "pearson"):
                    r, p = pearsonr(main_resource, other_resource)
                    RscRscMatrix[index][rest] = r 
                elif(method == "mine"):
                    similarity = SNCreator.my_similarity(self, main_resource, other_resource, False)
                    RscRscMatrix[index][rest] = similarity
                elif(method == "hamming"):
                    similarity = SNCreator.hamming(self, main_resource, other_resource, False)
                    RscRscMatrix[index][rest] = similarity
        return RscRscMatrix
    
    def getResourceList(self):
        return self.resourceList
    
    def setResourceList(self, resourceList):
        self.resourceList = resourceList.copy()

    def setActivityList(self, activityList):
        self.activityList = activityList.copy()
    
    def getActivityList(self):
        return self.activityList
        
    def drawRscRscGraph_simple(self, RscRscMatrix, weight_threshold, directed):
        rows, cols = np.where(RscRscMatrix > weight_threshold)
        edges = zip(rows.tolist(), cols.tolist())
        
        if(directed):
            G = nx.DiGraph()
        else:
            G = nx.Graph()
       
        labels = {}
        nodes = []
        for index, item in enumerate(self.resourceList):
            labels[index] = item
            nodes.append(index)
            
        G.add_nodes_from(nodes)  
        G.add_edges_from(edges)
        nx.draw(G, with_labels=True, node_color=['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0'], labels=labels, node_size=500, pos=nx.circular_layout(G))
        plt.show()
            
    def drawRscRscGraph_advanced(self, RscRscMatrix, weight_threshold, directed, encryption):
        
        rows, cols = np.where(RscRscMatrix > weight_threshold)
        weights = list();
        
        for x in range(len(rows)):
            weights.append(RscRscMatrix[rows[x]][cols[x]])
        
        #got_net = Network(height="750px", width="100%", bgcolor="white", font_color="#3de975", directed=directed)
        got_net = Network(height="750px", width="100%", bgcolor="white", font_color="black", directed=directed)
        ##f57b2b
        # set the physics layout of the network
        got_net.barnes_hut()
      
        edge_data = zip(rows, cols, weights)
        
        for e in edge_data:
            
            src = self.resourceList[e[0]]  # convert ids to labels
            dst = self.resourceList[e[1]]
            w = e[2] 
            
            if(encryption):
                src = Utilities.AES_ECB_Encrypt(self,src.encode('utf-8'))
                dst = Utilities.AES_ECB_Encrypt(self,dst.encode('utf-8'))
                
            # I have to add some options here, there is no parameter
            highlight = {'border': "#3de975", 'background': "#41e9df"}
            #color = {'border': "#000000", 'background': "#123456"}
            got_net.add_node(src, src, title=src, labelHighlightBold=True, color={'highlight': highlight})
            got_net.add_node(dst, dst, title=dst , labelHighlightBold=True, color={'highlight': highlight})
            got_net.add_edge(src, dst, value=w, title=w)
        
        neighbor_map = got_net.get_adj_list()
        
        dict = got_net.get_edges()
        
        self.getResourceList()
        
        # add neighbor data to node hover data
        for node in got_net.nodes:
            counter = 0
            if(directed):
                node["title"] = "<h3>" + node["title"] + " Output Links: </h3>"
            else:
                node["title"] = "<h3>" + node["title"] + " Links: </h3>"
            for neighbor in neighbor_map[node["id"]]:
                if(counter % 10 == 0):
                    node["title"] += "<br>::: " + neighbor        
                else:
                    node["title"] += " ::: " + neighbor
                node["value"] = len(neighbor_map[node["id"]])
                counter += 1
        
        got_net.show_buttons(filter_=['nodes', 'edges', 'physics'])
        got_net.show_buttons(filter_=['physics'])
        
        got_net.show("PMSocial.html")
        
    def drawActivityResourceGraph_advanced(self, ActivityRscMatrix, weight_threshold, directed, splitted):
        
        rows, cols = np.where(ActivityRscMatrix > weight_threshold)
        weights = list();
        
        for x in range(len(rows)):
            weights.append(ActivityRscMatrix[rows[x]][cols[x]])
        
        got_net = Network(height="750px", width="100%", bgcolor="black", font_color="#f57b2b", directed= directed)
        
        # set the physics layout of the network
        got_net.barnes_hut()
      
        edge_data = zip(rows, cols, weights)
        
        counter = 1
        for e in edge_data:
            src = self.activityList[e[0]]  # convert ids to labels
            dst = self.resourceList[e[1]]
            w = e[2] 
    
            # I have to add some options here, there is no parameter
            highlight = {'border': "#3de975", 'background': "#41e9df"}
            if(splitted):
                got_net.add_node(src, src, title=src, labelHighlightBold=True, color={'highlight': highlight},shape='square')
                got_net.add_node(dst+ "__" +str(counter) , dst , title=dst , labelHighlightBold=True, color={'border': "#dd4b39", 'background': "#dd4b39", 'highlight': highlight})
                got_net.add_edge(src, dst+ "__" +str(counter), value=w, title=w)
                counter +=1
            else:
                got_net.add_node(src, src, title=src, labelHighlightBold=True, color={'highlight': highlight},shape='square')
                got_net.add_node(dst , dst, title=dst , labelHighlightBold=True, color={'border': "#dd4b39", 'background': "#dd4b39", 'highlight': highlight})
                got_net.add_edge(src, dst , value=w, title=w)

        neighbor_map = got_net.get_adj_list()
        
        dict = got_net.get_edges()
        
        self.getResourceList()
        
        # add neighbor data to node hover data
        for node in got_net.nodes:
            counter = 0
            if(directed):
                node["title"] = "<h3>" + node["title"] + " Output Links: </h3>"
            else:
                node["title"] = "<h3>" + node["title"] + " Links: </h3>"
            for neighbor in neighbor_map[node["id"]]:
                if(counter % 10 == 0):
                    node["title"] += "<br>::: " + neighbor        
                else:
                    node["title"] += " ::: " + neighbor
                node["value"] = len(neighbor_map[node["id"]])
                counter += 1
        
        got_net.show_buttons(filter_=['nodes', 'edges', 'physics'])
        got_net.show_buttons(filter_=['physics'])
        
        got_net.show("PMSocial.html")
        
