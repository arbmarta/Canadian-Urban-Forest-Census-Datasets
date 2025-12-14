import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import warnings
from collections import defaultdict

## --------------------------------------------------- LOAD DATASETS ---------------------------------------------------
#region

# Load tabular data
csd = pd.read_csv('Datasets/Outputs/urban_csds/urban_csds_attributes.csv')
roads = pd.read_csv('Datasets/Outputs/roads/road_lengths_by_csd.csv')
canopy_csds = pd.read_csv('Datasets/Outputs/gee_export/canopy_cover_csd.csv')
canopy_roads_10m = pd.read_csv('Datasets/Outputs/gee_export/canopy_cover_road_buffers_10m.csv')
canopy_roads_20m = pd.read_csv('Datasets/Outputs/gee_export/canopy_cover_road_buffers_20m.csv')
census = pd.read_csv('Datasets/Outputs/2021_census_of_population/2021_census_of_population_municipalities.csv')

# Load spatial data
provinces = gpd.read_file('Datasets/Inputs/provinces/provinces_simplified_1km.gpkg')
csds = gpd.read_file('Datasets/Outputs/urban_csd_centroids/urban_csd_centroids.gpkg')
ecozones = gpd.read_file('Datasets/Inputs/ecozone_shp/ecozones.shp')
ecozones = ecozones.to_crs(provinces.crs)  # match ecozone CRS to provinces

print("\n" + "=" * 70)
print("IMPORTING DATASETS")
print("=" * 70)

print("\nOriginal columns:")
print("CSD:", csd.columns.tolist())
print("Roads:", roads.columns.tolist())
print("Canopy in CSDs:", canopy_csds.columns.tolist())
print("Canopy near roads (10 m):", canopy_roads_10m.columns.tolist())
print("Canopy near roads (20 m):", canopy_roads_20m.columns.tolist())
print("2021 Census of Population:", census.columns.tolist())

print("\nData types:")
print("CSD CSDUID:", csd['CSDUID'].dtype)
print("Roads CSDUID:", roads['CSDUID'].dtype)
print("Canopy CSDUID:", canopy_csds['CSDUID'].dtype)
print("Canopy near roads (10 m) CSDUID:", canopy_roads_10m['CSDUID'].dtype)
print("Canopy near roads (20 m) CSDUID:", canopy_roads_20m['CSDUID'].dtype)
print("Census CSDUID:", census['CSDUID'].dtype)

# Map provinces to regions
province_to_region = {
    10: "Atlantic Canada", 11: "Atlantic Canada", 12: "Atlantic Canada", 13: "Atlantic Canada",
    24: "Québec",
    35: "Ontario",
    46: "Prairies", 47: "Prairies", 48: "Prairies",
    59: "British Columbia"
}

# Create regions dictionary (region -> list of PRUIDs)
regions = defaultdict(list)
for pruid, region_name in province_to_region.items():
    regions[region_name].append(pruid)
regions = dict(regions)  # Convert back to regular dict

ecozone_groups = {
    'Arctic': {
        'Arctic Cordillera': '#bac3e0',
        'Northern Arctic': '#FAF9F6',
        'Southern Arctic': '#e6f1ff',
    },
    'Subarctic': {
        'Taiga Shield': '#ffe4c9',
        'Hudson Plain': '#98d4ff',
    },
    'Forested': {
        'MixedWood Plain': '#818c3c',
        'Boreal Shield': '#25591f',
        'Boreal Plain': '#487a67',
        'Taiga Cordillera': '#a7bc30',
        'Taiga Plain': '#b5d79f',
        'Boreal Cordillera': '#147453',
    },
    'Mountain': {
        'Montane Cordillera': '#969797',
    },
    'Prairie': {
        'Prairie': '#b08962',
    },
    'Maritime': {
        'Pacific Maritime': '#064273',
        'Atlantic Maritime': '#1da2d8',
    }
}

# ---------- Add suffixes to canopy tables ----------
# Add '_csd' to all canopy_csds columns except the join key CSDUID
canopy_csds_renamed = canopy_csds.rename(
    columns={c: f"{c}_csd" for c in canopy_csds.columns if c != "CSDUID"}
)

# Add '_10m_buffer' to all canopy_roads_10m columns except the join key CSDUID
canopy_roads_10m_renamed = canopy_roads_10m.rename(
    columns={c: f"{c}_10m_buffer" for c in canopy_roads_10m.columns if c != "CSDUID"}
)

# Add '_20m_buffer' to all canopy_roads_20m columns except the join key CSDUID
canopy_roads_20m_renamed = canopy_roads_20m.rename(
    columns={c: f"{c}_20m_buffer" for c in canopy_roads_20m.columns if c != "CSDUID"}
)

print("\nAfter suffixing canopy columns:")
print("Canopy in CSDs:", canopy_csds_renamed.columns.tolist())
print("Canopy near roads (10 m):", canopy_roads_10m_renamed.columns.tolist())
print("Canopy near roads (20 m):", canopy_roads_20m_renamed.columns.tolist())

# Drop redundant columns before merging
census_clean = census.drop(columns=['CSDNAME'])  # Avoid duplicate CSDNAME
csd_clean = csd.drop(columns=['area_km2'])  # Avoid redundant area measurement

# Merge datasets
merged = csd_clean.merge(roads, on='CSDUID', how='inner') \
    .merge(canopy_csds_renamed, on='CSDUID', how='inner') \
    .merge(canopy_roads_10m_renamed, on='CSDUID', how='inner') \
    .merge(canopy_roads_20m_renamed, on='CSDUID', how='inner') \
    .merge(census_clean, on='CSDUID', how='inner')

print("\nMerged data info:")
print("Rows:", len(merged))
print("Columns:", merged.columns)

#endregion


## --------------------------------------------------- RENAME COLUMNS AND DROP REDUNDANCIES
#region

# --- 1) CSDNAME_y no longer exists (census CSDNAME was dropped before merge) ---
# Just rename CSDNAME_x to CSDNAME (handled by rename_mapping)
# The CSDNAME from roads dataset becomes CSDNAME_y, verify it matches
if 'CSDNAME_y' in df.columns:
    mismatches_mask = df['CSDNAME_x'] != df['CSDNAME_y']

    if mismatches_mask.any():
        print("\nERROR: Strict mismatches found between CSDNAME_x and CSDNAME_y:")
        for idx in df.index[mismatches_mask]:
            x = df.at[idx, 'CSDNAME_x']
            y = df.at[idx, 'CSDNAME_y']
            print(f" Row {idx}: CSDNAME_x = {repr(x)} | CSDNAME_y = {repr(y)}")
    else:
        df = df.drop(columns=['CSDNAME_y'])
        print("\nCSDNAME_y dropped (all values matched exactly).")
else:
    print("\nNote: CSDNAME_y does not exist in merged dataframe.")

# --- 2) Filter rename_mapping to only include columns that exist ---
existing_columns = set(df.columns)
filtered_rename_mapping = {
    old: new for old, new in rename_mapping.items()
    if old in existing_columns
}

print("\nColumns to be renamed:")
for old, new in filtered_rename_mapping.items():
    print(f"  {old} -> {new}")

# Check for columns in df that won't be renamed
unrenamed_cols = existing_columns - set(filtered_rename_mapping.keys())
if unrenamed_cols:
    print("\nWarning: These columns will keep their original names:")
    for col in sorted(unrenamed_cols):
        print(f"  {col}")

# --- 3) Apply rename mapping ---
df = df.rename(columns=filtered_rename_mapping)

# --- 4) Drop redundant total_area_km2_csd column (redundant with census 'Land Area (sq km)') ---
if 'total_area_km2_csd' in df.columns:
    df = df.drop(columns=['total_area_km2_csd'])
    print("\ntotal_area_km2_csd dropped (redundant with census 'Land Area (sq km)').")

print("\nFinal columns after renaming:")
print(df.columns.tolist())

# Save result
df.to_csv('Datasets/Outputs/Canadian_urban_forest_census_independent_variables.csv', index=False)
print("\nMerged data saved to 'Datasets/Outputs/Canadian_urban_forest_census_independent_variables.csv'")

#endregion

