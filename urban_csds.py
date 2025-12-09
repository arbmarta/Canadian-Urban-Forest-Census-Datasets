import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.ops import unary_union
import contextily as ctx

# ======================================================
# Load + Prepare Data
# ======================================================
csd = gpd.read_file('Datasets/Inputs/census subdivisions 2021/census subdivisions 2021.shp')
eligible_csduid = pd.read_csv('Datasets/Inputs/eligible csduid.csv')

csd['CSDUID'] = pd.to_numeric(csd['CSDUID'], errors='coerce')
eligible_csduid['CSDUID'] = pd.to_numeric(eligible_csduid['CSDUID'], errors='coerce')

csd_merged = csd.merge(
    eligible_csduid,
    on='CSDUID',
    how='left',
    indicator=True,
    suffixes=('', '_eligible')
)

# Keyword and merge logic
keywords = ["lloydminster", "turner", "diamond"]
name_cond = csd_merged['CSDNAME'].str.contains("|".join(keywords), case=False, na=False)
merge_cond = csd_merged['_merge'] == 'both'

# Select all matches
csd_urban = csd_merged[merge_cond | name_cond].copy()

# Remove Petite-Rocher (store rows first)
rocher_cond = csd_urban['CSDNAME'].str.contains("rocher", case=False, na=False)
rocher_rows = csd_urban.loc[rocher_cond, ['CSDUID', 'CSDNAME']]
csd_urban = csd_urban[~rocher_cond].copy()

csd_urban.drop(columns=['_merge'], inplace=True)
csd_urban = csd_urban.drop_duplicates(subset='CSDUID')


# ======================================================
# Reporting Section (Improved Formatting)
# ======================================================

print("\n" + "="*70)
print(" Summary of Urban CSD Selection")
print("="*70)
print(f"Total rows in csd_urban: {len(csd_urban)}")

def pretty(df):
    return df.to_string(index=False) if len(df) else "None"

print("\n--- Name-matches only ---")
print(pretty(csd_urban.loc[name_cond & ~merge_cond, ['CSDUID','CSDNAME']].head()))

print("\n--- Merge-matches only ---")
print(pretty(csd_urban.loc[merge_cond & ~name_cond, ['CSDUID','CSDNAME']].head()))

print("\n--- Both match ---")
print(pretty(csd_urban.loc[merge_cond & name_cond, ['CSDUID','CSDNAME']].head()))

print("\n--- Removed due to containing 'rocher' ---")
print(pretty(rocher_rows))

print("\n" + "="*70 + "\n")


# ======================================================
# Merge Black Diamond + Turner Valley
# ======================================================
dt_cond = csd_urban['CSDNAME'].str.contains("black diamond", case=False, na=False) | \
          csd_urban['CSDNAME'].str.contains("turner valley", case=False, na=False)
dt_rows = csd_urban.loc[dt_cond, ['CSDUID', 'CSDNAME', 'geometry']]

print("Black Diamond + Turner Valley source rows:")
print(pretty(dt_rows[['CSDUID','CSDNAME']]))

if len(dt_rows):
    dt_geom_union = unary_union(dt_rows.geometry.values)
    dt_merged_gdf = gpd.GeoDataFrame(
        {'name': ['Diamond+Turner'], 'geometry': [dt_geom_union]},
        crs=csd_urban.crs
    )

    fig, ax = plt.subplots(figsize=(8, 8))
    dt_merged_gdf.to_crs(epsg=3857).plot(ax=ax, edgecolor='red', facecolor='none', linewidth=2)
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
    ax.set_title('Black Diamond + Turner Valley (merged)')
    ax.set_axis_off()
    plt.show()

print("\n" + "="*70 + "\n")


# ======================================================
# Merge Lloydminsters
# ======================================================
lloyd_cond = csd_urban['CSDNAME'].str.contains("lloydminster", case=False, na=False)
lloyd_rows = csd_urban.loc[lloyd_cond, ['CSDUID', 'CSDNAME', 'geometry']]

print("Lloydminster source rows:")
print(pretty(lloyd_rows[['CSDUID','CSDNAME']]))

if len(lloyd_rows):
    lloyd_geom_union = unary_union(lloyd_rows.geometry.values)
    lloyd_merged_gdf = gpd.GeoDataFrame(
        {'name': ['Lloydminster (merged)'], 'geometry': [lloyd_geom_union]},
        crs=csd_urban.crs
    )

    fig, ax = plt.subplots(figsize=(8, 8))
    lloyd_merged_gdf.to_crs(epsg=3857).plot(ax=ax, edgecolor='blue', facecolor='none', linewidth=2)
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
    ax.set_title('Lloydminster (merged)')
    ax.set_axis_off()
    plt.show()


# ======================================================
# Save Final Output (Urban CSDs + Centroids)
# ======================================================

# 1. Save polygons
urban_path = 'Datasets/Outputs/urban csds.gpkg'
csd_urban.to_file(urban_path, driver="GPKG")
print(f"\n\n\nSaved polygons to: {urban_path}")

# 2. Save centroids
centroids = csd_urban.copy()
centroids["geometry"] = centroids.geometry.centroid

centroid_path = 'Datasets/Outputs/urban csd centroids.gpkg'
centroids.to_file(centroid_path, driver="GPKG")
print(f"Saved centroids to: {centroid_path}")

print("\nAll processing complete.\n")
