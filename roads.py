import geopandas as gpd
from shapely.ops import unary_union
from tqdm import tqdm
import os
import pandas as pd

BUFFER_DISTANCE_M = 20  # either 10 or 20

print("Loading data...")
roads = gpd.read_file('Datasets/Inputs/roads/roads.shp')
csd = gpd.read_file('Datasets/Outputs/urban_csds/urban_csds.gpkg')

# Ensure CSDUID is int64
csd['CSDUID'] = csd['CSDUID'].astype('int64')

print(f"Original roads: {len(roads)}")
print(f"Roads CRS: {roads.crs}")
print(f"CSD CRS: {csd.crs}")

## ----------------------------------------- Reproject Roads to Match CSD CRS ------------------------------------------
# region

print("\nReprojecting roads to match CSD CRS...")
roads = roads.to_crs(csd.crs)
print(f"Roads reprojected to: {roads.crs}")

# endregion

## --------------------------------- Filter Roads that Intersect CSDs (spatial filter) ---------------------------------
# region

intersecting_roads_path = 'Datasets/Outputs/roads/intersecting_roads.gpkg'

if os.path.exists(intersecting_roads_path):
    print(f"\nLoading pre-filtered intersecting roads from: {intersecting_roads_path}")
    roads_intersecting = gpd.read_file(intersecting_roads_path)
    print(f"Loaded {len(roads_intersecting)} intersecting roads")
else:
    print("\nFiltering roads that intersect urban CSDs...")

    # Create a union of all CSD geometries for efficient filtering
    csd_union = unary_union(csd.geometry.values)

    # Use spatial index for efficient filtering with progress bar
    tqdm.pandas(desc="Checking intersections")
    roads['intersects'] = roads.geometry.progress_apply(lambda geom: geom.intersects(csd_union))
    roads_intersecting = roads[roads['intersects']].copy()
    roads_intersecting = roads_intersecting.drop(columns=['intersects'])

    print(f"Roads after filtering: {len(roads_intersecting)} (removed {len(roads) - len(roads_intersecting)})")

    # Save for future use
    print(f"Saving intersecting roads to: {intersecting_roads_path}")
    roads_intersecting.to_file(intersecting_roads_path, driver="GPKG")
    print("Saved successfully")

# endregion

## ------------------------------------------------ Clip Roads by CSDs -------------------------------------------------
# region

clipped_roads_path = 'Datasets/Outputs/roads/clipped_roads.gpkg'

if os.path.exists(clipped_roads_path):
    print(f"\nLoading pre-clipped roads from: {clipped_roads_path}")
    clipped_roads_gdf = gpd.read_file(clipped_roads_path)
    print(f"Loaded {len(clipped_roads_gdf)} clipped road segments")
else:
    print("\nClipping roads to CSD boundaries...")

    # Perform spatial join to identify which CSD each road intersects
    roads_csd_join = gpd.sjoin(roads_intersecting, csd[['CSDUID', 'geometry']], how='inner', predicate='intersects')

    # Clip each road segment to its intersecting CSD(s)
    clipped_roads = []
    for idx, road_row in tqdm(roads_csd_join.iterrows(), total=len(roads_csd_join), desc="Clipping roads"):
        road_geom = road_row.geometry
        csduid = road_row['CSDUID']

        # Get the CSD polygon
        csd_geom = csd[csd['CSDUID'] == csduid].iloc[0].geometry

        # Clip the road to the CSD boundary
        clipped_geom = road_geom.intersection(csd_geom)

        if not clipped_geom.is_empty:
            clipped_roads.append({
                'CSDUID': csduid,
                'geometry': clipped_geom
            })

    clipped_roads_gdf = gpd.GeoDataFrame(clipped_roads, crs=csd.crs)
    print(f"Clipped road segments: {len(clipped_roads_gdf)}")

    # Save for future use
    print(f"Saving clipped roads to: {clipped_roads_path}")
    clipped_roads_gdf.to_file(clipped_roads_path, driver="GPKG")
    print("Saved successfully")

# endregion

## ----------------------------------------------- Calculate Road Lengths ----------------------------------------------
# region

print("\nCalculating road lengths by CSDUID...")

# Calculate length in meters for each road segment
clipped_roads_gdf['road_length_m'] = clipped_roads_gdf.geometry.length

# Sum lengths by CSDUID and convert to kilometers
road_lengths = clipped_roads_gdf.groupby('CSDUID')['road_length_m'].sum().reset_index()
road_lengths['road_length_km'] = road_lengths['road_length_m'] / 1000
road_lengths = road_lengths[['CSDUID', 'road_length_km']]

# Merge with CSD names for reference
csd_names = csd[['CSDUID', 'CSDNAME']].copy()
road_lengths = road_lengths.merge(csd_names, on='CSDUID', how='left')

# Reorder columns
road_lengths = road_lengths[['CSDUID', 'CSDNAME', 'road_length_km']]

# Save to CSV
road_lengths_csv_path = 'Datasets/Outputs/roads/road_lengths_by_csd.csv'
road_lengths.to_csv(road_lengths_csv_path, index=False)
print(f"Saved road lengths to: {road_lengths_csv_path}")

# Print summary statistics
print(f"\nRoad Length Summary:")
print(f"Total CSDs with roads: {len(road_lengths)}")
print(f"Mean road length: {road_lengths['road_length_km'].mean():.2f} km")
print(f"Median road length: {road_lengths['road_length_km'].median():.2f} km")
print(f"Min road length: {road_lengths['road_length_km'].min():.2f} km")
print(f"Max road length: {road_lengths['road_length_km'].max():.2f} km")

# Check for CSDs with less than 100 km of roads
low_road_csds = road_lengths[road_lengths['road_length_km'] < 100]
if len(low_road_csds) > 0:
    print(f"\n*** WARNING: {len(low_road_csds)} CSDs have less than 100 km of roads ***")
    print(low_road_csds.to_string(index=False))
else:
    print("\nAll CSDs have at least 100 km of roads.")

# endregion

# --------------------------------------------------- Buffer Roads ----------------------------------------------------
# region

# Create buffer-specific output directory and file paths
buffer_dir = f'Datasets/Outputs/roads/road_buffers_{BUFFER_DISTANCE_M}m'
os.makedirs(buffer_dir, exist_ok=True)

buffered_roads_gpkg = os.path.join(buffer_dir, f'buffered_roads_{BUFFER_DISTANCE_M}m.gpkg')

if os.path.exists(buffered_roads_gpkg):
    print(f"\nLoading pre-buffered roads from: {buffered_roads_gpkg}")
    road_buffers_gdf = gpd.read_file(buffered_roads_gpkg)
    print(f"Loaded {len(road_buffers_gdf)} buffered road segments")
else:
    print(f"\nBuffering roads by {BUFFER_DISTANCE_M} meters...")
    buffered_roads_gdf = clipped_roads_gdf.copy()

    # use the variable here
    buffered_roads_gdf['geometry'] = buffered_roads_gdf.geometry.buffer(BUFFER_DISTANCE_M)

    print("\nClipping buffers to CSD boundaries...")

    final_buffers = []
    for idx, buffer_row in tqdm(buffered_roads_gdf.iterrows(), total=len(buffered_roads_gdf), desc="Clipping buffers"):
        buffer_geom = buffer_row.geometry
        csduid = buffer_row['CSDUID']

        # Safe lookup of CSD polygon (ensure matching types)
        # If your csd['CSDUID'] is not int, coerce both sides consistently earlier
        csd_match = csd.loc[csd['CSDUID'] == csduid, 'geometry']
        if csd_match.empty:
            # fallback: try numeric comparison if types mismatch
            try:
                csd_match = csd.loc[pd.to_numeric(csd['CSDUID'], errors='coerce') == int(csduid), 'geometry']
            except Exception:
                csd_match = csd_match  # stay empty
        if csd_match.empty:
            # warn and skip if no CSD polygon found
            print(f"Warning: no CSD polygon found for CSDUID {csduid}; skipping buffer idx {idx}")
            continue

        csd_geom = csd_match.iloc[0]

        # Clip the buffer to the CSD boundary
        clipped_buffer = buffer_geom.intersection(csd_geom)

        if not clipped_buffer.is_empty:
            final_buffers.append({
                'CSDUID': csduid,
                'geometry': clipped_buffer
            })

    road_buffers_gdf = gpd.GeoDataFrame(final_buffers, crs=csd.crs)
    print(f"Final road buffers: {len(road_buffers_gdf)}")

    # Save for future use (explicit file)
    print(f"Saving buffered roads to: {buffered_roads_gpkg}")
    road_buffers_gdf.to_file(buffered_roads_gpkg, driver="GPKG")
    print("Saved successfully")

# endregion

# ------------------------------------------------- Dissolve Buffers --------------------------------------------------
# region

print("\nDissolving overlapping buffers within each CSD...")
road_buffers_dissolved = road_buffers_gdf.dissolve(by='CSDUID').reset_index()
print(f"Dissolved road buffers: {len(road_buffers_dissolved)}")
print(f"Columns in dissolved data: {road_buffers_dissolved.columns.tolist()}")

# Verify CSDUID is present
print("\nSample of dissolved buffers with CSDUID:")
print(road_buffers_dissolved[['CSDUID']].head())

# endregion

# ---------------------------------------------------- Save Output ----------------------------------------------------
# region

# Rename columns for shapefile compatibility
road_buffers_shp = road_buffers_dissolved.copy()

# Save as GeoPackage (file inside buffer_dir)
output_gpkg_path = os.path.join(buffer_dir, f'road_buffers_{BUFFER_DISTANCE_M}m.gpkg')
road_buffers_dissolved.to_file(output_gpkg_path, driver="GPKG")
print(f"\nSaved road buffers (geopackage) to: {output_gpkg_path}")

# Save as Shapefile (shapefile will create multiple files in the same folder)
output_shp_path = os.path.join(buffer_dir, f'road_buffers_{BUFFER_DISTANCE_M}m.shp')
road_buffers_shp.to_file(output_shp_path, driver="ESRI Shapefile")
print(f"Saved road buffers (shapefile) to: {output_shp_path}")

print("\nProcessing complete.\n")

# endregion