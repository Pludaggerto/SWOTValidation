from Baser import Baser
import logging 
import os
import glob
import geopandas as gpd
import pandas as pd
from tqdm import tqdm

class Joiner(Baser):

    def __init__(self, workspace = r"D:\SWOTValidate"):

        logging.info("[INFO]02 Data Joining ...")
        super().__init__(workspace = workspace)


    def select(self):

        station = gpd.read_file(self.station).to_crs(crs="EPSG:2380")
        for distance in [1000, 2000, 3000, 4000]:
            stationBuffer =  station.buffer(distance)
            dataRecords = []
            for subtype in ["Observed", "Prior", "Unassigned"]:
            
                subFolder = self.set_folder(self.SWOTdataFolder, subtype)
                subFiles = glob.glob(os.path.join(subFolder, "*.json"))

                targetFolder = self.set_folder(self.filterFolder, str(distance))
                targetFolder = self.set_folder(targetFolder, subtype)

                for subFile in subFiles:
                
                    # data
                    SWOTfile = gpd.read_file(subFile).to_crs(crs="EPSG:2380")
                    intersectData = SWOTfile[SWOTfile.intersects(stationBuffer)]

                    # station
                    intersectStation = station[station.intersects(SWOTfile)]

                    stnm = str(list(intersectStation["stnm"]))
                    stcd = str(list(intersectStation["stnm"]))

                    if not intersectData.empty:
                    
                        dataRecords.append([stnm, stcd, subtype, subFile.split("\\")[-1]])
                        targetFileName = os.path.join(targetFolder, subFile.split("\\")[-1])
                        logging.info("[INFO] outputing " + targetFileName)
                        intersectData.to_file(targetFileName)

            pd.DataFrame(dataRecords).to_csv(os.path.join(self.workspace, "StationIntersectRecord_" + str(distance) +  ".csv"))

    def select2(self):

        station = gpd.read_file(self.station).to_crs(crs="EPSG:2380")
        results = []

        for subtype in self.datatypes:

            subFolder = self.set_folder(self.SWOTdataFolder, subtype)
            subFiles = glob.glob(os.path.join(subFolder, "*.json"))

            targetFolder = self.set_folder(self.filterFolder, "nearest")
            targetFolder = self.set_folder(targetFolder, subtype)

            for subFile in tqdm(subFiles):
                
                # data
                SWOTfile = gpd.read_file(subFile).to_crs(crs="EPSG:2380")
                result = gpd.sjoin_nearest(SWOTfile, station, lsuffix='_SWOT', rsuffix='_station', distance_col = "distance")[["stcd", "distance"]]
                
                result["name"] = [subFile.split("\\")[-1].split(".")[0]] * len(result)
                results.append(result)

            pd.concat(results).to_csv(os.path.join(targetFolder, "nearest.csv"))

def main():

    log = logging.getLogger()
    handler = logging.StreamHandler()
    log.addHandler(handler)
    log.setLevel(logging.INFO)

    joiner = Joiner()
    joiner.select2()

if __name__ == '__main__':
    main()