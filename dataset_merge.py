import pandas as pd
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
province_to_subregion = {
    10: "Atlantic Canada", 11: "Atlantic Canada", 12: "Atlantic Canada", 13: "Atlantic Canada",
    24: "Québec",
    35: "Ontario",
    46: "Manitoba", 47: "Saskatchewan", 48: "Alberta",
    59: "British Columbia"
}

# Create regions dictionary (region -> list of PRUIDs)
regions = defaultdict(list)
for pruid, region_name in province_to_region.items():
    regions[region_name].append(pruid)
regions = dict(regions)  # Convert back to regular dict

# Create subregions dictionary (subregions -> list of PRUIDs)
subregions = defaultdict(list)
for pruid, subregion_name in province_to_subregion.items():
    subregions[subregion_name].append(pruid)
subregions = dict(subregions)  # Convert back to regular dict

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
df = csd_clean.merge(roads, on='CSDUID', how='inner') \
    .merge(canopy_csds_renamed, on='CSDUID', how='inner') \
    .merge(canopy_roads_10m_renamed, on='CSDUID', how='inner') \
    .merge(canopy_roads_20m_renamed, on='CSDUID', how='inner') \
    .merge(census_clean, on='CSDUID', how='inner')

print("\nMerged data info:")
print("Rows:", len(df))
print("Columns:", df.columns)

#endregion

## --------------------------------------------------- RENAME COLUMNS AND DROP REDUNDANCIES
#region

# CSDNAME_y no longer exists (census CSDNAME was dropped before merge) ---
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

# Rename CSDNAME_x to CSDNAME
df = df.rename(columns={'CSDNAME_x': 'CSDNAME'})
print("CSDNAME_x renamed to CSDNAME.")

# Drop redundant total_area_km2_csd column (redundant with census 'Land Area (sq km)')
if 'total_area_km2_csd' in df.columns:
    df = df.drop(columns=['total_area_km2_csd'])
    print("\ntotal_area_km2_csd dropped (redundant with census 'Land Area (sq km)').")

# Extract PRUID from CSDUID (first 2 digits)
df['PRUID'] = df['CSDUID'].astype(str).str[:2].astype(int)

# Add Region and Subregion columns using the dictionaries
df['Region'] = df['PRUID'].map(province_to_region)
df['Subregion'] = df['PRUID'].map(province_to_subregion)

print("\nRegion and Subregion columns added based on PRUID.")
print(f"Regions: {df['Region'].unique().tolist()}")
print(f"Subregions: {df['Subregion'].unique().tolist()}")

print("\nFinal columns after renaming:")
print(df.columns.tolist())

# Save result
df.to_csv('Datasets/Outputs/Canadian_urban_forest_census_independent_variables.csv', index=False)
print("\nMerged data saved to 'Datasets/Outputs/Canadian_urban_forest_census_independent_variables.csv'")

#endregion

## --------------------------------------------------- FINAL ROW COUNT CHECK ---------------------------------------------------

print("\n" + "=" * 70)
print("FINAL DATA CHECK")
print("=" * 70)

final_row_count = len(df)
expected_row_count = 343

if final_row_count == expected_row_count:
    print(f"\n✅ SUCCESS: Final dataset has {final_row_count} rows (expected {expected_row_count})")
else:
    print(f"\n⚠️  WARNING: Final dataset has {final_row_count} rows (expected {expected_row_count})")
    print(f"   Difference: {final_row_count - expected_row_count} rows")
    if final_row_count < expected_row_count:
        print(f"   {expected_row_count - final_row_count} CSDs are missing from the final dataset!")

print("\n" + "=" * 70)