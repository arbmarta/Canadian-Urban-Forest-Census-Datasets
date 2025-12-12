import os
import glob
import shutil
from datetime import datetime
import pandas as pd

# ---------- Config ----------
MASTER_FILENAME = "canopy_cover_road_buffers_10m.csv"  # master file in same folder
BATCH_GLOB = "canopy_cover_road_buffer_batch_*.csv"  # pattern to find batch files
BACKUP_DIR = "backups"                               # where to put master backups
# ----------------------------

cwd = os.getcwd()
master_path = os.path.join(cwd, MASTER_FILENAME)

# Ensure backup dir exists
os.makedirs(BACKUP_DIR, exist_ok=True)

# Load (or create) master dataframe
if os.path.exists(master_path):
    master_df = pd.read_csv(master_path)
    print(f"Loaded master file '{MASTER_FILENAME}' with {len(master_df)} rows "
          f"and {master_df['CSDUID'].nunique() if 'CSDUID' in master_df.columns else 'N/A'} unique CSDUIDs.")
else:
    # If the master doesn't exist, create empty DataFrame (we'll infer columns from first batch)
    master_df = pd.DataFrame()
    print(f"Master file '{MASTER_FILENAME}' not found. A new master will be created if batch files exist.")

# Find batch files in current dir that match the pattern
batch_files = sorted(glob.glob(os.path.join(cwd, BATCH_GLOB)))
print(f"Found {len(batch_files)} batch file(s).")

if not batch_files:
    print("No batch files to process. Exiting.")
    raise SystemExit(0)

# Read batch files with error handling
batch_dfs = []
for f in batch_files:
    try:
        df_temp = pd.read_csv(f)
        df_temp['_source_file'] = os.path.basename(f)  # optional: track origin
        batch_dfs.append(df_temp)
        print(f"  -> Loaded '{f}' ({len(df_temp)} rows).")
    except Exception as e:
        print(f"  ! Skipping '{f}' due to read error: {e}")

if not batch_dfs:
    print("No valid batch dataframes were loaded. Exiting.")
    raise SystemExit(1)

batch_df = pd.concat(batch_dfs, ignore_index=True)
print(f"Total rows loaded from batch files: {len(batch_df)}")
if 'CSDUID' in batch_df.columns:
    print(f"Unique CSDUIDs in batches: {batch_df['CSDUID'].nunique()}")
else:
    print("Warning: 'CSDUID' column not found in batch files. Merge/dedup will fail.")

# If master is empty, initialize its columns from batch_df
if master_df.empty:
    master_df = pd.DataFrame(columns=batch_df.columns)
    print("Master dataframe was empty; initialized master with batch columns.")

# Make a backup of the current master before overwriting (if it exists)
if os.path.exists(master_path):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{os.path.splitext(MASTER_FILENAME)[0]}_backup_{ts}.csv"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy(master_path, backup_path)
    print(f"Backup of master saved to: {backup_path}")

# Merge: append batch rows to master and drop duplicate CSDUIDs.
# NOTE: keep='first' will keep the first occurrence in the concatenated DataFrame.
# Because we concat [master_df, batch_df], this keeps the existing master values for duplicate CSDUIDs.
merged_df = pd.concat([master_df, batch_df], ignore_index=True)

if 'CSDUID' in merged_df.columns:
    before_unique = master_df['CSDUID'].nunique() if 'CSDUID' in master_df.columns else 0
    total_before = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=["CSDUID"], keep="first")
    after_unique = merged_df['CSDUID'].nunique()
    print(f"After drop_duplicates (keep='first'): rows {total_before} -> {len(merged_df)}; "
          f"unique CSDUIDs: {before_unique} -> {after_unique}.")
else:
    print("Warning: 'CSDUID' not found; no duplicate removal performed.")

# Save merged back to master file
merged_df.to_csv(master_path, index=False)
print(f"Master file updated and saved to: {master_path}")
