import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import warnings

from config import participating_csds, ecozone_groups, regions

# Load data
csd = pd.read_csv('Datasets/Outputs/urban_csds/urban_csds_attributes.csv')
roads = pd.read_csv('Datasets/Outputs/roads/road_lengths_by_csd.csv')
canopy_csds = pd.read_csv('Datasets/Outputs/gee_export/canopy_cover_csd.csv')
canopy_roads_10m = pd.read_csv('Datasets/Outputs/gee_export/canopy_cover_road_buffers_10m.csv')
canopy_roads_20m = pd.read_csv('Datasets/Outputs/gee_export/canopy_cover_road_buffers_20m.csv')
census = pd.read_csv('Datasets/Outputs/2021_census_of_population/2021_census_of_population_municipalities.csv')

print("Original columns:")
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

# Merge datasets
merged = csd.merge(roads, on='CSDUID', how='inner') \
    .merge(canopy_csds_renamed, on='CSDUID', how='inner') \
    .merge(canopy_roads_10m_renamed, on='CSDUID', how='inner') \
    .merge(canopy_roads_20m_renamed, on='CSDUID', how='inner') \
    .merge(census, on='CSDUID', how='inner')

print("\nMerged data info:")
print("Rows:", len(merged))
print("Columns:", merged.columns.tolist())

# ======================================================================
# CHECK DOMINANT_ECOZONE VALUES
# ======================================================================
print("\n" + "=" * 70)
print("CHECKING DOMINANT_ECOZONE VALUES")
print("=" * 70)

if 'dominant_ecozone' in merged.columns:
    # Check for values that are not 'Yes'
    not_yes_mask = merged['dominant_ecozone'] != 'Yes'

    # Count non-Yes values
    num_not_yes = not_yes_mask.sum()
    total_rows = len(merged)

    print(f"\nTotal rows: {total_rows}")
    print(f"Rows where dominant_ecozone = 'Yes': {total_rows - num_not_yes}")
    print(f"Rows where dominant_ecozone ≠ 'Yes': {num_not_yes}")

    if num_not_yes > 0:
        print(f"\n⚠️  WARNING: {num_not_yes} rows have dominant_ecozone values that are NOT 'Yes'!")
        print("\nRows with non-'Yes' values:")
        print("-" * 70)

        not_yes_df = merged[not_yes_mask][
            ['CSDUID', 'CSDNAME_x', 'assigned_ecozone', 'dominant_ecozone', 'coverage_pct']].copy()

        # Display all non-Yes rows
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(not_yes_df.to_string(index=True))

        # Summary of non-Yes values
        print("\n" + "-" * 70)
        print("NON-'Yes' VALUE SUMMARY:")
        print("-" * 70)
        print("\nUnique values in dominant_ecozone (non-'Yes' rows):")
        print(not_yes_df['dominant_ecozone'].value_counts())

        print("\nAssigned ecozone for these rows:")
        print(not_yes_df['assigned_ecozone'].value_counts())

        print("\nCoverage % statistics for non-'Yes' rows:")
        print(not_yes_df['coverage_pct'].describe())

    else:
        print("\n✓ All rows have dominant_ecozone = 'Yes'")
        print("  The dominant_ecozone column can be safely dropped if not needed.")

else:
    print("\n⚠️  ERROR: 'dominant_ecozone' column not found in merged dataframe")

print("\n" + "=" * 70)

# Create the rename mapping dictionary
rename_mapping = {
    'CSDUID': 'CSDUID',
    'CSDNAME_x': 'CSDNAME',
    'area_km2': 'csd_area_km2',
    'assigned_ecozone': 'ecozone',
    'coverage_pct': 'ecozone_coverage_pct',
    'length_km': 'road_length_km',
    'canopy_area_km2': 'canopy_area_csd_km2',
    'canopy_proportion': 'canopy_proportion_csd'
}

df = merged.copy()

# Drop dominant_ecozone if all values are 'Yes'
if 'dominant_ecozone' in df.columns:
    not_yes_mask = df['dominant_ecozone'] != 'Yes'
    if not not_yes_mask.any():
        df = df.drop(columns=['dominant_ecozone'])
        print("\ndominant_ecozone dropped (all values were 'Yes').")
    else:
        print("\ndominant_ecozone kept (contains non-'Yes' values).")

# --- 1) Check if CSDNAME_y exists before comparing ---
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

print("\nFinal columns after renaming:")
print(df.columns.tolist())

# Save result
df.to_csv('Datasets/Outputs/Canadian_urban_forest_census_independent_variables.csv', index=False)
print("\nMerged data saved to 'Datasets/Outputs/Canadian_urban_forest_census_independent_variables.csv'")

# Suppress the specific GeoPandas overlay warning
warnings.filterwarnings('ignore', message='.*keep_geom_type.*')

participating_set = set(participating_csds)

# --- Import datasets ---
provinces = gpd.read_file('Datasets/Inputs/provinces/provinces_simplified_1km.gpkg')
csds = gpd.read_file('Datasets/Outputs/urban_csd_centroids/urban_csd_centroids.gpkg')
ecozones = gpd.read_file('Datasets/Inputs/ecozone_shp/ecozones.shp')
ecozones = ecozones.to_crs(provinces.crs)  # match ecozone CRS to provinces

csds['CSDUID_num'] = pd.to_numeric(csds['CSDUID'], errors='coerce')

# --- Ensure PRUID is consistent type across all dataframes ---
provinces['PRUID'] = provinces['PRUID'].astype(int)
csds['PRUID'] = csds['PRUID'].astype(int)

# --- Ensure CSDUID exists and create safe numeric column for matching ---
if 'CSDUID' not in csds.columns:
    # try a few common alternatives, else raise helpful error
    alt_columns = [c for c in csds.columns if c.lower().replace('_', '') in ('csduid','csd_uid','csduid')]
    if alt_columns:
        csds = csds.rename(columns={alt_columns[0]: 'CSDUID'})
        print(f"Renamed column {alt_columns[0]} -> 'CSDUID' for matching.")
    else:
        raise KeyError(f"'CSDUID' column not present in csds. Columns are: {csds.columns.tolist()}")

# Safe numeric coercion (leave NaNs where coercion fails)
csds['CSDUID_num'] = pd.to_numeric(csds['CSDUID'], errors='coerce')

# Optional: create an integer column for matching (dropping rows where coercion failed)
csds['CSDUID_int'] = csds['CSDUID_num'].dropna().astype(int)

# --- Diagnostics: check list vs csds ---
list_len = len(participating_csds)
unique_list_len = len(participating_set)
unique_csds_in_df = set(csds['CSDUID_int'].dropna().astype(int).unique())

in_both = participating_set & unique_csds_in_df
in_list_not_in_csds = participating_set - unique_csds_in_df
in_csds_not_in_list = unique_csds_in_df - participating_set

print(f"Participating list length: {list_len} (unique: {unique_list_len})")
print(f"Unique CSDUIDs in csds: {len(unique_csds_in_df)}")
print(f"IDs in list AND csds: {len(in_both)}")
print(f"IDs in list BUT NOT in csds: {len(in_list_not_in_csds)}")
if in_list_not_in_csds:
    print(" - Examples missing from csds:", list(in_list_not_in_csds)[:10])

# --- Fix spelling mistake in Boreal Plain ---
ecozones['ZONE_NAME'] = ecozones['ZONE_NAME'].replace('Boreal PLain', 'Boreal Plain')

# --- Clip ecozones to provincial boundaries for national map ---
ecozones = gpd.overlay(ecozones, provinces, how='intersection')

# --- Create figure and axis for national map ---
fig, ax = plt.subplots(figsize=(15, 10))

# Base provinces
provinces.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.5)

# Flatten mapping and assign colors
ecozone_colours = {zone: color for group in ecozone_groups.values() for zone, color in group.items()}
ecozones['color'] = ecozones['ZONE_NAME'].map(ecozone_colours)

# Plot ecozones
for zone_name, color in ecozone_colours.items():
    ecozone_subset = ecozones[ecozones['ZONE_NAME'] == zone_name]
    if not ecozone_subset.empty:
        ecozone_subset.plot(ax=ax, color=color, alpha=0.55, edgecolor='darkgray', linewidth=0.5)

# --- Use CSDUID membership to separate eligible / participating ---
# Note: use the integer column for matching; rows with NaN CSDUID_int will be treated as eligible (not in list)
eligible_only = csds[~csds['CSDUID_int'].isin(participating_set)]
participating = csds[csds['CSDUID_int'].isin(participating_set)]

# Print counts based on membership (these should be consistent)
total_count = len(eligible_only) + len(participating)
print(f"Number of municipalities (rows in csds used in national map): {total_count}")
print(f"Number of eligible (non-participating) municipalities: {len(eligible_only)}")
print(f"Number of participating municipalities (by CSDUID list): {len(participating)}")
print(f"Number of UNIQUE participating CSDUIDs matched in csds: {participating['CSDUID_int'].dropna().astype(int).nunique()}")

# Plot eligible (non-participating) communities as black points
eligible_only.plot(ax=ax,
                   color='black',
                   markersize=25,
                   alpha=0.7)

# Plot participating municipalities as red points (larger)
participating.plot(ax=ax,
                   color='red',
                   markersize=40,
                   alpha=0.9)

# Create combined legend with grouped ecozones
combined_legend_elements = []

# Add ecozones by group
for group_name, zones in ecozone_groups.items():
    # Add group header (bold text, no patch)
    combined_legend_elements.append(Patch(facecolor='none', edgecolor='none',
                                         label=f'$\\bf{{{group_name}}}$ $\\bf{{Ecozones}}$'))
    # Add each zone in the group (indented with spaces)
    for zone_name, color in zones.items():
        if zone_name in ecozones['ZONE_NAME'].values:
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
plt.savefig('figures/Survey participation - national.pdf')
plt.show()

# Function to create legend elements
def create_legend_elements(ecozones_in_region):
    """Create legend elements for ecozones and municipalities present in the region"""
    legend_elements = []

    # Add ecozones by group
    for group_name, zones in ecozone_groups.items():
        zones_in_region = [z for z in zones.keys() if z in ecozones_in_region]
        if zones_in_region:
            # Add group header
            legend_elements.append(Patch(facecolor='none', edgecolor='none',
                                         label=f'$\\bf{{{group_name}}}$ $\\bf{{Ecozones}}$'))
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
    region_provinces = provinces[provinces['PRUID'].isin(pruid_list)]

    if region_provinces.empty:
        print(f"Warning: No provinces found for {region_name}")
        continue

    # Filter ecozones by PRUID
    region_ecozones = gpd.overlay(ecozones, region_provinces, how='intersection')

    # Filter communities by PRUID
    region_communities = csds[csds['PRUID'].isin(pruid_list)]

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 10))

    # Plot provinces as base layer
    region_provinces.plot(ax=ax,
                          facecolor='none',
                          edgecolor='black',
                          linewidth=1.5)

    # Plot ecozones with custom colors
    ecozones_in_region = []
    for zone_name, color in ecozone_colours.items():
        ecozone_subset = region_ecozones[region_ecozones['ZONE_NAME'] == zone_name]
        if not ecozone_subset.empty:
            ecozones_in_region.append(zone_name)
            ecozone_subset.plot(ax=ax,
                                color=color,
                                alpha=0.55,
                                edgecolor='darkgray',
                                linewidth=0.5)

    # Separate eligible and participating municipalities
    eligible_only = region_communities[~region_communities['CSDUID_int'].isin(participating_set)]
    participating = region_communities[region_communities['CSDUID_int'].isin(participating_set)]

    # Plot eligible (non-participating) communities
    if not eligible_only.empty:
        eligible_only.plot(ax=ax,
                           color='black',
                           markersize=50,
                           alpha=0.7)

    # Plot participating municipalities
    if not participating.empty:
        participating.plot(ax=ax,
                           color='red',
                           markersize=80,
                           alpha=0.9)

    # Create and add legend (without title)
    legend_elements = create_legend_elements(ecozones_in_region)
    ax.legend(handles=legend_elements,
              loc='center left',
              bbox_to_anchor=(1, 0.5),
              fontsize=12,
              framealpha=0.9)

    # Remove axes (no title added)
    ax.set_axis_off()

    # Adjust layout and save
    plt.tight_layout()
    filename = f'figures/Survey participation - {region_name}.pdf'
    plt.savefig(filename, bbox_inches='tight')
    print(f"Saved: {filename}")
    plt.show()
    plt.close()

print("\nAll regional maps created successfully!")