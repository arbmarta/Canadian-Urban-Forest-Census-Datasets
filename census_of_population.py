import pandas as pd
import numpy as np
from functools import reduce

## ------------------------------------------------ LOAD AND CLEAN DATA ------------------------------------------------
#region

# load datasets
population = pd.read_csv('Datasets/Inputs/2021_census_of_population/population.csv')
labour = pd.read_csv('Datasets/Inputs/2021_census_of_population/labour.csv')
indigenous_identity = pd.read_csv('Datasets/Inputs/2021_census_of_population/indigenous_identity.csv')
visible_minorities = pd.read_csv('Datasets/Inputs/2021_census_of_population/visible_minorities.csv')

amalgamated_csv_path = 'Datasets/Inputs/2021_census_of_population/amalgamated_cities.csv'

# Drop CSDNAME from all datasets except population
for dataset in [labour, indigenous_identity, visible_minorities]:
    dataset.drop(columns=['CSDNAME'], errors='ignore', inplace=True)

# Merge all dataframes
df = reduce(lambda left, right: left.merge(right, on='CSDUID', how='outer'),
            [population, labour, indigenous_identity, visible_minorities])

print("Columns in merged dataset:")
print(df.columns)

#endregion

## --------------------------------------------- HANDLE AMALGAMATED CITIES ---------------------------------------------
#region

# CSDUIDs to remove from the original df before concatenation
to_remove_csduids = {'4810039', '4717029', '4806011', '4806009'}
key_col = 'CSDUID'

print(f"\nTotal number of CSDs before amalgamation: {len(df)}")

# ---------- LOAD amalgamated CSV ----------
am_df = pd.read_csv(amalgamated_csv_path)

# ---------- NORMALIZE KEY COLUMN ----------
df[key_col] = df[key_col].astype(str).str.strip()
am_df[key_col] = am_df[key_col].astype(str).str.strip()

# ---------- HARMONIZE DTYPES ----------
# Convert amalgamated numeric columns to match original df's float64
numeric_cols = ['Population, 2021', 'Total private dwellings',
                'Private dwellings occupied by usual residents']
for col in numeric_cols:
    if col in am_df.columns:
        am_df[col] = am_df[col].astype('float64')

print("\nAMALGAMATION PROCESS:")
print(f" - CSDUIDs to remove: {sorted(to_remove_csduids)}")
print(f" - Rows in amalgamated CSV: {len(am_df)}")
print(f" - Amalgamated CSDUIDs: {sorted(am_df[key_col].unique())}")

# ---------- Remove specified CSDs and add amalgamated ones ----------
df_without = df[~df[key_col].isin(to_remove_csduids)].copy()
print(f" - Rows after removing specified CSDUIDs: {len(df_without)}")

# Ensure column order matches
am_df = am_df[df.columns]

# Concatenate
df = pd.concat([df_without, am_df], axis=0, ignore_index=True, sort=False)

# Validate no duplicates
dup_counts = df[key_col].value_counts()
duplicates = dup_counts[dup_counts > 1]
if not duplicates.empty:
    print("\nERROR: Duplicate CSDUIDs detected!")
    print(duplicates)
    raise RuntimeError("Aborting: duplicates found after concatenation.")

print(f" - Total rows after amalgamation: {len(df)}")
print("SUCCESS: Amalgamation complete, no duplicates detected.\n")

#endregion

## --------------------------------------- REMOVE NON-URBAN AND INDIGENOUS CSDs ----------------------------------------
#region

print(f"Total number of CSDs in dataset (after amalgamation): {len(df)}")

# Filter for urban CSDs
urban_df = df[(df['Population, 2021'] >= 1000) & (df['Population Density (sq km)'] >= 400)].copy()

# Combined exclusion pattern (exclude CSDs with digits in name, PETIT-ROCHER, or WENDAKE)
exclusion_pattern = r'\d|PETIT-ROCHER|WENDAKE'
urban_df = urban_df[~urban_df['CSDNAME'].str.contains(exclusion_pattern, case=False, na=False)]

print(f"Number of urban and non-Indigenous CSDs: {len(urban_df)}")

# Verify amalgamated cities are included
amalgamated_in_urban = urban_df[urban_df[key_col].isin(am_df[key_col].unique())]
print(f"Amalgamated cities in urban dataset: {len(amalgamated_in_urban)}")
if not amalgamated_in_urban.empty:
    print("Amalgamated cities included:")
    print(amalgamated_in_urban[['CSDNAME', 'CSDUID', 'Population, 2021']].to_string(index=False))

#endregion

## ------------------------------------------------- SAVE OUTPUT -------------------------------------------------------
#region

urban_df.to_csv('Datasets/Outputs/2021_census_of_population/2021_census_of_population_municipalities.csv', index=False)
print(f"\nFinal urban dataset saved to "
      f"'Datasets/Outputs/2021_census_of_population/2021_census_of_population_municipalities.csv' ({len(urban_df)} rows)")

#endregion