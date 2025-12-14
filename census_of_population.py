import pandas as pd
import geopandas as gpd
import numpy as np
import os

## ----------------------------------------------------- FUNCTIONS -----------------------------------------------------
#region

def clean_columns(df, pattern_to_remove):
    """Remove symbol columns and clean column names"""
    # Remove columns starting with "Symbol"
    df = df.loc[:, ~df.columns.str.startswith("Symbol")]

    # Remove specified pattern and trailing brackets
    df.columns = (df.columns
                  .str.replace(pattern_to_remove, "", regex=True)
                  .str.replace(r"\[.*\]$", "", regex=True))
    return df


def recalculate_derived_metrics(df, csduid):
    """Calculate derived metrics for a given CSDUID in place"""
    idx = df['CSDUID'] == csduid

    # Population Density
    df.loc[idx, 'Population Density (sq km)'] = (
            df.loc[idx, 'Population, 2021'] / df.loc[idx, 'Land Area (sq km)']
    )

    # Population Change %
    df.loc[idx, 'Population Change (%), 2016 to 2021'] = (
            ((df.loc[idx, 'Population, 2021'] - df.loc[idx, 'Population, 2016'])
             / df.loc[idx, 'Population, 2016']) * 100
    )

    # Total Private Dwellings Change %
    df.loc[idx, 'Total Private Dwellings Change (%), 2016 to 2021'] = (
            ((df.loc[idx, 'Number of Private Dwellings, 2021'] - df.loc[idx, 'Number of Private Dwellings, 2016'])
             / df.loc[idx, 'Number of Private Dwellings, 2016']) * 100
    )

    # Occupied Dwellings Change %
    df.loc[idx, 'Occupied Dwellings Change (%), 2016 to 2021'] = (
            ((df.loc[idx, 'Number of Occupied Private Dwellings, 2021'] - df.loc[
                idx, 'Number of Occupied Private Dwellings, 2016'])
             / df.loc[idx, 'Number of Occupied Private Dwellings, 2016']) * 100
    )


def merge_csd_pairs(df, csd_to_keep, csd_to_remove, columns_to_sum):
    """Merge two CSDs by summing their values"""
    mask = df['CSDUID'].isin([csd_to_keep, csd_to_remove])
    summed_values = df.loc[mask, columns_to_sum].sum()

    # Update the CSD to keep with summed values
    df.loc[df['CSDUID'] == csd_to_keep, columns_to_sum] = summed_values.values

    # Remove the other CSD
    df = df[df['CSDUID'] != csd_to_remove]

    return df


def add_percentage_columns(df, value_cols, total_col, percentage_types):
    """Add percentage columns for a set of value columns relative to a total"""
    if total_col not in df.columns:
        return

    for col in value_cols:
        if col in df.columns:
            df[f'{col} (%)'] = (df[col] / df[total_col] * 100).round(2)

#endregion

## ------------------------------------------------ LOAD AND CLEAN DATA ------------------------------------------------
#region

# Fetch CSDUID to CSDNAME from shapefile
csd_shp = gpd.read_file('Datasets/Inputs/census_subdivisions_2021/census_subdivisions_2021.shp')

# Input directory
base_path = 'Datasets/Inputs/2021_census_of_population/'

datasets = {
    'population': ('98100002.csv', r"Population and dwelling counts \(13\): "),
    'dwellings': ('98100041.csv', r"Household size \(8\):"),
    'indigenous': ('98100293.csv', r"Indigenous identity \(9\):"),
    'minorities': ('98100352.csv', r"Visible minority \(15\):"),
    'labour': ('98100485.csv', r"Gender \(3\):"),
}

dfs = {}
for name, (file, pattern) in datasets.items():
    file_path = os.path.join(base_path, file)
    df = clean_columns(pd.read_csv(file_path), pattern)
    df = df[df['DGUID'].str.len() == 16]

    # Define common filters
    filters = {
        'Age (8G)': 'Total - Age',
        'Age (15C)': 'Total - Age',
        'Age (15A)': 'Total - Age',
        'Gender (3a)': 'Total - Gender',
        'Gender (3)': 'Total - Gender',
        'Statistics (5)': '2021 Counts',
        'Statistics (2)': '2021 Counts',
        'Labour force status (8)': 'In the labour force'
    }

    # Apply filters that exist in the dataframe
    for col, value in filters.items():
        if col in df.columns:
            df = df[df[col] == value]

    # Special handling for dwellings - pivot the structural types
    if name == 'dwellings' and 'Structural type of dwelling (9)' in df.columns:
        avg_household = df[df['Structural type of dwelling (9)'] == 'Total - Structural type of dwelling'][
            ['DGUID', 'Average household size']]

        df = df.pivot(
            index='DGUID',
            columns='Structural type of dwelling (9)',
            values='Total - Household size'
        ).reset_index()

        df.columns.name = None
        df = df.merge(avg_household, on='DGUID', how='left')

    dfs[name] = df

# Import gender separately (Men+ only)
gender = pd.read_csv('Datasets/Inputs/2021_census_of_population/98100032.csv')
gender = gender[(gender["Gender (3a)"] == "Men+") & (gender["Broad age groups (5)"] == "Total - Age")]
gender = clean_columns(gender, r"View: ")
gender = gender[gender['DGUID'].str.len() == 16]
dfs['gender'] = gender

# Merge all datasets
all_csds = dfs['population']
all_csds = all_csds.merge(dfs['gender'], on='DGUID', how='left', suffixes=('_pop', '_gender'))
all_csds = all_csds.merge(dfs['dwellings'], on='DGUID', how='left', suffixes=('', '_dwell'))
all_csds = all_csds.merge(dfs['labour'], on='DGUID', how='left', suffixes=('', '_labour'))
all_csds = all_csds.merge(dfs['indigenous'], on='DGUID', how='left', suffixes=('', '_indig'))
all_csds = all_csds.merge(dfs['minorities'], on='DGUID', how='left', suffixes=('', '_minor'))

# Strip blank space at the end of column names
all_csds.columns = all_csds.columns.str.rstrip()

# Columns to rename
columns_to_rename = {
    'DGUID': 'CSDUID',
    'Population, 2021': 'Population, 2021',
    'Population, 2016': 'Population, 2016',
    'Population density per square kilometre, 2021': 'Population Density (sq km)',
    'Land area in square kilometres, 2021': 'Land Area (sq km)',
    'Population percentage change, 2016 to 2021': 'Population Change (%), 2016 to 2021',

    'View:2021 counts': 'Number of Men',
    'Men+': 'Men in Workforce',
    'Total - Gender': 'People in Workforce',

    'Total private dwellings, 2021': 'Number of Private Dwellings, 2021',
    'Total private dwellings, 2016': 'Number of Private Dwellings, 2016',
    'Private dwellings occupied by usual residents, 2021': 'Number of Occupied Private Dwellings, 2021',
    'Private dwellings occupied by usual residents, 2016': 'Number of Occupied Private Dwellings, 2016',
    'Average household size': 'Average Household Size',
    'Total private dwellings percentage change, 2016 to 2021': 'Total Private Dwellings Change (%), 2016 to 2021',
    'Private dwellings occupied by usual residents percentage change, 2016 to 2021': 'Occupied Dwellings Change (%), 2016 to 2021',

    'Total - Indigenous identity': 'Indigenous identity: total count',
    'Indigenous identity': 'Indigenous identity: Indigenous identity count',

    'Total - Visible minority': 'Visible minority: total counts',
    'Total visible minority population': 'Visible minority: Total visible minority population',
}

# List of all columns
"""

'DGUID': 'CSDUID',
'Population, 2021': 'Population, 2021',
'Population, 2016': 'Population, 2016',
'Population density per square kilometre, 2021': 'Population Density (sq km)',
'Land area in square kilometres, 2021': 'Land Area (sq km)',
'Population percentage change, 2016 to 2021': 'Population Change (%), 2016 to 2021',

'View:2021 counts': 'Number of Men',
'Men+': 'Men in Workforce',
'Total - Gender': 'People in Workforce',

'Total private dwellings, 2021': 'Number of Private Dwellings, 2021',
'Total private dwellings, 2016': 'Number of Private Dwellings, 2016',
'Private dwellings occupied by usual residents, 2021': 'Number of Occupied Private Dwellings, 2021',
'Private dwellings occupied by usual residents, 2016': 'Number of Occupied Private Dwellings, 2016',
'Average household size': 'Average Household Size',
'Total private dwellings percentage change, 2016 to 2021': 'Total Private Dwellings Change (%), 2016 to 2021',
'Private dwellings occupied by usual residents percentage change, 2016 to 2021': 'Occupied Dwellings Change (%), 2016 to 2021',

'Single-detached house': 'Number of Single-detached Houses',
'Semi-detached house': 'Number of Semi-detached Houses',
'Row house': 'Number of Row Houses',
'Apartment or flat in a duplex': 'Number of Apartments (duplex)',
'Apartment in a building that has fewer than five storeys': 'Number of Apartments (<5 story buildings)',
'Apartment in a building that has five or more storeys': 'Number of Apartments (5+ story buildings)',
'Other single-attached house': 'Number of Other Single-attached Houses',
'Movable dwelling': 'Number of Movable Dwellings',
'Total - Structural type of dwelling': 'Total Dwellings by Type',

'Total - Indigenous identity': 'Indigenous identity: total count',
'Indigenous identity': 'Indigenous identity: Indigenous identity count',
'Single Indigenous responses': 'Single Indigenous responses',
'First Nations (North American Indian)': 'Single Indigenous responses: First Nations',
'Métis': 'Single Indigenous responses: Métis',
'Inuk (Inuit)': 'Single Indigenous responses: Inuit',
'Multiple Indigenous responses': 'Multiple Indigenous responses',

'Total - Visible minority': 'Visible minority: total counts',
'Total visible minority population': 'Visible minority: Total visible minority population',
'South Asian': 'Visible minority: South Asian',
'Chinese': 'Visible minority: Chinese',
'Black': 'Visible minority: Black',
'Filipino': 'Visible minority: Filipino',
'Arab': 'Visible minority: Arab',
'Latin American': 'Visible minority: Latin American',
'Southeast Asian': 'Visible minority: Southeast Asian',
'West Asian': 'Visible minority: West Asian',
'Korean': 'Visible minority: Korean',
'Japanese': 'Visible minority: Japanese',
'Multiple visible minorities': 'Visible minority: Multiple visible minorities',
'Not a visible minority': 'Visible minority: Not a visible minority'

"""

# Keep only specified columns that exist in the dataframe
existing_columns = [col for col in columns_to_rename.keys() if col in all_csds.columns]
all_csds = all_csds[existing_columns]

# Rename columns
all_csds = all_csds.rename(columns=columns_to_rename)

# Clean CSDUID column (only once!)
all_csds["CSDUID"] = all_csds["CSDUID"].astype(str).str.replace(
    r"^2021A0005", "", regex=True
)

#endregion

## ------------------- MERGE LLOYDMINSTER, DIAMOND VALLEY, AND REMOVE NON-URBAN AND INDIGENOUS CSDs --------------------
#region

# Define columns to sum for merging operations
columns_to_sum = ['Population, 2021', 'Population, 2016', 'Population Density (sq km)', 'Land Area (sq km)',
                  'Population Change (%), 2016 to 2021', 'Number of Men', 'Men in Workforce', 'People in Workforce',
                  'Number of Private Dwellings, 2021', 'Number of Private Dwellings, 2016',
                  'Number of Occupied Private Dwellings, 2021', 'Number of Occupied Private Dwellings, 2016',
                  'Average Household Size', 'Total Private Dwellings Change (%), 2016 to 2021',
                  'Occupied Dwellings Change (%), 2016 to 2021', 'Indigenous identity: total count',
                  'Indigenous identity: Indigenous identity count', 'Visible minority: total counts',
                  'Visible minority: Total visible minority population']

# Merge Lloydminster (4717029 + 4810039) into 4810039
csds_merged = merge_csd_pairs(all_csds, '4810039', '4717029', columns_to_sum)
recalculate_derived_metrics(csds_merged, '4810039')
print("Merged Lloydminster: 4717029 deleted, values summed into 4810039")

# Merge Diamond Valley (4806009 + 4806011) into 4806011
csds_merged = merge_csd_pairs(csds_merged, '4806011', '4806009', columns_to_sum)
recalculate_derived_metrics(csds_merged, '4806011')
print("Merged Diamond Valley: 4806009 deleted, values summed into 4806011")

# Filter for urban CSDs — use csds_merged (the post-merge frame)
urban_csds = csds_merged[
    (csds_merged['Population, 2021'] >= 1000) &
    (csds_merged['Population Density (sq km)'] >= 400)
]

# Merge with shapefile and exclude Indigenous CSDs
urban_csds = urban_csds.merge(
    csd_shp[['CSDUID', 'CSDNAME']],
    on='CSDUID',
    how='left'
)

# Combined exclusion pattern
exclusion_pattern = r'\d|PETIT-ROCHER|WENDAKE'
urban_csds = urban_csds[
    ~urban_csds['CSDNAME'].str.contains(exclusion_pattern, case=False, na=False)
]

print("\nNumber of CSDs after merging Lloydminster and Diamond Valley:", len(csds_merged))
print("Number of CSDs after excluding non-urban & Indigenous CSDs:", len(urban_csds))

#endregion

## ----------------------------------------- CALCULATE PROPORTIONAL STATISTICS -----------------------------------------
#region

# Define percentage rules: (value_cols_list, total_col)
percentage_rules = [
    (['Indigenous identity: Indigenous identity count'], 'Indigenous identity: total count'),
    (['Visible minority: Total visible minority population'], 'Visible minority: total counts'),
    (['Number of Men'], 'Population, 2021'),
    (['Men in Workforce'], 'People in Workforce'),
]

def safe_pct(df, value_col, total_col):
    """Return percent series (rounded 2dp) safely handling zeros/NaNs/infs."""
    if value_col not in df.columns or total_col not in df.columns:
        return None
    # Use elementwise division, suppress divide-by-zero producing inf, then round
    pct = df[value_col].astype(float).div(df[total_col].replace({0: np.nan})).mul(100)
    pct = pct.replace([np.inf, -np.inf], np.nan).round(2)
    return pct

# Apply all percentage rules
for value_cols, total_col in percentage_rules:
    for col in value_cols:
        pct_series = safe_pct(urban_csds, col, total_col)
        if pct_series is not None:
            urban_csds[f'{col} (%)'] = pct_series

# Replace zeros with NaN for specific CSDs and columns
csd_zero_to_nan_rules = {
    '4806011': [  # Diamond Valley
        'Men in Workforce',
        'People in Workforce',
        'Indigenous identity: total count',
        'Indigenous identity: Indigenous identity count',
        'Visible minority: total counts',
        'Visible minority: Total visible minority population'
    ],
    '4810039': [  # Lloydminster
        'Men in Workforce',
        'People in Workforce',
        'Indigenous identity: total count',
        'Indigenous identity: Indigenous identity count',
    ]
}

for csduid, cols in csd_zero_to_nan_rules.items():
    mask = urban_csds['CSDUID'] == csduid
    urban_csds.loc[mask, cols] = urban_csds.loc[mask, cols].replace(0, np.nan)

# Clean up and save
urban_csds = urban_csds.drop(columns=['CSDNAME'], errors='ignore')

# Ensure output directory exists and save CSV
out_path = 'Datasets/Outputs/2021_census_of_population'
os.makedirs(out_path, exist_ok=True)
out_file = os.path.join(out_path, '2021_census_of_population_municipalities.csv')
urban_csds.to_csv(out_file, index=False)
print(f"\nSaved to '{out_file}'")

#endregion