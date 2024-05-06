import os
import glob

class Baser(object):

    def __init__(self, workspace = r"D:\SWOTValidate"):

        # folder
        self.workspace = workspace 
        self.originFolder      = self.set_folder(self.workspace, "origin")
        self.originDataFolders = glob.glob(os.path.join(self.originFolder, "04*"))
        self.SWOTdataFolder = self.set_folder(self.workspace, "SWOTData")
        self.tempFolder = self.set_folder(self.workspace, "temp")
        self.filterFolder = self.set_folder(self.workspace, "filter")

        # file
        self.station = os.path.join(self.workspace, "station\\station.json")

        # variables
        self.datatypes = ["Observed", "Prior", "Unassigned", "Node", "Reach"]

    @staticmethod
    def set_folder(folder, name):

        path = os.path.join(folder, name)
        if not os.path.exists(path):
            os.mkdir(path)
        return path


            
        

