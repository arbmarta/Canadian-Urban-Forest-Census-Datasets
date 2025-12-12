import pandas as pd
import os

def clean_columns(df, pattern_to_remove):
    """Remove symbol columns and clean column names"""
    # Remove columns starting with "Symbol"
    df = df.loc[:, ~df.columns.str.startswith("Symbol")]

    # Remove specified pattern and trailing brackets
    df.columns = (df.columns
                  .str.replace(pattern_to_remove, "", regex=True)
                  .str.replace(r"\[.*\]$", "", regex=True))
    return df

## ------------------------------------------------ Load and clean data ------------------------------------------------
#region

# Eligible csduids list
eligible_csduid = pd.read_csv('Datasets/Inputs/eligible_csduid.csv')

# Input directory
base_path = 'Datasets/Inputs/2021_census_of_population/'  # Adjust to your directory

datasets = {
    'population': ('98100002.csv', r"Population and dwelling counts \(13\): "),
    'dwellings': ('98100041.csv', r"Household size \(8\):"),
    'indigenous': ('98100293.csv', r"Indigenous identity \(9\):"),
    'minorities': ('98100352.csv', r"Visible minority \(15\):"),
    'labour': ('98100485.csv', r"Gender \(3\):"),
}

dfs={}
for name, (file, pattern) in datasets.items():
    file_path = os.path.join(base_path, file)
    df = clean_columns(pd.read_csv(file_path), pattern)
    df = df[df['DGUID'].str.len() == 16]

    # Filter age columns if present
    if 'Age (8G)' in df.columns:
        df = df[df['Age (8G)'] == 'Total - Age']
    if 'Age (15C)' in df.columns:
        df = df[df['Age (15C)'] == 'Total - Age']
    if 'Age (15A)' in df.columns:
        df = df[df['Age (15A)'] == 'Total - Age']

    # Filter gender columns if present
    if 'Gender (3a)' in df.columns:
        df = df[df['Gender (3a)'] == 'Total - Gender']
    if 'Gender (3)' in df.columns:
        df = df[df['Gender (3)'] == 'Total - Gender']

    # Filter Statistics column if present
    if 'Statistics (5)' in df.columns:
        df = df[df['Statistics (5)'] == '2021 Counts']
    if 'Statistics (2)' in df.columns:
        df = df[df['Statistics (2)'] == '2021 Counts']
    if 'Labour force status (8)' in df.columns:
        df = df[df['Labour force status (8)'] == 'In the labour force']

    # Special handling for dwellings - pivot the structural types
    if name == 'dwellings' and 'Structural type of dwelling (9)' in df.columns:
        # Get the Average household size for "Total - Structural type of dwelling"
        avg_household = df[df['Structural type of dwelling (9)'] == 'Total - Structural type of dwelling'][
            ['DGUID', 'Average household size']]

        # Pivot so each structural type becomes a column
        df = df.pivot(
            index='DGUID',
            columns='Structural type of dwelling (9)',
            values='Total - Household size'
        ).reset_index()

        # Clean up column names
        df.columns.name = None  # Remove the column index name

        # Merge back the Average household size
        df = df.merge(avg_household, on='DGUID', how='left')

    dfs[name] = df

# Import gender separately (Men+ only)
gender = pd.read_csv('Datasets/Inputs/2021_census_of_population/98100032.csv') # 98100032.csv
gender = gender[(gender["Gender (3a)"] == "Men+") & (gender["Broad age groups (5)"] == "Total - Age")]
gender = clean_columns(gender, r"View: ")
gender = gender[gender['DGUID'].str.len() == 16]
dfs['gender'] = gender

# Use LEFT merge with population as the base
merged = dfs['population']
merged = merged.merge(dfs['gender'], on='DGUID', how='left', suffixes=('_pop', '_gender'))
merged = merged.merge(dfs['dwellings'], on='DGUID', how='left', suffixes=('', '_dwell'))
merged = merged.merge(dfs['labour'], on='DGUID', how='left', suffixes=('', '_labour'))
merged = merged.merge(dfs['indigenous'], on='DGUID', how='left', suffixes=('', '_indig'))
merged = merged.merge(dfs['minorities'], on='DGUID', how='left', suffixes=('', '_minor'))

# Strip blank space at the end of column names
merged.columns = merged.columns.str.rstrip()

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
}

# Keep only specified columns that exist in the dataframe
existing_columns = [col for col in columns_to_rename.keys() if col in merged.columns]
merged = merged[existing_columns]

# Rename columns
merged = merged.rename(columns=columns_to_rename)

#endregion

## ------------------------------------------ Set up the two different export ------------------------------------------
#region

# Create percentage columns for dwelling types
dwelling_types = [
    'Number of Single-detached Houses',
    'Number of Semi-detached Houses',
    'Number of Row Houses',
    'Number of Apartments (duplex)',
    'Number of Apartments (<5 story buildings)',
    'Number of Apartments (5+ story buildings)',
    'Number of Other Single-attached Houses',
    'Number of Movable Dwellings'
]

# Create percentage columns for indigenous identity
indigenous_types = [
    'Indigenous identity: Indigenous identity count',
    'Single Indigenous responses',
    'Single Indigenous responses: First Nations',
    'Single Indigenous responses: Métis',
    'Single Indigenous responses: Inuit',
    'Multiple Indigenous responses'
]

# Create percentage columns for visible minorities
minority_types = [
    'Visible minority: Total visible minority population',
    'Visible minority: South Asian',
    'Visible minority: Chinese',
    'Visible minority: Black',
    'Visible minority: Filipino',
    'Visible minority: Arab',
    'Visible minority: Latin American',
    'Visible minority: Southeast Asian',
    'Visible minority: West Asian',
    'Visible minority: Korean',
    'Visible minority: Japanese',
    'Visible minority: Multiple visible minorities',
    'Visible minority: Not a visible minority'
]

# Clean CSDUID column
merged["CSDUID"] = merged["CSDUID"].astype(str).str.replace(r"^2021A0005", "", regex=True)

#endregion

## ------------------------------------------- Statistics of municipalities --------------------------------------------
#region

columns_to_sum = ['Population, 2021', 'Population, 2016', 'Land Area (sq km)', 'Number of Men', 'Men in Workforce',
                  'People in Workforce', 'Number of Private Dwellings, 2021', 'Number of Private Dwellings, 2016',
                  'Number of Occupied Private Dwellings, 2021', 'Number of Occupied Private Dwellings, 2016',
                  'Average Household Size', 'Number of Single-detached Houses', 'Number of Semi-detached Houses',
                  'Number of Row Houses', 'Number of Apartments (duplex)', 'Number of Apartments (<5 story buildings)',
                  'Number of Apartments (5+ story buildings)', 'Number of Other Single-attached Houses',
                  'Number of Movable Dwellings', 'Total Dwellings by Type', 'Indigenous identity: total count',
                  'Indigenous identity: Indigenous identity count', 'Single Indigenous responses',
                  'Single Indigenous responses: First Nations', 'Single Indigenous responses: Métis',
                  'Single Indigenous responses: Inuit', 'Multiple Indigenous responses',
                  'Visible minority: total counts', 'Visible minority: Total visible minority population',
                  'Visible minority: South Asian', 'Visible minority: Chinese', 'Visible minority: Black',
                  'Visible minority: Filipino', 'Visible minority: Arab', 'Visible minority: Latin American',
                  'Visible minority: Southeast Asian', 'Visible minority: West Asian', 'Visible minority: Korean',
                  'Visible minority: Japanese', 'Visible minority: Multiple visible minorities',
                  'Visible minority: Not a visible minority']

# Create copy of merged df to merge Lloydminster and Diamond Valley
municipalities_merged = merged.copy()

# Sum values for Lloydminster (4717029 + 4810039) and overwrite 4810039
lloydminster_mask = municipalities_merged['CSDUID'].isin(['4717029', '4810039'])
lloydminster_sum = municipalities_merged[lloydminster_mask][columns_to_sum].sum()

# Overwrite 4810039 with summed values
for col in columns_to_sum:
    municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', col] = lloydminster_sum[col]

# Delete 4717029
municipalities_merged = municipalities_merged[municipalities_merged['CSDUID'] != '4717029']
print("Merged Lloydminster: 4717029 deleted, values summed into 4810039")

# Sum values for Diamond Valley (4806009 + 4806011) and overwrite 4806011
diamond_valley_mask = municipalities_merged['CSDUID'].isin(['4806009', '4806011'])
diamond_valley_sum = municipalities_merged[diamond_valley_mask][columns_to_sum].sum()

# Overwrite 4806011 with summed values
for col in columns_to_sum:
    municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', col] = diamond_valley_sum[col]

# Delete 4806009
municipalities_merged = municipalities_merged[municipalities_merged['CSDUID'] != '4806009']
print("Merged Diamond Valley: 4806009 deleted, values summed into 4806011")

# Recalculate for Lloydminster (4810039)
municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Population Density (sq km)'] = (
    municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Population, 2021'].values[0] /
    municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Land Area (sq km)'].values[0]
)

municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Population Change (%), 2016 to 2021'] = (
    ((municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Population, 2021'].values[0] -
      municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Population, 2016'].values[0]) /
     municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Population, 2016'].values[0]) * 100
)

municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Total Private Dwellings Change (%), 2016 to 2021'] = (
    ((municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Number of Private Dwellings, 2021'].values[0] -
      municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Number of Private Dwellings, 2016'].values[0]) /
     municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Number of Private Dwellings, 2016'].values[0]) * 100
)

municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Occupied Dwellings Change (%), 2016 to 2021'] = (
    ((municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Number of Occupied Private Dwellings, 2021'].values[0] -
      municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Number of Occupied Private Dwellings, 2016'].values[0]) /
     municipalities_merged.loc[municipalities_merged['CSDUID'] == '4810039', 'Number of Occupied Private Dwellings, 2016'].values[0]) * 100
)

# Recalculate for Diamond Valley (4806011)
municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Population Density (sq km)'] = (
    municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Population, 2021'].values[0] /
    municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Land Area (sq km)'].values[0]
)

municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Population Change (%), 2016 to 2021'] = (
    ((municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Population, 2021'].values[0] -
      municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Population, 2016'].values[0]) /
     municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Population, 2016'].values[0]) * 100
)

municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Total Private Dwellings Change (%), 2016 to 2021'] = (
    ((municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Number of Private Dwellings, 2021'].values[0] -
      municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Number of Private Dwellings, 2016'].values[0]) /
     municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Number of Private Dwellings, 2016'].values[0]) * 100
)

municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Occupied Dwellings Change (%), 2016 to 2021'] = (
    ((municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Number of Occupied Private Dwellings, 2021'].values[0] -
      municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Number of Occupied Private Dwellings, 2016'].values[0]) /
     municipalities_merged.loc[municipalities_merged['CSDUID'] == '4806011', 'Number of Occupied Private Dwellings, 2016'].values[0]) * 100
)

for indigenous in indigenous_types:
    if (indigenous in municipalities_merged.columns and 'Indigenous identity: total count' in
            municipalities_merged.columns):
        municipalities_merged[f'{indigenous} (%)'] = (municipalities_merged[indigenous] /
                                                      municipalities_merged['Indigenous identity: total count']
                                                      * 100).round(2)

for dwelling in dwelling_types:
    if dwelling in municipalities_merged.columns and 'Total Dwellings by Type' in municipalities_merged.columns:
        municipalities_merged[f'{dwelling} (%)'] = (municipalities_merged[dwelling] /
                                                    municipalities_merged['Total Dwellings by Type']
                                                    * 100).round(2)

for minority in minority_types:
    if minority in municipalities_merged.columns and 'Visible minority: total counts' in municipalities_merged.columns:
        municipalities_merged[f'{minority} (%)'] = (municipalities_merged[minority] /
                                                    municipalities_merged['Visible minority: total counts']
                                                    * 100).round(2)

# Create percentage for men
if 'Number of Men' in municipalities_merged.columns and 'Population, 2021' in municipalities_merged.columns:
    municipalities_merged['Number of Men (%)'] = (municipalities_merged['Number of Men']
                                                  / municipalities_merged['Population, 2021'] * 100).round(2)

if 'Men in Workforce' in municipalities_merged.columns and 'People in Workforce' in municipalities_merged.columns:
    municipalities_merged['Men in Workforce (%)'] = (municipalities_merged['Men in Workforce']
                                                     / municipalities_merged['People in Workforce'] * 100).round(2)

# Clean CSDUID column
municipalities_merged["CSDUID"] = municipalities_merged["CSDUID"].astype(str).str.replace(r"^2021A0005", "", regex=True)

# Load eligible CSDs
eligible_csduid = pd.read_csv('Datasets/Inputs/eligible_csduid.csv')
eligible_csduid['CSDUID'] = pd.to_numeric(eligible_csduid['CSDUID'], errors='coerce')

# Convert municipalities_merged CSDUID to numeric for comparison
municipalities_merged['CSDUID'] = pd.to_numeric(municipalities_merged['CSDUID'], errors='coerce')

# Filter to keep only eligible CSDs
municipalities_merged = municipalities_merged[municipalities_merged['CSDUID'].isin(eligible_csduid['CSDUID'])]

print(f"\nNumber of rows in the municipalities dataset: {len(municipalities_merged)}")

# Save to a CSV
municipalities_merged.to_csv('Datasets/Outputs/2021_census_of_population/2021_census_of_population_municipalities.csv', index=False)
print("Saved to 'Datasets/Outputs/2021_census_of_population/2021_census_of_population_municipalities.csv'")

#endregion