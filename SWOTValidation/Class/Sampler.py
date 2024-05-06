from pandas.core.frame import DataFrame
from Baser import Baser
import logging 
import os
import glob
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
import geojson
from collections import Counter
import json

class Sampler(Baser):

    def __init__(self, workspace = r"D:\SWOTValidate"):

        logging.info("[INFO]02 Data Joining ...")
        super().__init__(workspace = workspace)

        self.reachFolder = os.path.join(self.SWOTdataFolder, "Reach")
        self.observedFolder = os.path.join(self.SWOTdataFolder, "Observed")

        self.ValidationFolder = self.set_folder(workspace, "ValidationDataset")

        self.selectedReachFolder = self.set_folder(self.ValidationFolder, "selectedReach")
        self.selectedLakeFolder  = self.set_folder(self.ValidationFolder, "selectedLake")
        self.selectedLakeChinaFolder  = self.set_folder(self.ValidationFolder, "selectedLakeChina")


    def reach_stat(self):

        # stat reach WIDTH

        reachFiles = glob.glob(os.path.join(self.reachFolder, "*.json"))
        cnt = Counter()
        for reachFile in tqdm(reachFiles):
            with open(reachFile) as f:
                reachJSON = geojson.load(f)["features"]
                for reach in reachJSON:
                    reachID = reach["properties"]['reach_id']
                    width = reach["properties"]['width']
                    if width < 100:
                        continue
                    else:
                        cnt[reachID] += 1
        pd.DataFrame(cnt.items(),columns=['label','counts']).to_csv(os.path.join(self.reachFolder, "stat.csv"), 
                                                                    index = False, mode = "w+")

    def lake_stat(self):

        # stat Lake Observed

        observedFiles = glob.glob(os.path.join(self.observedFolder, "*.json"))
        cnt = Counter()
        for observedFile in tqdm(observedFiles):
            with open(observedFile) as f:
                observedJSON = geojson.load(f)["features"]
                for observed in observedJSON:
                    lakeId = observed["properties"]['lake_id']
                    area = observed["properties"]['area_total']
                    if area < 1:
                        continue
                    else:
                        cnt[lakeId] += 1
        cnt2 = Counter()
        for key in cnt.keys():
            if ";" not in key:
                cnt2[key] += cnt[key]
            else:
                for lakeid in key.split(";"):
                    cnt2[lakeid] += cnt[key]
        pd.DataFrame(cnt.items(),columns=['label', 'counts']).to_csv(os.path.join(self.observedFolder, "stat.csv"), index = False)
        pd.DataFrame(cnt2.items(),columns=['label', 'counts']).to_csv(os.path.join(self.observedFolder, "stat2.csv"), index = False)

    def lake_stat_china(self):

        # stat Lake Observed in china
        china = gpd.read_file(r"D:\test\China_84.shp").to_crs(4326)
        observedFiles = glob.glob(os.path.join(self.observedFolder, "*.json"))
        cnt = Counter()
        for observedFile in tqdm(observedFiles):
            observedJSON = gpd.read_file(observedFile).clip(china)
            observedJSON = observedJSON[observedJSON["area_total"] > 1]
            for lakeId in observedJSON["lake_id"]:
                cnt[lakeId] += 1                   
        cnt2 = Counter()
        for key in cnt.keys():
            if ";" not in key:
                cnt2[key] += cnt[key]
            else:
                for lakeid in key.split(";"):
                    cnt2[lakeid] += cnt[key]
        pd.DataFrame(cnt.items(),columns=['label', 'counts']).to_csv(os.path.join(self.observedFolder, "stat_china.csv"), index = False)
        pd.DataFrame(cnt2.items(),columns=['label', 'counts']).to_csv(os.path.join(self.observedFolder, "stat2_china.csv"), index = False)
    
    def select_pos(self):
        
        # lake to be selected
        lakeStat  = pd.read_csv(os.path.join(self.observedFolder, "stat2.csv"))
        lakeSelected = lakeStat[lakeStat["counts"] > 10]
        observedFiles = glob.glob(os.path.join(self.observedFolder, "*.json"))

        for lake in tqdm(list(lakeSelected["label"])):

            mergedCounts = 0

            for observedFile in observedFiles:
                
                gdf = gpd.read_file(observedFile)

                if sum(gdf['lake_id'].str.contains(str(lake))) > 0:
                    
                    if mergedCounts == 0:

                        selectedLake = gdf[(gdf['lake_id'].str.contains(str(lake)))]
                        mergedCounts += 1

                    else:
                        
                        selectedLake = selectedLake.append(gdf[(gdf['lake_id'].str.contains(str(lake)))])

            selectedLake.to_file(os.path.join(self.selectedLakeFolder, str(lake) + ".json"))

    def select_pos_china(self):
        
        # lake to be selected
        lakeStat  = pd.read_csv(os.path.join(self.observedFolder, "stat2_china.csv"))
        lakeSelected = lakeStat[(lakeStat["counts"] > 15) & (lakeStat["counts"] < 20)]
        observedFiles = glob.glob(os.path.join(self.observedFolder, "*.json"))

        for lake in tqdm(list(lakeSelected["label"])):

            mergedCounts = 0

            for observedFile in observedFiles:
                
                gdf = gpd.read_file(observedFile)

                if sum(gdf['lake_id'].str.contains(str(lake))) > 0:
                    
                    if mergedCounts == 0:

                        selectedLake = gdf[(gdf['lake_id'].str.contains(str(lake)))]
                        mergedCounts += 1

                    else:
                        
                        selectedLake = selectedLake.append(gdf[(gdf['lake_id'].str.contains(str(lake)))])

            selectedLake.to_file(os.path.join(self.selectedLakeChinaFolder, str(lake) + ".json"))


    def get_location_genpoint(self):

        result = []
        selectedLakes = glob.glob(os.path.join(self.selectedLakeFolder, "*.json"))
        for selectedLake in selectedLakes:
            gdf = gpd.read_file(selectedLake)
            result.append([gdf.centroid[0], selectedLake.split("\\")[-1].split(".")[0]])

        df = pd.DataFrame(result, columns=["geometry", "LakeID"])
        gdf = gpd.GeoDataFrame(df, geometry=df["geometry"]).to_crs(4326)
        gdf.to_file(os.path.join(self.selectedLakeFolder, "lakeSelectedPoint.shp"))

    def get_location_genpoint_china(self):

        result = []
        selectedLakes = glob.glob(os.path.join(self.selectedLakeChinaFolder, "*.json"))
        for selectedLake in selectedLakes:
            gdf = gpd.read_file(selectedLake)
            result.append([gdf.centroid[0], selectedLake.split("\\")[-1].split(".")[0]])

        df = pd.DataFrame(result, columns = ["geometry", "LakeID"])
        gdf = gpd.GeoDataFrame(df, geometry = df["geometry"])
        gdf.crs = "EPSG:4326"
        gdf.to_file(os.path.join(self.selectedLakeChinaFolder, "lakeSelectedPoint.shp"))

    def select_pos_china_by_lakeID(self, lake):
        observedFiles = glob.glob(os.path.join(self.observedFolder, "*.json"))
        mergedCounts = 0

        for observedFile in observedFiles:
                
            gdf = gpd.read_file(observedFile)

            if sum(gdf['lake_id'].str.contains(str(lake))) > 0:
                    
                if mergedCounts == 0:

                    selectedLake = gdf[(gdf['lake_id'].str.contains(str(lake)))]
                    mergedCounts += 1

                else:
                        
                    selectedLake = selectedLake.append(gdf[(gdf['lake_id'].str.contains(str(lake)))])

        selectedLake.to_file(os.path.join(self.selectedLakeChinaFolder, str(lake) + ".json"))

        return

    def run_all(self):
        #self.lake_stat_china()
        #self.select_pos_china()
        #self.get_location_genpoint_china()
        self.select_pos_china_by_lakeID("4560037932")

def main():

    log = logging.getLogger()
    handler = logging.StreamHandler()
    log.addHandler(handler)
    log.setLevel(logging.INFO)

    sampler = Sampler()
    sampler.run_all()


if __name__ == '__main__':
    main()
