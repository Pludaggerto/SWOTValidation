# ---01--- 
"""To json"""
from Baser import Baser
import zipfile
import logging 
import os
import glob
import geopandas as gpd
import shutil

class DataArranger(Baser):

    def __init__(self, workspace = r"D:\SWOTValidate"):
        logging.info("[INFO]01 Data Arranging ...")
        super().__init__(workspace = workspace)

    def extract_data(self, datatype):
       # extract file
        subFolders = glob.glob(os.path.join(self.tempFolder, "SWOT*"))

        for subFolder in subFolders:

            filename = glob.glob(os.path.join(subFolder, "*.zip"))[0]

            with zipfile.ZipFile(filename, 'r') as zf:
                zf.extractall(subFolder)

            shpFile = glob.glob(os.path.join(subFolder, "*.shp"))[0]

            date = subFolder.split("_")[8].split("T")[0]
            Pass = subFolder.split("_")[6]
            continent = subFolder.split("_")[7]

            targetFolder = self.set_folder(self.SWOTdataFolder, datatype)
            gdf = gpd.read_file(shpFile)
            targetPath = os.path.join(targetFolder, date + "_" + Pass + "_" + continent + ".json")
            gdf.to_file(targetPath)
               
        return 

    def get_one_type_data(self, datatype):
       
        for folder in self.originDataFolders:

            logging.info("[INFO]01 extracting " + folder.split("_")[-1]  + " ...") 

            try:

                fileName = glob.glob(os.path.join(folder, "*" + datatype + "*"))[0]
                with zipfile.ZipFile(fileName, 'r') as zf:
                    zf.extractall(self.tempFolder)

                self.extract_data(datatype)

            except:

                logging.info("Error in" + folder)

            self.del_temp()


    def get_all_type_data(self):
        
        for datatype in self.datatypes:

            self.get_one_type_data(datatype)

    def del_temp(self):

        shutil.rmtree(self.tempFolder)

def main():

    log = logging.getLogger()
    handler = logging.StreamHandler()
    log.addHandler(handler)
    log.setLevel(logging.INFO)

    dataArranger = DataArranger()
    dataArranger.get_all_type_data()

if __name__ == '__main__':
    main()
