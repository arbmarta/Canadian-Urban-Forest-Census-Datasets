import os
import pandas as pd

# Folder containing all CSVs
folder = "Datasets/Outputs/gee_export"

# Path to the master file
master_path = os.path.join(folder, "canopy_cover_road_buffers.csv")

# Load the existing master dataframe
master_df = pd.read_csv(master_path)

print(f"Loaded master file with {len(master_df)} rows.")
print(f"Number of unique CSDUIDs: {master_df['CSDUID'].nunique()}")

print(master_df['CSDUID'].unique())

exit()
# Find all batch files
batch_files = [
    os.path.join(folder, f)
    for f in os.listdir(folder)
    if f.startswith("canopy_cover_road_buffer_batch_") and f.endswith(".csv")
]

print(f"Found {len(batch_files)} batch files.")

# Load all batch files
batch_df = pd.concat((pd.read_csv(f) for f in batch_files), ignore_index=True)

print(f"Loaded {len(batch_df)} new rows from batch files.")

# Merge safely and drop duplicate CSDUIDs
merged_df = pd.concat([master_df, batch_df], ignore_index=True)

# Remove duplicates based on CSDUID (keep the first occurrence)
merged_df = merged_df.drop_duplicates(subset=["CSDUID"], keep="first")

print(f"After merging and removing duplicates, final row count: {len(merged_df)}")

# Save back to the master file
merged_df.to_csv(master_path, index=False)

print(f"Master file updated: {master_path}")
