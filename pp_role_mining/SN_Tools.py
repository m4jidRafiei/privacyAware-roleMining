'''
@author: majid
'''
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import pandas as pd
from _collections import defaultdict
#from distributed.utils import resource
from scipy.stats import pearsonr
from _operator import index
from pp_role_mining.Utilities import Utilities



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

    
    def get_activity_from_substitution(self,activity_substitutions,sub_activity):
        for index, rowSub in activity_substitutions.iterrows():   
            if(sub_activity in rowSub['substitution_list']):
                return  rowSub['activity']
    
    def makeEmptyActRscMatrix(self):
        ActRscMatrix = np.zeros([len(self.activityList), len(self.resourceList)])  # +1 is just for considering <None>
        return ActRscMatrix;
    
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
        
