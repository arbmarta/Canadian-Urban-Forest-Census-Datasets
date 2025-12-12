import pandas as pd

# Load data
csd = pd.read_csv('Datasets/Outputs/urban_csds/urban_csds_attributes.csv')
roads = pd.read_csv('Datasets/Outputs/roads/road_lengths_by_csd.csv')
canopy_csds = pd.read_csv('Datasets/Outputs/canopy_cover_csd.csv')
canopy_roads_20m = pd.read_csv('Datasets/Outputs/gee_export/canopy_cover_road_buffers_20m.csv')

print("Original columns:")
print("CSD:", csd.columns.tolist())
print("Roads:", roads.columns.tolist())
print("Canopy in CSDs:", canopy_csds.columns.tolist())
print("Canopy near roads:", canopy_roads_20m.columns.tolist())

print("\nData types:")
print("CSD CSDUID:", csd['CSDUID'].dtype)
print("Roads CSDUID:", roads['CSDUID'].dtype)
print("Canopy CSDUID:", canopy_csds['CSDUID'].dtype)
print("Canopy near roads:", canopy_roads_20m['CSDUID'].dtype)

# ---------- Add suffixes to canopy tables ----------
# Add '_csd' to all canopy_csds columns except the join key CSDUID
canopy_csds_renamed = canopy_csds.rename(
    columns={c: f"{c}_csd" for c in canopy_csds.columns if c != "CSDUID"}
)

# Add '_20m_buffer' to all canopy_roads_20m columns except the join key CSDUID
canopy_roads_renamed = canopy_roads_20m.rename(
    columns={c: f"{c}_20m_buffer" for c in canopy_roads_20m.columns if c != "CSDUID"}
)

print("\nAfter suffixing canopy columns:")
print("Canopy in CSDs:", canopy_csds_renamed.columns.tolist())
print("Canopy near roads:", canopy_roads_renamed.columns.tolist())

# Merge datasets
merged = csd.merge(roads, on='CSDUID', how='inner') \
    .merge(canopy_csds, on='CSDUID', how='inner') \
    .merge(canopy_roads_20m, on='CSDUID', how='inner')

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
        print("\n✓ All rows have dominant_ecozone = 'Yes'!")
        print("  The dominant_ecozone column can be safely dropped if not needed.")

else:
    print("\n⚠️  ERROR: 'dominant_ecozone' column not found in merged dataframe!")

print("\n" + "=" * 70)

# Create the rename mapping dictionary
rename_mapping = {
    'CSDUID': 'CSDUID',
    'CSDNAME_x': 'CSDNAME',
    'area_km2': 'csd_area_km2',
    'assigned_ecozone': 'ecozone',
    'coverage_pct': 'ecozone_coverage_pct',
    'length_km': 'road_length_km',
    'total_area_km2': 'total_area_km2',
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
df.to_csv('Datasets/Outputs/merged_urban_data.csv', index=False)
print("\nMerged data saved to 'Datasets/Outputs/merged_urban_data.csv'")