import pandas as pd
import glob

# Pattern for matching files
file_list = glob.glob("canopy_cover_road_buffer_batch_*.csv")

# Read and concatenate
df = pd.concat((pd.read_csv(f) for f in file_list), ignore_index=True)

print(df['CSDUID'].nunique())
print(df.columns)

# Count occurrences of each CSDUID
counts = df["CSDUID"].value_counts().rename("count")

# Group by CSDUID and sum the area columns
grouped = (
    df.groupby("CSDUID", as_index=False)
      .agg({
          "total_area_km2": "sum",
          "canopy_area_km2": "sum"
      })
)

# Compute canopy proportion (%)
grouped["canopy_proportion"] = (
    grouped["canopy_area_km2"] / grouped["total_area_km2"]
) * 100

print(grouped)

# ---- SAVE TO CSV ----
grouped.to_csv("canopy_cover_road_buffer_batch_export_5.csv", index=False)
print("Saved grouped results")
