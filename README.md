# Description
This repository houses files used in the analysis of the Canadian Urban Forest Census (2025).

# Datasets

| File Name | File Type | Relevant Code | Source File | Source Format | Description |
|-----------|-----------|----------------|-------------|----------------|-------------|
| **urban_csds** | .shp; .gpkg | `analysis.py` | Census Subdivision Boundary File (2021) | Polygons | Final processed polygons representing 343 non-Indigenous urban census subdivisions. |
| **urban_csd_centroids** | .shp; .gpkg | `analysis.py` | `urban_csds.gpkg` | Points | Centroids generated from the final urban census subdivision polygons. |
| **urban_csds_attributes** | .csv | `analysis.py` | `urban_csds.gpkg` | Tabular | Attribute table containing CSDUID, CSDNAME, land area, assigned ecozone, dominance status, and percentage coverage. |
| **clipped_roads** | .shp; .gpkg | `roads.py` | 2024 Intercensal Road Network File | Polylines | Road network features clipped to the 343 urban census subdivision boundaries. |
| **road_buffers** | .shp; .gpkg | `roads.py` | `clipped_roads.gpkg` | Polylines | Buffered representations of clipped road features. |

## Determining Urban Areas
To determine urban municipalities, we use census subdivisions, which is Statistics Canada's dataset of municipal boundaries. We selected census subdivisions that meet the definition of urban used by Statistics Canada:

> Urban areas are those continuously built-up areas having a minimum population concentration of 1,000 persons and a population density of at least 400 persons per square kilometer based on the previous census. (Statistical Classifications: Urban and rural areas - 'Urban' versus 'rural' variant)

We then excluded Indigenous Communities because they operate under different governance structures.

Additional edits were performed after excluding non-urban and Indigenous census subdivisions:
1. The two Lloydminster parts (Alberta and Saskatchewan) were merged as it represents one inter-provincial city
2. Turner Valley and Black Diamond, Alberta were merged in keeping with their amalgamation
3. Petit-Rocher, New Brunswick was removed as its new land area results in a population density below the definition of urban used by Statistics Canada.
