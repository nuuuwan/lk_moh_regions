import json
import os
import random
from functools import cache

import geopandas as gpd
import matplotlib.pyplot as plt
import topojson


class MOH:
    DIR_ORIGINAL_DATA = os.path.join("original_data")
    DIR_DATA = os.path.join("data")
    DIR_DATA_GEO = os.path.join(DIR_DATA, "geo")
    DIR_DATA_ENT = os.path.join(DIR_DATA, "ent")

    SHP_PATH = os.path.join(DIR_ORIGINAL_DATA, "shp", "SL_MOH_GN.shp")
    GEOJSON_PATH = os.path.join(DIR_DATA_GEO, "moh.geojson")
    TOPOJSON_PATH = os.path.join(DIR_DATA_GEO, "moh.topojson")
    IMAGE_PATH = os.path.join(DIR_DATA_GEO, "moh.png")
    ENT_PATH = os.path.join(DIR_DATA_ENT, "moh.json")

    @staticmethod
    def build_geojson():
        gdf = gpd.read_file(MOH.SHP_PATH)
        gdf = gdf.set_crs(epsg=5234)
        gdf["geometry"] = gdf["geometry"].make_valid()
        moh = gdf.dissolve(by="MOH_N", as_index=False)[
            ["MOH_N", "DISTRICT_N", "PROVINCE_N", "geometry"]
        ]
        moh = moh.to_crs(epsg=4326)
        os.makedirs(MOH.DIR_DATA_GEO, exist_ok=True)
        moh.to_file(MOH.GEOJSON_PATH, driver="GeoJSON")
        print(f"Wrote {len(moh)} MOH regions to {MOH.GEOJSON_PATH}")
        return moh

    @staticmethod
    def build_topojson():
        moh = gpd.read_file(MOH.GEOJSON_PATH)
        moh["geometry"] = moh["geometry"].simplify(tolerance=0.001)
        topo = topojson.Topology(moh, prequantize=False)
        with open(MOH.TOPOJSON_PATH, "w") as f:
            json.dump(topo.to_dict(), f)
        print(f"Wrote simplified MOH regions to {MOH.TOPOJSON_PATH}")
        return moh

    @staticmethod
    def build_image():
        with open(MOH.TOPOJSON_PATH) as f:
            topo_dict = json.load(f)
        moh = topojson.Topology(topo_dict).to_gdf()
        colors = [
            f"#{random.randint(0, 0xFFFFFF):06x}" for _ in range(len(moh))
        ]
        fig, ax = plt.subplots(figsize=(8, 12))
        moh.plot(ax=ax, color=colors, edgecolor="white", linewidth=0.3)
        ax.axis("off")
        plt.tight_layout()
        plt.savefig(MOH.IMAGE_PATH, dpi=600, bbox_inches="tight")
        plt.close(fig)
        print(f"Wrote image to {MOH.IMAGE_PATH}")
        return MOH.IMAGE_PATH

    @staticmethod
    @cache
    def get_district_idx():
        districts = json.load(
            open(os.path.join(MOH.DIR_ORIGINAL_DATA, "ents", "districts.json"))
        )
        district_idx = {
            district["name"]: district["id"] for district in districts
        }
        return district_idx

    @staticmethod
    @cache
    def get_district_id(district_name):
        district_name = {
            "Monaragala": "Moneragala",
        }.get(district_name, district_name)
        district_idx = MOH.get_district_idx()
        return district_idx.get(district_name.title(), "None")

    @staticmethod
    def build_metadata():

        moh = gpd.read_file(MOH.GEOJSON_PATH)
        records = []
        for _, row in moh.iterrows():
            centroid = row.geometry.centroid
            records.append(
                {
                    "district_id": MOH.get_district_id(row["DISTRICT_N"]),
                    "region_name": row["MOH_N"].title(),
                    "centroid_lat": round(centroid.y, 6),
                    "centroid_lng": round(centroid.x, 6),
                }
            )
        records.sort(key=lambda x: (x["district_id"], x["region_name"]))

        os.makedirs(MOH.DIR_DATA_ENT, exist_ok=True)
        with open(MOH.ENT_PATH, "w") as f:
            json.dump(records, f, indent=2)
        print(f"Wrote {len(records)} MOH metadata records to {MOH.ENT_PATH}")
        return records

    @staticmethod
    def build():
        MOH.build_geojson()
        MOH.build_topojson()
        MOH.build_image()
        MOH.build_metadata()
