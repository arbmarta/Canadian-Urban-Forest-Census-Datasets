from functools import reduce
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.ops import unary_union
import contextily as ctx
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

## ------------------------------------------------ LOAD AND CLEAN DATA ------------------------------------------------
#region

# load datasets
population = pd.read_csv('Datasets/Inputs/2021_census_of_population/population.csv')
labour = pd.read_csv('Datasets/Inputs/2021_census_of_population/labour.csv')
indigenous_identity = pd.read_csv('Datasets/Inputs/2021_census_of_population/indigenous_identity.csv')
visible_minorities = pd.read_csv('Datasets/Inputs/2021_census_of_population/visible_minorities.csv')

amalgamated_csds = pd.read_csv('Datasets/Inputs/2021_census_of_population/amalgamated_cities.csv')

# Drop CSDNAME from all datasets except population
for dataset in [labour, indigenous_identity, visible_minorities]:
    dataset.drop(columns=['CSDNAME'], errors='ignore', inplace=True)

# Merge all dataframes
df = reduce(lambda left, right: left.merge(right, on='CSDUID', how='outer'),
            [population, labour, indigenous_identity, visible_minorities])

print("Columns in merged dataset:")
for col in df.columns:
    print(f"  - {col}")

#endregion

## --------------------------------------- REMOVE NON-URBAN AND INDIGENOUS CSDs ----------------------------------------
#region

print(f"\nTotal number of CSDs in dataset: {len(df)}")

# Filter for urban CSDs
urban_df = df[(df['Population, 2021'] >= 1000) & (df['Population Density (sq km)'] >= 400)].copy()

# Combined exclusion pattern (exclude CSDs with digits in name, PETIT-ROCHER, or WENDAKE)
exclusion_pattern = r'\d|PETIT-ROCHER|WENDAKE'
urban_df = urban_df[~urban_df['CSDNAME'].str.contains(exclusion_pattern, case=False, na=False)]

print(f"Number of urban and non-Indigenous CSDs: {len(urban_df)}")

#endregion

## --------------------------------------------- HANDLE AMALGAMATED CITIES ---------------------------------------------
#region

# CSDUIDs to remove from urban_df before concatenation
to_remove_csduids = {'4810039', '4717029', '4806011', '4806009'}

# ---------- NORMALIZE KEY COLUMN ----------
urban_df['CSDUID'] = urban_df['CSDUID'].astype(str).str.strip()  # ✅ ADDED
amalgamated_csds['CSDUID'] = amalgamated_csds['CSDUID'].astype(str).str.strip()

# ---------- HARMONIZE DTYPES ----------
# Convert integer columns (counts)
int_cols = ['Population, 2021', 'Total private dwellings',
            'Private dwellings occupied by usual residents']
for col in int_cols:
    if col in amalgamated_csds.columns:
        amalgamated_csds[col] = amalgamated_csds[col].astype('int64')

# Convert float columns (percentages, areas, densities)
float_cols = [
    'Population percentage change, 2016 to 2021 (%)',
    'Land Area (sq km)',
    'Population Density (sq km)',
    'Proportion of the Labour Force that is Men+ (%)',
    'Proportion of the Employed Population that is Men+ (%)',
    'Indigenous identity (%)',
    'Single Indigenous responses (%)',
    'First Nations (%)',
    'Métis (%)',
    'Inuit (%)',
    'Multiple Indigenous responses (%)',
    'Indigenous responses nie (%)',
    'Non-Indigenous identity (%)',
    'visible minority population  (%)'
]
for col in float_cols:
    if col in amalgamated_csds.columns:
        amalgamated_csds[col] = amalgamated_csds[col].astype('float64')

print("\nAMALGAMATION PROCESS:")
print(f" - CSDUIDs to remove: {sorted(to_remove_csduids)}")
print(f" - Rows in amalgamated CSV: {len(amalgamated_csds)}")
print(f" - Amalgamated CSDUIDs: {sorted(amalgamated_csds['CSDUID'].unique())}")

# ---------- Remove specified CSDs and add amalgamated ones ----------
urban_df = urban_df[~urban_df['CSDUID'].isin(to_remove_csduids)].copy()
print(f" - Rows after removing specified CSDUIDs: {len(urban_df)}")

# Ensure column order matches
amalgamated_csds = amalgamated_csds[df.columns]

# Concatenate
urban_df = pd.concat([urban_df, amalgamated_csds], axis=0, ignore_index=True, sort=False)

# Validate no duplicates
dup_counts = urban_df['CSDUID'].value_counts()  # ✅ FIXED
duplicates = dup_counts[dup_counts > 1]
if not duplicates.empty:
    print("\nERROR: Duplicate CSDUIDs detected!")
    print(duplicates)
    raise RuntimeError("Aborting: duplicates found after concatenation.")

print(f" - Total rows after amalgamation: {len(urban_df)}")
print("SUCCESS: Amalgamation complete, no duplicates detected.\n")

#endregion

## ----------------------------------------------- IDENTIFY THE ECOZONES -----------------------------------------------
#region

# Import spatial data
csd_shp = gpd.read_file('Datasets/Inputs/census_subdivisions_2021/census_subdivisions_2021.shp')
ecozone = gpd.read_file('Datasets/Inputs/ecozone_shp/ecozones.shp')
provinces_gdf = gpd.read_file('Datasets/Inputs/provinces/provinces_simplified_1km.gpkg')

# Merge polygons of amalgamated cities
lloydminster = ['4810039', '4717029']
black_diamond = ['4806011', '4806009']

# Ensure CSDUID is string
csd_shp['CSDUID'] = csd_shp['CSDUID'].astype(str)

# Merge Lloydminster
lloyd_rows = csd_shp[csd_shp['CSDUID'].isin(lloydminster)]
lloyd_merged = lloyd_rows.iloc[0].copy()
lloyd_merged['geometry'] = unary_union(lloyd_rows.geometry)
lloyd_merged['CSDNAME'] = 'Lloydminster'
lloyd_merged['CSDUID'] = '4810039'
csd_shp = csd_shp[~csd_shp['CSDUID'].isin(lloydminster)]
csd_shp = gpd.GeoDataFrame(pd.concat([csd_shp, gpd.GeoDataFrame([lloyd_merged], crs=csd_shp.crs)],
                                     ignore_index=True), crs=csd_shp.crs)

# Merge Black Diamond + Turner Valley -> Diamond Valley
bd_rows = csd_shp[csd_shp['CSDUID'].isin(black_diamond)]
bd_merged = bd_rows.iloc[0].copy()
bd_merged['geometry'] = unary_union(bd_rows.geometry)
bd_merged['CSDNAME'] = 'Diamond Valley'
bd_merged['CSDUID'] = '4806011'
csd_shp = csd_shp[~csd_shp['CSDUID'].isin(black_diamond)]
csd_shp = pd.concat([csd_shp, gpd.GeoDataFrame([bd_merged], crs=csd_shp.crs)], ignore_index=True)

print(f"\nTotal CSDs in shapefile after merging: {len(csd_shp)}")

# Filter csd_shp to only keep rows that are in urban_csds
urban_csd_shp = csd_shp[csd_shp['CSDUID'].isin(urban_df['CSDUID'])].copy()
print(f"Rows in urban_csd_shp after removing non-urban and Indigenous CSDs: {len(urban_csd_shp)}")

# Add province names after filtering to urban_csd_shp
provinces_territories = {
    10: "Newfoundland and Labrador",
    11: "Prince Edward Island",
    12: "Nova Scotia",
    13: "New Brunswick",
    24: "Quebec",
    35: "Ontario",
    46: "Manitoba",
    47: "Saskatchewan",
    48: "Alberta",
    59: "British Columbia",
    60: "Yukon",
    61: "Northwest Territories",
    62: "Nunavut"
}

urban_csd_shp['PRUID'] = urban_csd_shp['PRUID'].astype(int)
urban_csd_shp['province'] = urban_csd_shp['PRUID'].map(provinces_territories)

# Ensure ecozone has valid geometries and a CRS
ecozone = ecozone.dropna(subset=['geometry']).copy()
if ecozone.crs is None:
    raise ValueError("ecozone layer has no CRS — please set the CRS before proceeding.")

# Reproject ecozone to the same CRS as csd_urban
ecozone = ecozone.to_crs(urban_csd_shp.crs)

# Fix "Boreal PLain" spelling mistake
ecozone['ZONE_NAME'] = ecozone['ZONE_NAME'].replace('Boreal PLain', 'Boreal Plain')

# Calculate area before ecozone assignment
urban_csd_shp['area_km2'] = urban_csd_shp.geometry.area / 1_000_000

# Calculate area of intersection for each CSD-ecozone pair
ecozone_assignments = []

for idx, csd_row in urban_csd_shp.iterrows():
    csd_id = csd_row['CSDUID']
    csd_geom = csd_row.geometry
    csd_area = csd_row['area_km2']

    # Find intersecting ecozone
    intersecting = ecozone[ecozone.geometry.intersects(csd_geom)]

    if len(intersecting) == 0:
        ecozone_assignments.append({
            'CSDUID': csd_id,
            'assigned_ecozone': 'No ecozone',
            'ecozone_count': 0,
            'all_ecozone': 'No ecozone',
            'dominant_ecozone': 'No',
            'coverage_pct': 0,
            'assignment_error': False
        })
    elif len(intersecting) == 1:
        ecozone_assignments.append({
            'CSDUID': csd_id,
            'assigned_ecozone': intersecting.iloc[0]['ZONE_NAME'],
            'ecozone_count': 1,
            'all_ecozone': intersecting.iloc[0]['ZONE_NAME'],
            'dominant_ecozone': 'Yes',
            'coverage_pct': 100.0,
            'assignment_error': False
        })
    else:
        # Multiple ecozone - calculate coverage percentages
        coverage_data = []
        for _, ecozone_row in intersecting.iterrows():
            intersection = csd_geom.intersection(ecozone_row.geometry)
            intersection_area_km2 = gpd.GeoSeries([intersection], crs=urban_csd_shp.crs).area.iloc[0] / 1_000_000
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
                'all_ecozone': all_zones,
                'dominant_ecozone': 'Yes',
                'coverage_pct': round(max_coverage, 2),
                'assignment_error': False
            })
        else:
            ecozone_assignments.append({
                'CSDUID': csd_id,
                'assigned_ecozone': 'ERROR: No dominant ecozone',
                'ecozone_count': len(intersecting),
                'all_ecozone': all_zones,
                'dominant_ecozone': 'No',
                'coverage_pct': round(max_coverage, 2),
                'assignment_error': True
            })

# Convert to DataFrame and merge
ecozone_df = pd.DataFrame(ecozone_assignments)
csd_urban = urban_csd_shp.merge(ecozone_df, on='CSDUID', how='left')

print("Assign ecozones:")
print(csd_urban[['CSDUID', 'CSDNAME', 'assigned_ecozone', 'dominant_ecozone', 'coverage_pct']].head(
    10).to_string(index=False))

# Report CSDs in multiple ecozone
multi_ecozone_csds = csd_urban[csd_urban['ecozone_count'] > 1]
print(f"\n--- CSDs spanning multiple ecozone: {len(multi_ecozone_csds)} ---")
if len(multi_ecozone_csds) > 0:
    print(multi_ecozone_csds[
              ['CSDUID', 'CSDNAME', 'all_ecozone', 'assigned_ecozone', 'dominant_ecozone', 'coverage_pct']].to_string(
        index=False))
else:
    print("None")

# Report assignment errors
error_csds = csd_urban[csd_urban['assignment_error']]
print(f"\n--- ERROR: CSDs with no dominant ecozone (< 50% coverage): {len(error_csds)} ---")
if len(error_csds) > 0:
    print(error_csds[['CSDUID', 'CSDNAME', 'all_ecozone', 'coverage_pct']].to_string(index=False))
    print("\n*** ATTENTION: These CSDs could not be assigned to a single ecozone ***")
else:
    print("None - all multi-ecozone CSDs have a dominant zone")

#endregion

## --------------------------------------------------- SAVE OUTPUTS ----------------------------------------------------
#region

urban_df.to_csv('Datasets/Outputs/2021_census_of_population/2021_census_of_population_municipalities.csv', index=False)
print(f"\nFinal urban dataset saved to "
      f"'Datasets/Outputs/2021_census_of_population/2021_census_of_population_municipalities.csv' ({len(urban_df)} rows)")

# Create a copy with shortened column names for shapefile compatibility
csd_urban_shp = csd_urban.copy()
csd_urban_shp = csd_urban_shp.rename(columns={
    'assigned_ecozone': 'assign_eco',
    'ecozone_count': 'eco_count',
    'all_ecozone': 'all_eco',
    'dominant_ecozone': 'dom_eco',
    'coverage_pct': 'cover_pct',
    'assignment_error': 'assign_err'
})

# Save polygons (both formats)
urban_shp_path = 'Datasets/Outputs/urban_csds/urban_csds.shp'
csd_urban_shp.to_file(urban_shp_path, driver="ESRI Shapefile")
print(f"Saved polygons (shapefile) to: {urban_shp_path}")

urban_gpkg_path = 'Datasets/Outputs/urban_csds/urban_csds.gpkg'
csd_urban.to_file(urban_gpkg_path, driver="GPKG")
print(f"Saved polygons (geopackage) to: {urban_gpkg_path}")

# Save centroids (both formats)
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

# Save attribute table as CSV (with full column names)
csv_data = csd_urban[['CSDUID', 'CSDNAME', 'PRUID', 'province', 'area_km2', 'assigned_ecozone', 'dominant_ecozone',
                      'coverage_pct']].copy()
csv_path = 'Datasets/Outputs/urban_csds/urban_csds_attributes.csv'
csv_data.to_csv(csv_path, index=False)
print(f"Saved attribute table to: {csv_path}")

#endregion

## ----------------------------------------- MAP CSDs WITHIN MULTIPLE ECOZONES -----------------------------------------
#region

# Define ecozone colours organized by groups
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

# Flatten the dictionary for plotting
ecozone_colours = {zone: color for group in ecozone_groups.values() for zone, color in group.items()}

# Map CSDs with multiple ecozone
if len(multi_ecozone_csds) > 0:
    print(f"\nGenerating maps for {len(multi_ecozone_csds)} CSDs spanning multiple ecozone...")

    for idx, row in multi_ecozone_csds.iterrows():
        csd_geom = row.geometry
        csd_name = row['CSDNAME']
        csd_id = row['CSDUID']

        # Find which ecozone intersect this specific CSD
        intersecting_ecozone = ecozone[ecozone.geometry.intersects(csd_geom)].copy()

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 10))

        # Plot the ecozones that intersect this CSD with custom colors
        intersecting_ecozone_3857 = intersecting_ecozone.to_crs(epsg=3857)
        for zone_name, color in ecozone_colours.items():
            ecozone_subset = intersecting_ecozone_3857[intersecting_ecozone_3857['ZONE_NAME'] == zone_name]
            if not ecozone_subset.empty:
                ecozone_subset.plot(
                    ax=ax,
                    color=color,
                    alpha=0.35,
                    edgecolor='black',
                    linewidth=2
                )

        # Plot the CSD boundary on top
        csd_3857 = gpd.GeoSeries([csd_geom], crs=csd_urban.crs).to_crs(epsg=3857)
        csd_3857.plot(
            ax=ax,
            edgecolor='red',
            facecolor='none',
            linewidth=4
        )

        # Add ecozone labels
        for _, ecozone_row in intersecting_ecozone.iterrows():
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
        ax.set_title(f'{csd_name} (CSDUID: {csd_id})\nEcozones: {row["all_ecozone"]}',
                     fontsize=14, fontweight='bold', pad=20)
        ax.set_axis_off()

        plt.tight_layout()
        plt.show()

    print(f"Completed mapping {len(multi_ecozone_csds)} CSDs with multiple ecozone.\n")
else:
    print("\nNo CSDs span multiple ecozone - no maps to generate.\n")

#endregion

## ----------------------------------------- MAP THE URBAN CSDs WITH ECOZONES ------------------------------------------
#region

# Create figure and axis
fig, ax = plt.subplots(figsize=(15, 10))

# Plot provinces as base layer (with edges)
provinces_gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.5)

# Flatten the dictionary for plotting
ecozone_colours = {zone: color for group in ecozone_groups.values() for zone, color in group.items()}

# Clip ecozones to province boundaries
ecozone_clipped = gpd.overlay(ecozone, provinces_gdf, how='intersection')

# Map colors to ecozone
ecozone_clipped['color'] = ecozone_clipped['ZONE_NAME'].map(ecozone_colours)

# Plot ecozone with custom colors
for zone_name, color in ecozone_colours.items():
    ecozone_subset = ecozone_clipped[ecozone_clipped['ZONE_NAME'] == zone_name]
    if not ecozone_subset.empty:
        ecozone_subset.plot(ax=ax,
                           color=color,
                           alpha=0.55,
                           edgecolor='darkgray',
                           linewidth=0.5)

print(f"Number of CSDs to plot: {len(centroids_gpkg)}")

# Plot CSDs as black points
centroids_gpkg.plot(ax=ax,
                   color='black',
                   markersize=25,
                   alpha=0.7)

# Create combined legend with grouped ecozone
combined_legend_elements = []

# Add ecozone by group
for group_name, zones in ecozone_groups.items():
    # Add group header (bold text, no patch)
    combined_legend_elements.append(Patch(facecolor='none', edgecolor='none',
                                         label=f'$\\bf{{{group_name}}}$ $\\bf{{ecozone}}$'))
    # Add each zone in the group (indented with spaces)
    for zone_name, color in zones.items():
        if zone_name in ecozone['ZONE_NAME'].values:
            combined_legend_elements.append(Patch(facecolor=color, alpha=0.5,
                                                 edgecolor='darkgray',
                                                 label=f'  {zone_name}'))

# Add a separator
combined_legend_elements.append(Patch(facecolor='none', edgecolor='none', label=''))

# Add municipality section header (bold)
combined_legend_elements.append(Patch(facecolor='none', edgecolor='none',
                                     label='$\\bf{Municipalities}$'))

# Add municipality legend elements
combined_legend_elements.extend([
    Line2D([0], [0], marker='o', color='w', markerfacecolor='black',
           markersize=10, alpha=0.6, label='  Eligible'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
           markersize=12, alpha=0.8, label='  Participating')
])

# Add the combined legend
ax.legend(handles=combined_legend_elements,
         loc='center left',
         bbox_to_anchor=(1, 0.5),
         fontsize=12,
         title='Legend',
         framealpha=0.9)

# Remove axes
ax.set_axis_off()

plt.tight_layout()
plt.savefig('figures/eligible_csds/eligible_csds_nationally.pdf')
plt.show()

# Define regions using PRUID values directly
regions = {
    "British Columbia": [59],
    "Prairies": [48, 47, 46],
    "Ontario": [35],
    "Québec": [24],
    "Atlantic Canada": [10, 11, 12, 13]
}

# Function to create legend elements
def create_legend_elements(ecozone_in_region):
    """Create legend elements for ecozone and municipalities present in the region"""
    legend_elements = []

    # Add ecozone by group
    for group_name, zones in ecozone_groups.items():
        zones_in_region = [z for z in zones.keys() if z in ecozone_in_region]
        if zones_in_region:
            # Add group header
            legend_elements.append(Patch(facecolor='none', edgecolor='none',
                                         label=f'$\\bf{{{group_name}}}$ $\\bf{{ecozone}}$'))
            # Add each zone in the group
            for zone_name in zones_in_region:
                color = zones[zone_name]
                legend_elements.append(Patch(facecolor=color, alpha=0.5,
                                             edgecolor='darkgray',
                                             label=f'  {zone_name}'))

    # Add separator
    legend_elements.append(Patch(facecolor='none', edgecolor='none', label=''))

    # Add municipality section
    legend_elements.append(Patch(facecolor='none', edgecolor='none',
                                 label='$\\bf{Municipalities}$'))
    legend_elements.extend([
        Line2D([0], [0], marker='o', color='w', markerfacecolor='black',
               markersize=10, alpha=0.6, label='  Eligible'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
               markersize=12, alpha=0.8, label='  Participating')
    ])

    return legend_elements


# Create a plot for each region
for region_name, pruid_list in regions.items():
    # Filter provinces for this region
    region_provinces = provinces_gdf[provinces_gdf['PRUID'].astype(int).isin(pruid_list)]

    if region_provinces.empty:
        print(f"Warning: No provinces found for {region_name}")
        continue

    # Filter ecozone by PRUID
    region_ecozone = ecozone[ecozone['PRUID'].isin(pruid_list)]

    # Filter communities by PRUID
    region_communities = centroids_gpkg[centroids_gpkg['PRUID'].isin(pruid_list)]

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 10))

    # Plot provinces as base layer
    region_provinces.plot(ax=ax,
                          facecolor='none',
                          edgecolor='black',
                          linewidth=1.5)

    # Clip ecozones to regional province boundaries
    region_ecozone_clipped = gpd.overlay(region_ecozone, region_provinces, how='intersection')

    # Plot ecozone with custom colors
    ecozone_in_region = []
    for zone_name, color in ecozone_colours.items():
        ecozone_subset = region_ecozone_clipped[region_ecozone_clipped['ZONE_NAME'] == zone_name]
        if not ecozone_subset.empty:
            ecozone_in_region.append(zone_name)
            ecozone_subset.plot(ax=ax,
                                color=color,
                                alpha=0.55,
                                edgecolor='darkgray',
                                linewidth=0.5)

    # Plot CSDs
    centroids_gpkg.plot(ax=ax,
                        color='black',
                        markersize=25,
                        alpha=0.7)

    # Create and add legend (without title)
    legend_elements = create_legend_elements(ecozone_in_region)
    ax.legend(handles=legend_elements,
              loc='center left',
              bbox_to_anchor=(1, 0.5),
              fontsize=12,
              framealpha=0.9)

    # Remove axes (no title added)
    ax.set_axis_off()

    # Adjust layout and save
    plt.tight_layout()
    filename = f'figures/eligible_csds/eligible_csds_{region_name}.pdf'
    plt.savefig(filename, bbox_inches='tight')
    print(f"Saved: {filename}")
    plt.show()
    plt.close()

#endregion