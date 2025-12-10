# Description
This repository houses files used in the analysis of the Canadian Urban Forest Census (2025).

# Datasets

| File Name | Relevant Code | Source File | Source Format | Description |
|-----------|----------------|-------------|----------------|-------------|
| **urban_csds** (.shp; .gpkg) | `analysis.py` | 2021 Census Subdivision Boundary File | Cartographic Boundary File (CBF) | Polygons of 343 census subdivisions that are not Indigenous communities and meet the Statistics Canada definition of urban. |
| **urban_csd_centerpoints** (.shp; .gpkg) | `analysis.py` | `urban_csds.gpkg` | Polygons | Centerpoints generated for the 343 urban census subdivisions. |
| **clipped_roads** (.shp; .gpkg) | `roads.py` | 2024 Intercensal Road Network File | Polylines | Road network clipped to the boundaries of the 343 urban census subdivisions. |
| **road_buffers** (.shp; .gpkg) | `roads.py` | `clipped_roads.gpkg` | Polylines | Buffered versions of the clipped road network features. |


## Urban Census Subdivisions 
**File Name:** urban_csds (.shp; .gpkg)

**Relevant Code:** analysis.py

**Source File:** Census Subdivision shapefile (2021 Census Boundary Files) \
**Source Format:** Cartographic Boundary File (CBF)

This geopackage includes polygons of the 343 census subdivisions that are not Indigenous communities (i.e., First Nations reserves) and meet the definition of urban used by Statistics Canada:

> Urban areas are those continuously built-up areas having a minimum population concentration of 1,000 persons and a population density of at least 400 persons per square kilometer based on the previous census. (Statistical Classifications: Urban and rural areas - 'Urban' versus 'rural' variant)

Additional edits were performed after excluding Indigenous and non-urban census subdivisions:
1. The two Lloydminster parts (Alberta and Saskatchewan) were merged as it represents one inter-provincial city
2. Turner Valley and Black Diamond, Alberta were merged in keeping with their amalgamation
3. Petit-Rocher, New Brunswick was removed as its new land area results in a population density below the definition of urban used by Statistics Canada.

## Urban Census Subdivision Centerpoints
**File Name:** urban_csd_centerpoints (.shp; .gpkg)

**Relevant Code:** analysis.py

**Source File:** urban_csds.gpkg\
**Source Format:** polygons

This geopackage includes centerpoints of the 343 urban census subdivisions.

## Road Network File
**File Name:** clipped_roads (.shp; .gpkg)

**Relevant Code:** roads.py

**Source File:** Intercensal - Road network files (2024 road network file) \
**Source Format:** polylines

This geopackage includes polylines of roads within the 343 urban census subdivisions, clipped to the boundaries of the urban census subdivisions.

## Road Buffer File
**File Name:** road_buffers (.shp; .gpkg)

**Relevant Code:** roads.py

**Source File:** clipped_roads.gpkg\
**Source Format:** polylines

This geopackage includes polylines of roads within the 343 urban census subdivisions, clipped to the boundaries of the urban census subdivisions.
