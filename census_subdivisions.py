import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.ops import unary_union
import contextily as ctx

## ------------------------------------------------ Load & Prepare Data ------------------------------------------------
#region

csd = gpd.read_file('Datasets/Inputs/census_subdivisions_2021/census_subdivisions_2021.shp')
eligible_csduid = pd.read_csv('Datasets/Inputs/eligible_csduid.csv')
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

# Check for duplicates before removing
duplicate_count = csd_urban['CSDUID'].duplicated().sum()
if duplicate_count > 0:
    print(f"\n*** WARNING: Found {duplicate_count} duplicate CSDUIDs ***")
    duplicate_csds = csd_urban[csd_urban['CSDUID'].duplicated(keep=False)][['CSDUID', 'CSDNAME']].sort_values('CSDUID')
    print(duplicate_csds.to_string(index=False))
else:
    print("\nNo duplicate CSDUIDs found.")

# Drop the duplicates
csd_urban = csd_urban.drop_duplicates(subset='CSDUID')

#endregion

## ------------------------------------------------- Reporting Section -------------------------------------------------
#region

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

#endregion

## --------------------------------- Merge Black Diamond, Turner Valley & Lloydminster ---------------------------------
# region

print("\n" + "=" * 70)
print(" Merging Multi-Part CSDs")
print("=" * 70)

# ===== BLACK DIAMOND + TURNER VALLEY =====
dt_cond = csd_urban['CSDNAME'].str.contains("black diamond", case=False, na=False) | \
          csd_urban['CSDNAME'].str.contains("turner valley", case=False, na=False)
dt_rows = csd_urban.loc[dt_cond, ['CSDUID', 'CSDNAME', 'geometry']]

print("\nBlack Diamond + Turner Valley source rows:")
print(pretty(dt_rows[['CSDUID', 'CSDNAME']]))

if len(dt_rows) > 0:
    # Get Turner Valley CSDUID (4806009)
    turner_valley_csduid = \
    dt_rows[dt_rows['CSDNAME'].str.contains("turner valley", case=False, na=False)]['CSDUID'].iloc[0]

    # Create merged geometry
    dt_geom_union = unary_union(dt_rows.geometry.values)

    # Visualize the merge
    dt_merged_gdf = gpd.GeoDataFrame(
        {'name': ['Diamond Valley'], 'geometry': [dt_geom_union]},
        crs=csd_urban.crs
    )

    fig, ax = plt.subplots(figsize=(8, 8))
    dt_merged_gdf.to_crs(epsg=3857).plot(ax=ax, edgecolor='red', facecolor='none', linewidth=2)
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
    ax.set_title('Diamond Valley (Black Diamond + Turner Valley merged)')
    ax.set_axis_off()
    plt.show()

    # Actually merge in the dataset
    merged_dt = csd_urban[dt_cond].iloc[0].copy()
    merged_dt['geometry'] = dt_geom_union
    merged_dt['CSDNAME'] = 'Diamond Valley'
    merged_dt['CSDUID'] = turner_valley_csduid

    # Remove original rows and add merged row
    csd_urban = csd_urban[~dt_cond].copy()
    csd_urban = pd.concat([csd_urban, gpd.GeoDataFrame([merged_dt], crs=csd_urban.crs)], ignore_index=True)

    print(f"✓ Merged into Diamond Valley (CSDUID: {turner_valley_csduid})")

print("\n" + "-" * 70)

# ===== LLOYDMINSTER =====
lloyd_cond = csd_urban['CSDNAME'].str.contains("lloydminster", case=False, na=False)
lloyd_rows = csd_urban.loc[lloyd_cond, ['CSDUID', 'CSDNAME', 'geometry']]

print("\nLloydminster source rows:")
print(pretty(lloyd_rows[['CSDUID', 'CSDNAME']]))

if len(lloyd_rows) > 0:
    # Get Alberta Lloydminster CSDUID (4717029)
    alberta_lloyd_csduid = lloyd_rows[lloyd_rows['CSDUID'].astype(str).str.startswith('47')]['CSDUID'].iloc[0]

    # Create merged geometry
    lloyd_geom_union = unary_union(lloyd_rows.geometry.values)

    # Visualize the merge
    lloyd_merged_gdf = gpd.GeoDataFrame(
        {'name': ['Lloydminster'], 'geometry': [lloyd_geom_union]},
        crs=csd_urban.crs
    )

    fig, ax = plt.subplots(figsize=(8, 8))
    lloyd_merged_gdf.to_crs(epsg=3857).plot(ax=ax, edgecolor='blue', facecolor='none', linewidth=2)
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
    ax.set_title('Lloydminster (AB + SK merged)')
    ax.set_axis_off()
    plt.show()

    # Actually merge in the dataset
    merged_lloyd = csd_urban[lloyd_cond].iloc[0].copy()
    merged_lloyd['geometry'] = lloyd_geom_union
    merged_lloyd['CSDNAME'] = 'Lloydminster'
    merged_lloyd['CSDUID'] = alberta_lloyd_csduid

    # Remove original rows and add merged row
    csd_urban = csd_urban[~lloyd_cond].copy()
    csd_urban = pd.concat([csd_urban, gpd.GeoDataFrame([merged_lloyd], crs=csd_urban.crs)], ignore_index=True)

    print(f"✓ Merged into Lloydminster (CSDUID: {alberta_lloyd_csduid})")

print(f"\nTotal CSDs after merging: {len(csd_urban)}")
print("\n" + "=" * 70 + "\n")

# endregion

## -------------------------------------------- Calculate Land Area of CSDs --------------------------------------------
#region

# EPSG:3347 is Statistics Canada Lambert - already an equal-area projection for Canada
# Calculate area directly and convert from m² to km²
csd_urban['area_km2'] = csd_urban.geometry.area / 1_000_000

print("\n" + "="*70)
print(" Census Subdivision Areas (km²)")
print("="*70)
print(csd_urban[['CSDUID', 'CSDNAME', 'area_km2']].head(5).to_string(index=False))
print("\n" + "="*70 + "\n")

#endregion

## -------------------------------------------------- Assign Ecozones --------------------------------------------------
# region

# 1) Ensure ecozone has valid geometries and a CRS
ecozone = ecozone.dropna(subset=['geometry']).copy()
if ecozone.crs is None:
    raise ValueError("ecozone layer has no CRS — please set the CRS before proceeding.")

# 2) Reproject ecozones to the same CRS as csd_urban
ecozone = ecozone.to_crs(csd_urban.crs)

# 3) Fix "Boreal PLain" spelling mistake
if 'ZONE_NAME' in ecozone.columns:
    ecozone['ZONE_NAME'] = (
        ecozone['ZONE_NAME']
        .str.replace("Boreal PLain", "Boreal Plain", case=False, regex=False)
    )

# Calculate area of intersection for each CSD-ecozone pair
ecozone_assignments = []

for csd_id in csd_urban['CSDUID'].unique():
    csd_row = csd_urban[csd_urban['CSDUID'] == csd_id].iloc[0]
    csd_geom = csd_row.geometry
    csd_area = csd_row['area_km2']

    # Find intersecting ecozones
    intersecting = ecozone[ecozone.geometry.intersects(csd_geom)]

    if len(intersecting) == 0:
        ecozone_assignments.append({
            'CSDUID': csd_id,
            'assigned_ecozone': 'No ecozone',
            'ecozone_count': 0,
            'all_ecozones': 'No ecozone',
            'dominant_ecozone': 'No',
            'coverage_pct': 0,
            'assignment_error': False
        })
    elif len(intersecting) == 1:
        ecozone_assignments.append({
            'CSDUID': csd_id,
            'assigned_ecozone': intersecting.iloc[0]['ZONE_NAME'],
            'ecozone_count': 1,
            'all_ecozones': intersecting.iloc[0]['ZONE_NAME'],
            'dominant_ecozone': 'Yes',
            'coverage_pct': 100.0,
            'assignment_error': False
        })
    else:
        # Multiple ecozones - calculate coverage percentages
        coverage_data = []
        for _, ecozone_row in intersecting.iterrows():
            intersection = csd_geom.intersection(ecozone_row.geometry)
            intersection_area_km2 = gpd.GeoSeries([intersection], crs=csd_urban.crs).area.iloc[0] / 1_000_000
            coverage_pct = (intersection_area_km2 / csd_area) * 100
            coverage_data.append({
                'zone_name': ecozone_row['ZONE_NAME'],
                'coverage_pct': coverage_pct
            })

        # Sort by coverage
        coverage_data.sort(key=lambda x: x['coverage_pct'], reverse=True)
        max_coverage = coverage_data[0]['coverage_pct']
        all_zones = ' | '.join([z['zone_name'] for z in coverage_data])

        # Check if dominant ecozone covers at least 50.01%
        if max_coverage >= 50.01:
            ecozone_assignments.append({
                'CSDUID': csd_id,
                'assigned_ecozone': coverage_data[0]['zone_name'],
                'ecozone_count': len(intersecting),
                'all_ecozones': all_zones,
                'dominant_ecozone': 'Yes',
                'coverage_pct': round(max_coverage, 2),
                'assignment_error': False
            })
        else:
            ecozone_assignments.append({
                'CSDUID': csd_id,
                'assigned_ecozone': 'ERROR: No dominant ecozone',
                'ecozone_count': len(intersecting),
                'all_ecozones': all_zones,
                'dominant_ecozone': 'No',
                'coverage_pct': round(max_coverage, 2),
                'assignment_error': True
            })

# Convert to DataFrame and merge
ecozone_df = pd.DataFrame(ecozone_assignments)
csd_urban = csd_urban.merge(ecozone_df, on='CSDUID', how='left')

print("\n" + "=" * 70)
print(" Urban CSD Ecozone Assignment")
print("=" * 70)
print(csd_urban[['CSDUID', 'CSDNAME', 'area_km2', 'assigned_ecozone', 'dominant_ecozone', 'coverage_pct']].head(
    10).to_string(index=False))

# Report CSDs in multiple ecozones
multi_ecozone_csds = csd_urban[csd_urban['ecozone_count'] > 1]
print(f"\n--- CSDs spanning multiple ecozones: {len(multi_ecozone_csds)} ---")
if len(multi_ecozone_csds) > 0:
    print(multi_ecozone_csds[
              ['CSDUID', 'CSDNAME', 'all_ecozones', 'assigned_ecozone', 'dominant_ecozone', 'coverage_pct']].to_string(
        index=False))
else:
    print("None")

# Report assignment errors
error_csds = csd_urban[csd_urban['assignment_error']]
print(f"\n--- ERROR: CSDs with no dominant ecozone (< 50% coverage): {len(error_csds)} ---")
if len(error_csds) > 0:
    print(error_csds[['CSDUID', 'CSDNAME', 'all_ecozones', 'coverage_pct']].to_string(index=False))
    print("\n*** ATTENTION: These CSDs could not be assigned to a single ecozone ***")
else:
    print("None - all multi-ecozone CSDs have a dominant zone")

print("\n" + "=" * 70 + "\n")

# Map CSDs with multiple ecozones
if len(multi_ecozone_csds) > 0:
    print(f"\nGenerating maps for {len(multi_ecozone_csds)} CSDs spanning multiple ecozones...\n")

    for idx, row in multi_ecozone_csds.iterrows():
        csd_geom = row.geometry
        csd_name = row['CSDNAME']
        csd_id = row['CSDUID']

        # Find which ecozones intersect this specific CSD
        intersecting_ecozones = ecozone[ecozone.geometry.intersects(csd_geom)].copy()

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
        csd_3857 = gpd.GeoSeries([csd_geom], crs=csd_urban.crs).to_crs(epsg=3857)
        csd_3857.plot(
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

        # Zoom to CSD extent with buffer
        bounds = csd_3857.total_bounds  # [minx, miny, maxx, maxy]
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        buffer = max(width, height) * 0.1  # 10% buffer

        ax.set_xlim(bounds[0] - buffer, bounds[2] + buffer)
        ax.set_ylim(bounds[1] - buffer, bounds[3] + buffer)

        # Add basemap
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

        # Set title and formatting
        ax.set_title(f'{csd_name} (CSDUID: {csd_id})\nEcozones: {row["all_ecozones"]}',
                     fontsize=14, fontweight='bold', pad=20)
        ax.set_axis_off()

        plt.tight_layout()
        plt.show()

    print(f"\nCompleted mapping {len(multi_ecozone_csds)} CSDs with multiple ecozones.\n")
else:
    print("\nNo CSDs span multiple ecozones - no maps to generate.\n")

print("\n" + "=" * 70 + "\n")

# endregion

## ------------------------------------------------ Save Final Outputs -------------------------------------------------
#region

# Create a copy with shortened column names for shapefile compatibility
csd_urban_shp = csd_urban.copy()
csd_urban_shp = csd_urban_shp.rename(columns={
    'assigned_ecozone': 'assign_eco',
    'ecozone_count': 'eco_count',
    'all_ecozones': 'all_eco',
    'dominant_ecozone': 'dom_eco',
    'coverage_pct': 'cover_pct',
    'assignment_error': 'assign_err'
})

# 1. Save polygons (both formats)
urban_shp_path = 'Datasets/Outputs/urban_csds/urban_csds.shp'
csd_urban_shp.to_file(urban_shp_path, driver="ESRI Shapefile")
print(f"Saved polygons (shapefile) to: {urban_shp_path}")

urban_gpkg_path = 'Datasets/Outputs/urban_csds/urban_csds.gpkg'
csd_urban.to_file(urban_gpkg_path, driver="GPKG")
print(f"Saved polygons (geopackage) to: {urban_gpkg_path}")

# 2. Save centroids (both formats)
centroids_shp = csd_urban_shp.copy()
centroids_shp["geometry"] = centroids_shp.geometry.centroid
centroid_shp_path = 'Datasets/Outputs/urban_csd_centroids/urban_csd_centroids.shp'
centroids_shp.to_file(centroid_shp_path, driver="ESRI Shapefile")
print(f"Saved centroids (shapefile) to: {centroid_shp_path}")

centroids_gpkg = csd_urban.copy()
centroids_gpkg["geometry"] = centroids_gpkg.geometry.centroid
centroid_gpkg_path = 'Datasets/Outputs/urban_csd_centroids/urban_csd_centroids.gpkg'
centroids_gpkg.to_file(centroid_gpkg_path, driver="GPKG")
print(f"Saved centroids (geopackage) to: {centroid_gpkg_path}")

# 3. Save attribute table as CSV (with full column names)
csv_data = csd_urban[['CSDUID', 'CSDNAME', 'area_km2', 'assigned_ecozone', 'dominant_ecozone', 'coverage_pct']].copy()
csv_path = 'Datasets/Outputs/urban_csds/urban_csds_attributes.csv'
csv_data.to_csv(csv_path, index=False)
print(f"Saved attribute table to: {csv_path}")

print("\nAll processing complete.\n")

#endregion