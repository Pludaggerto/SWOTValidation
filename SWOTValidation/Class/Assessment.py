import os
import matplotlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class ValGroup(object):
    """a pre and tru group class -- 20220417"""

    def __init__(self, pre, tru, method = "Noname"):

        if type(pre) == list:
            pre = np.asarray(pre)
        if type(tru) == list:
            tru = np.asarray(tru)

        if type(pre) == pd.Series:
            pre = np.asarray(pre)
        if type(tru) == pd.Series:
            tru = np.asarray(tru)

        if(pre.size != tru.size):
            return
        self.predictArray = pre.flatten()
        self.trueArray    = tru.flatten()
        self.method       = method

class Assessment(object):
    """a class that using ValGroup class to assemble the analysis result -- 20220417"""
    def __init__(self, valGroupList):
        self.path = os.getcwd()
        if type(valGroupList) == ValGroup:
            self.valGroupList = [Assessment.cal_one_error(valGroupList)]

        if type(valGroupList) == list:
            self.valGroupList = Assessment.cal_many_error(valGroupList)

    @staticmethod
    def cal_one_error(valGroup):
        pre  = valGroup.predictArray
        tru  = valGroup.trueArray

        df = pd.DataFrame(np.vstack((tru,pre)).transpose())

        valGroup.RMSE     = np.sqrt(np.mean((pre - tru) ** 2)) 
        valGroup.R2pear   = df.corr(method='pearson')[0][1]
        valGroup.R2ken    = df.corr(method='kendall')[0][1]
        valGroup.R2spear  = df.corr(method='spearman')[0][1]
        mask = tru != 0
        tru_nozero = tru[mask]
        pre_nozero = pre[mask]
        valGroup.rRMSE    = np.sqrt(np.mean(((pre_nozero - tru_nozero) / tru_nozero)** 2)) 
        valGroup.maxerror = np.abs(pre - tru).max()
        valGroup.nRMSE    = np.sqrt(np.mean(((pre - tru) / np.mean(pre- tru))** 2)) 

        return valGroup

    @staticmethod
    def cal_many_error(valGroupList):
        result = []
        for valGroup in valGroupList:
            result.append(Assessment.cal_one_error(valGroup))
        return result
    
    def append(self, valGroups):
        if type(valGroups) == ValGroup:
            self.valGroupList.append(Assessment.cal_one_error(valGroups))

        if type(valGroups) == list:
            for valGroup in valGroups:
                self.valGroupList.append(Assessment.cal_one_error(valGroup))

    def error_histor(self):
        for valGroup in self.valGroupList:
            error = valGroup.predictArray - valGroup.trueArray
            fig = plt.figure(figsize=(15, 9))
            plt.hist(error, bins = 20) 
            plt.title("Error", fontsize = 10) 
            plt.xlabel("bias", fontsize = 8)
            plt.ylabel("times",  fontsize = 8)
            plt.savefig(self.path + "\\" + valGroup.method +".jpg", dpi = 300)
            plt.close()
        return None

    def to_dataframe(self):
        name     = []
        RMSE     = []
        R2pear   = []
        R2ken    = []
        R2spear  = []
        rRMSE    = []
        maxerror = []
        nRMSE    = []

        for valGroup in self.valGroupList:
            name.append(valGroup.method)
            RMSE.append(valGroup.RMSE)
            R2pear.append(valGroup.R2pear)
            R2ken.append(valGroup.R2ken)
            R2spear.append(valGroup.R2spear)
            rRMSE.append(valGroup.rRMSE)
            maxerror.append(valGroup.maxerror)
            nRMSE.append(valGroup.nRMSE)

        df = pd.DataFrame(np.asarray([RMSE, R2pear, R2ken, R2spear, rRMSE, maxerror, nRMSE]).transpose())
        col = ["RMSE", "R2pear", "R2ken", "R2spear", "rRMSE", "maxerror", "nRMSE"]

        df.index = name
        df.columns = col
        self.dataframe = df

        return df

    def to_csv(self, name = "result.csv"):
        df = self.to_dataframe()
        if os.path.exists(name):
            df.to_csv(name, mode = "a", header = None)
        else:
            df.to_csv(name, mode = "a")
        return None
    
    def print(self):
        print(self.to_dataframe())
        return None