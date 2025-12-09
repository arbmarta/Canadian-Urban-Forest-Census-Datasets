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
ecozone = gpd.read_file('Datasets/Inputs/ecozone_shp/ecozones.shp')

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

# Drop the merge indicator column (we still have merge_cond/name_cond variables for reporting)
csd_urban.drop(columns=['_merge'], inplace=True)
csd_urban = csd_urban.drop_duplicates(subset='CSDUID')

# ======================================================
# Reporting Section (Improved Formatting)
# ======================================================
print("\n" + "="*70)
print(" Summary of Urban CSD Selection")
print("="*70)
print(f"Total rows in csd_urban: {len(csd_urban)}")
print(f"Current CRS: {csd.crs}")

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
# ECOZONE FILTERING: keep only ecozones that intersect csd_urban
# ======================================================

# 1) Ensure ecozone has valid geometries and a CRS
ecozone = ecozone.dropna(subset=['geometry']).copy()
if ecozone.crs is None:
    raise ValueError("ecozone layer has no CRS — please set the CRS before proceeding.")

# 2) Reproject ecozones to the same CRS as csd_urban
ecozone = ecozone.to_crs(csd_urban.crs)

# 3) Build a single (possibly multipart) union of all urban geometries for efficient intersection tests
urban_union = unary_union(csd_urban.geometry.values)

# 4) Select ecozones that intersect the urban_union
#    Using .intersects on the vectorized GeoSeries; this leverages spatial index where available
ecozones_intersect = ecozone[ecozone.geometry.intersects(urban_union)].copy()

# 5) Fix "Boreal PLain" spelling mistake
if 'ZONE_NAME' in ecozones_intersect.columns:
    ecozones_intersect['ZONE_NAME'] = (
        ecozones_intersect['ZONE_NAME']
        .str.replace("Boreal PLain", "Boreal Plain", case=False, regex=False)
    )

# 6) Reporting
print("\n" + "="*70)
print(" Ecozone filtering summary")
print("="*70)
print(f"Total ecozones in input: {len(ecozone)}")
print(f"Ecozones intersecting urban CSDs: {len(ecozones_intersect)}")
print(f"Ecozones excluded (no intersection): {len(ecozone) - len(ecozones_intersect)}")
print(f"Name of ecozones: {ecozones_intersect['ZONE_NAME'].unique()}")

print("\n" + "="*70 + "\n")

# ======================================================
# Calculate Geodesic Area in km²
# ======================================================

# EPSG:3347 is Statistics Canada Lambert - already an equal-area projection for Canada
# Calculate area directly and convert from m² to km²
csd_urban['area_km2'] = csd_urban.geometry.area / 1_000_000

print("\n" + "="*70)
print(" Census Subdivision Areas (km²)")
print("="*70)
print(csd_urban[['CSDUID', 'CSDNAME', 'area_km2']].head(5).to_string(index=False))
print("\n" + "="*70 + "\n")

# ======================================================
# Determine Ecozone for Each Urban CSD
# ======================================================

# Perform spatial join to find which ecozone(s) each CSD intersects
csd_ecozone_join = gpd.sjoin(
    csd_urban[['CSDUID', 'CSDNAME', 'geometry']],
    ecozones_intersect[['ZONE_NAME', 'geometry']],
    how='left',
    predicate='intersects'
)

# Count how many ecozones each CSD intersects
ecozone_counts = csd_ecozone_join.groupby('CSDUID').size().rename('ecozone_count')

# Get the ecozone name(s) for each CSD
ecozone_names = csd_ecozone_join.groupby('CSDUID')['ZONE_NAME'].apply(
    lambda x: ' | '.join(x.dropna().unique()) if x.notna().any() else 'No ecozone'
).rename('ecozones')

# Merge back to csd_urban
csd_urban = csd_urban.merge(ecozone_counts, on='CSDUID', how='left')
csd_urban = csd_urban.merge(ecozone_names, on='CSDUID', how='left')
csd_urban['ecozone_count'] = csd_urban['ecozone_count'].fillna(0).astype(int)
csd_urban['ecozones'] = csd_urban['ecozones'].fillna('No ecozone')

# Add flag for multiple ecozones
csd_urban['multiple_ecozones'] = csd_urban['ecozone_count'] > 1

print("\n" + "="*70)
print(" Urban CSD Ecozone Assignment")
print("="*70)
print(csd_urban[['CSDUID', 'CSDNAME', 'area_km2', 'ecozones', 'multiple_ecozones']].head(10).to_string(index=False))

# Report CSDs in multiple ecozones
multi_ecozone_csds = csd_urban[csd_urban['multiple_ecozones']]
print(f"\n--- CSDs spanning multiple ecozones: {len(multi_ecozone_csds)} ---")
if len(multi_ecozone_csds) > 0:
    print(multi_ecozone_csds[['CSDUID', 'CSDNAME', 'ecozones']].to_string(index=False))
else:
    print("None")

print("\n" + "="*70 + "\n")

# ======================================================
# Map CSDs with Multiple Ecozones
# ======================================================

if len(multi_ecozone_csds) > 0:
    print(f"\nGenerating maps for {len(multi_ecozone_csds)} CSDs spanning multiple ecozones...\n")

    for idx, row in multi_ecozone_csds.iterrows():
        csd_geom = row.geometry
        csd_name = row['CSDNAME']
        csd_id = row['CSDUID']

        # Find which ecozones intersect this specific CSD
        intersecting_ecozones = ecozones_intersect[
            ecozones_intersect.geometry.intersects(csd_geom)
        ].copy()

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 10))

        # Plot the ecozones that intersect this CSD
        intersecting_ecozones.to_crs(epsg=3857).plot(
            ax=ax,
            alpha=0.4,
            edgecolor='black',
            linewidth=2,
            cmap='Set3',
            legend=False
        )

        # Plot the CSD boundary on top
        gpd.GeoSeries([csd_geom], crs=csd_urban.crs).to_crs(epsg=3857).plot(
            ax=ax,
            edgecolor='red',
            facecolor='none',
            linewidth=3
        )

        # Add ecozone labels
        for _, ecozone_row in intersecting_ecozones.iterrows():
            # Get centroid of the intersection for label placement
            intersection = csd_geom.intersection(ecozone_row.geometry)
            if not intersection.is_empty:
                centroid = intersection.centroid
                centroid_3857 = gpd.GeoSeries([centroid], crs=csd_urban.crs).to_crs(epsg=3857).iloc[0]

                ax.annotate(
                    ecozone_row['ZONE_NAME'],
                    xy=(centroid_3857.x, centroid_3857.y),
                    fontsize=12,
                    fontweight='bold',
                    ha='center',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7)
                )

        # Add basemap
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

        # Set title and formatting
        ax.set_title(f'{csd_name} (CSDUID: {csd_id})\nEcozones: {row["ecozones"]}',
                     fontsize=14, fontweight='bold', pad=20)
        ax.set_axis_off()

        plt.tight_layout()
        plt.show()

    print(f"\nCompleted mapping {len(multi_ecozone_csds)} CSDs with multiple ecozones.\n")
else:
    print("\nNo CSDs span multiple ecozones - no maps to generate.\n")

print("\n" + "=" * 70 + "\n")

# ======================================================
# Save Final Output (Urban CSDs, Centroids, Filtered Ecozones)
# ======================================================

# 1. Save polygons
urban_path = 'Datasets/Outputs/urban csds.gpkg'
csd_urban.to_file(urban_path, driver="GPKG")
print(f"Saved polygons to: {urban_path}")

# 2. Save centroids (straightforward method)
centroids = csd_urban.copy()
centroids["geometry"] = centroids.geometry.centroid
centroid_path = 'Datasets/Outputs/urban csd centroids.gpkg'
centroids.to_file(centroid_path, driver="GPKG")
print(f"Saved centroids to: {centroid_path}")

# 3. Save filtered ecozones (in same CRS as csd_urban)
ecozone_path = 'Datasets/Outputs/filtered ecozones.gpkg'
ecozones_intersect.to_file(ecozone_path, driver="GPKG")
print(f"Saved filtered ecozones to: {ecozone_path}")

print("\nAll processing complete.\n")
