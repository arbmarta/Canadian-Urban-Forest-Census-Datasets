# Description
This repository houses files used in the analysis of the Canadian Urban Forest Census (2025).

## Urban Census Subdivisions 
File Name: urban_csds.gpkg (layer = 'urban_csds')

Source File: Census Subdivision shapefile (2021 Census Boundary Files)
Source Format: Cartographic Boundary File (CBF)

This geopackage includes polygons of the 343 census subdivisions that are not Indigenous communities (i.e., First Nations reserves) and meet the definition of urban used by Statistics Canada:

> Urban areas are those continuously built-up areas having a minimum population concentration of 1,000 persons and a population density of at least 400 persons per square kilometer based on the previous census. (Statistical Classifications: Urban and rural areas - 'Urban' versus 'rural' variant)

Additional edits were performed after excluding Indigenous and non-urban census subdivisions. First, the two Lloydminster parts (Alberta and Saskatchewan) were joined. Next, Turner Valley and Black Diamond, Alberta were joined in keeping with their amalgamation. Lastly, Petit Roche, New Brunswick was removed as its new land area results in a population density below the definition of urban used by Statistics Canada.
