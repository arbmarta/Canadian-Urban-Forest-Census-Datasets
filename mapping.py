import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

participating_csds = id_list = [1212014, 4817029, 4603053, 5915046, 5935010, 5915043, 5915051, 5903015, 5915011,
                                3530013, 4802019, 3547048, 3543031, 3509028, 3502008, 5917015, 3501012, 4602037,
                                4810039, 3523008, 1303012, 5917030, 1310032, 4613047, 4819012, 4617050, 3534011,
                                4602046, 5907041, 4611040, 4703036, 1211011, 4810028, 4812018, 3509004, 3522014,
                                4715008, 4702047, 4806006, 4806029, 3532004, 4708004, 4811049, 5915029, 5921018,
                                5915004, 5909052, 4806011, 5919021, 4808026, 1207024, 1102075, 5917040, 4701024,
                                3538019, 4602044, 3537039, 3534021, 4811068, 3529006, 4808012, 4620048, 5929005,
                                5926005, 5903045, 1102080, 3520005, 4803026, 4806017, 3518001, 5955014, 3518005,
                                4802013, 4806016, 4802012, 5927008, 3515014, 3538030, 3530016, 4706027, 3522021,
                                3521005, 4706039, 3502044, 4811018, 5917047, 4701008, 5921023, 5917044, 4715066,
                                5915015, 3519038, 4813019, 5915039, 3532042, 3530010, 4707039, 1001542, 4705016,
                                4614039, 1214002, 4808011, 3519028, 3547002, 4711070, 3514021, 4811019, 3524002,
                                3525005, 2442098, 2466117, 2466058, 2467020, 2443027, 2447025, 1314022, 2423057,
                                2472020, 2468030, 2421045, 2464008, 2471083, 2453052, 2475017, 2466032, 2466023,
                                2432040, 2447017, 2466102, 2459010, 2473020, 2467050, 2484060, 2456083, 2466107,
                                2458037, 2460013]

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
plt.savefig('Figures/Survey participation - national.pdf')
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
    filename = f'Figures/Survey participation - {region_name}.pdf'
    plt.savefig(filename, bbox_inches='tight')
    print(f"Saved: {filename}")
    plt.show()
    plt.close()

print("\nAll regional maps created successfully!")