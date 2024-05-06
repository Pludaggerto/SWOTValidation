from pandas.core.frame import DataFrame
from Baser import Baser
import logging 
import os
import glob
import geopandas as gpd
import pandas as pd
from tqdm import tqdm
import seaborn as sns
from matplotlib import pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib import rcParams
from matplotlib.ticker import FormatStrFormatter
plt.rcParams['font.family'] = ['Times New Roman']
import matplotlib
class Comparer(Baser):

    def __init__(self, workspace = r"D:\SWOTValidate"):

        logging.info("[INFO]02 Data Comparing ...")
        super().__init__(workspace = workspace)

        self.reachFolder = os.path.join(self.SWOTdataFolder, "Reach")
        self.observedFolder = os.path.join(self.SWOTdataFolder, "Observed")

        self.ValidationFolder    = self.set_folder(workspace, "ValidationDataset")
        self.SentinelDataFolder  = self.set_folder(self.ValidationFolder, "TrueLake")
        self.SentinelImageFolder = self.set_folder(self.SentinelDataFolder, "Image")
        self.SentinelPolygonFolder = self.set_folder(self.SentinelDataFolder, "Polygon")
        self.SentinelNamedPolygonFolder = self.set_folder(self.SentinelDataFolder, "NamedPolygon")

        self.selectedReachFolder = self.set_folder(self.ValidationFolder, "selectedReach")
        self.selectedLakeFolder  = self.set_folder(self.ValidationFolder, "selectedLake")
        self.selectedLakeChinaFolder  = self.set_folder(self.ValidationFolder, "selectedLakeChina")
        self.selectedPolygonFolder  = self.set_folder(self.ValidationFolder, "selectedPolygon")
        self.imageFolder  = self.set_folder(self.ValidationFolder, "Image")
        self.fontProperties = FontProperties(fname = r"C:\Users\hp\source\repos\SWOTLakeSimu\SWOTLakeSimu\font\STSong.ttf")

    def to_chs_name(self, key):

        nameDict = { "AksaiChin" : "阿克赛钦湖", "dengjingcuo" : "登静错", "hashihapao": "哈什哈泡",
                     "huashuchuan" : "桦树川水库", "jiezechaka" : "结则茶卡", "lac" : "拉昂错", 
                     "maojiacun" : "毛家村水库", "xianghe" : "襄河水库", "xiangmoshan" : "香磨山水库",
                     "xiaohaizi" : "小海子水库", "yuejinpao" : "跃进泡" , "lac" : "拉昂错", "rebangcuo": "热邦错"}
        if key in nameDict.keys():
            return nameDict[key]
        return key

    def to_shp(self):
        import arcpy
        arcpy.env.workspace = self.tempFolder
        arcpy.env.overwriteOutput = True
        AWEIImages = glob.glob(os.path.join(self.SentinelImageFolder, "AWEI_*.tif"))
        for AWEIImage in AWEIImages:
            AWEIPolygon = AWEIImage.split("\\")[-1].split(".")[0] + ".shp"
            lakeMask = arcpy.sa.Con(arcpy.Raster(AWEIImage), 1)
            target = os.path.join(self.SentinelPolygonFolder, AWEIPolygon)
            arcpy.RasterToPolygon_conversion(lakeMask, target, "NO_SIMPLIFY")     
            areas = []
            with arcpy.da.SearchCursor(target, ["SHAPE@AREA"]) as cursor:
                for row in cursor:
                    areas.append(row[0])
            areas.sort()
            if len(areas) > 2:
                areaBound = areas[-2]
                with arcpy.da.UpdateCursor(target, ["SHAPE@AREA"]) as cursor:
                    for row in cursor:
                        if row[0] < areaBound:
                            cursor.deleteRow()           
                del row
                del cursor

    def match_and_tochs(self):
        AWEIPolygons = glob.glob(os.path.join(self.SentinelPolygonFolder, "AWEI_*.shp"))
        SWOTshpPoint1 = gpd.read_file(os.path.join(self.selectedLakeChinaFolder, "lakeSelectedPoint.shp"))
        SWOTshpPoint2 = gpd.read_file(os.path.join(self.selectedLakeFolder, "lakeSelectedPointChina.shp"))
        for AWEIPolygon in AWEIPolygons:
            AWEIPolygonGDF = gpd.read_file(AWEIPolygon)
            intersections = gpd.sjoin(AWEIPolygonGDF, SWOTshpPoint1, how = 'inner', op = 'intersects')
            if intersections.empty:
                intersections = gpd.sjoin(AWEIPolygonGDF, SWOTshpPoint2, how = 'inner', op = 'intersects')

            if intersections.empty:
                intersections = gpd.sjoin_nearest(AWEIPolygonGDF, SWOTshpPoint2, how = 'inner')
            lakeID = intersections["LakeID"].values[0]
            if "lac" in AWEIPolygon:
                lakeID = "4560037932"
            lakeName = self.to_chs_name(AWEIPolygon.split("\\")[-1].split("_")[-1].split(".")[0])
            AWEIPolygonGDF.to_file(os.path.join(self.SentinelNamedPolygonFolder, lakeID + "_" + lakeName + "_tru.shp"))

    def merge(self, gdf):
        # base on observed time
        baseList = np.asarray(gdf["time_tai"][1:]) - np.asarray(gdf["time_tai"][:-1]) > 1e4
        returnList = []
        i = 0
        for base in baseList:
            returnList.append(i)
            if base == True:
                i = i + 1
        returnList.append(i)
        gdf["dissolve"] = returnList
        return gdf

    def plot(self):
        fig, axes = plt.subplots(3, 3, figsize=(15, 15))
        truePolygons = glob.glob(os.path.join(self.SentinelNamedPolygonFolder, "*_tru.shp"))
        i = 0
        subtitles = np.asarray([["(a)", "(b)", "(c)"], ["(d)", "(e)", "(f)"], ["(g)", "(h)", "(i)"]])
        subtitles = subtitles.flatten()
        plt.subplots_adjust(wspace = 0.15, hspace = 0.3)
        for truePolygon in truePolygons:
            ax = axes.flatten()[i]
            lakeID = truePolygon.split("\\")[-1].split("_")[0]
            SWOTPolygon = gpd.read_file(os.path.join(self.selectedPolygonFolder, lakeID + ".json"))
            SWOTPolygon = self.merge(SWOTPolygon)
            SWOTPolygonMerged = SWOTPolygon.dissolve(by = "dissolve")
            areaSeries = SWOTPolygonMerged.to_crs(32649).area
            SWOTPolygonMerged.to_file(os.path.join(self.SentinelNamedPolygonFolder, "_".join(truePolygon.split("_")[:-1]) + "_sim.shp"))
            SWOTPolygon["time_datetime"] = pd.to_datetime(SWOTPolygon["time_str"])
            date = SWOTPolygon.drop_duplicates(subset = "dissolve")["time_datetime"]

            truePolygonGDF = gpd.read_file(truePolygon).to_crs(32649)
            trueArea = truePolygonGDF.area.sum()

            ax.plot(date, areaSeries, marker = "o", label = "SWOT湖泊面积", lw = 1)     
            ax.axhline(y = trueArea, color='r', linestyle='--', label = "Sentinel-2湖泊面积" , lw = 1)
            ax.axhline(y = areaSeries.mean(), color='#2878b5', linestyle='--', label = "SWOT湖泊平均面积", lw = 1)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)      
                
            if "桦树川水库" in truePolygon:
                ax.set_ylim(5 * 1e6, 6.5 * 1e6)

            if "跃进泡" in truePolygon:
                ax.set_ylim(7 * 1e6, 10 * 1e6)

            if "香磨山水库" in truePolygon:
                ax.set_ylim(8 * 1e6, 1.3 * 1e7) 

            if "哈什哈泡" in truePolygon:
                ax.set_ylim(4.5 * 1e6, 7 * 1e6)
                
            if "襄河水库" in truePolygon:
                ax.set_ylim(2 * 1e6, 5 * 1e6)

            if "拉昂错" in truePolygon:
                ax.set_ylim(2 * 1e8, 8 * 1e8)

            if "热邦错" in truePolygon:
                ax.set_ylim(6 * 1e7, 7 * 1e7)

            if "小海子水库" in truePolygon:
                ax.set_ylim(1.1 * 1e8, 1.3 * 1e8)

            if "阿克赛钦湖" in truePolygon:
                ax.set_ylim(2.5 * 1e8, 5 * 1e8)

            if "登静错" in truePolygon:
                ax.set_ylim(0.3 * 1e7, 1.3 * 1e7)

            y_major_locator = plt.LinearLocator(6)
            ax.yaxis.set_major_locator(y_major_locator)
            ax.legend(prop = self.fontProperties, fontsize = 3)
            x_major_locator = plt.LinearLocator(6)
            ax.xaxis.set_major_locator(x_major_locator)

            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%m-%d'))
            x1_label = ax.get_xticklabels() 
            [x1_label_temp.set_fontname('Times New Roman')  for x1_label_temp in x1_label]
            [x1_label_temp.set_fontsize(11)  for x1_label_temp in x1_label]

            y1_label = ax.get_yticklabels() 
            [y1_label_temp.set_fontname('Times New Roman') for y1_label_temp in y1_label]        
            [y1_label_temp.set_fontsize(11)  for y1_label_temp in y1_label]

            ax.set_xlabel("")
            ax.set_ylabel("")
            name = truePolygon.split("\\")[-1].split(".")[0].split("_")[1]
            ax.set_title(subtitles[i] + " " + name, fontproperties  = self.fontProperties, size = 13)
            i = i + 1
        plt.text(0.5, 0.06, "日期", family = "STZhongsong", fontsize = 14, transform = fig.transFigure)
        plt.text(0.08, 0.45, "面积($m^2$)", family = "STZhongsong", rotation='vertical', fontsize = 14, transform = fig.transFigure)
        
        plt.savefig(os.path.join(self.imageFolder,  "total.png"), dpi = 400, bbox_inches='tight')
        plt.show()

    def run_all(self):
        #self.to_shp()
        self.match_and_tochs()
        self.plot()

def main():

    log = logging.getLogger()
    handler = logging.StreamHandler()
    log.addHandler(handler)
    log.setLevel(logging.INFO)

    comparer = Comparer()
    comparer.run_all()


if __name__ == '__main__':
    main()
