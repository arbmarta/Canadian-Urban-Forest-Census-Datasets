// CSDUIDs to exclude
var excludeList = [];

// Set the projection to Statistics Canada Lambert
var statsCanLambert = ee.Projection('EPSG:3347');

// Access census subdivision shapefiles (urban_csds, road_buffers_10m, or road_buffers_20m)
var censusSub = ee.FeatureCollection('projects/heroic-glyph-383701/assets/road_buffers_10m')
  .filter(ee.Filter.inList('CSDUID', excludeList).not());

// Access Meta 1m Canopy Height Model
var canopyHeight = ee.ImageCollection('projects/meta-forest-monitoring-okw37/assets/CanopyHeight').mosaic();

// Reproject canopy height to Stats Can Lambert
var canopyHeightReprojected = canopyHeight.reproject({
  crs: statsCanLambert,
  scale: 1
});

// Create binary canopy layer (>= 2m = 1, < 2m = 0)
var canopyBinary = canopyHeightReprojected.gte(2);

// Display the binary canopy layer
Map.addLayer(canopyBinary.selfMask(), {palette: ['green']}, 'Canopy (>=2m)', false);

// Define batch parameters
var totalFeatures = censusSub.size();
var batchSize = 50; // Process x CSDs at a time
var batchNumber = 0; // Change this for each run (0, 1, 2, 3, etc.)

// Calculate start and end indices
var startIndex = batchNumber * batchSize;

// Get subset of features
var censusSubBatch = ee.FeatureCollection(censusSub.toList(batchSize, startIndex));

print('Total CSDs:', totalFeatures);
print('Processing batch:', batchNumber);
print('CSDs in this batch:', censusSubBatch.size());

// Function to calculate canopy metrics for each CSD
var calculateCanopyMetrics = function(feature) {
  // Get the geometry
  var geometry = feature.geometry();

  // Calculate pixel area in square meters (1m x 1m = 1 sq m per pixel)
  var pixelArea = ee.Image.pixelArea().reproject({
    crs: statsCanLambert,
    scale: 1
  });

  // Calculate total area of the CSD in square meters
  var totalArea = pixelArea.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geometry,
    crs: statsCanLambert,
    scale: 1,
    maxPixels: 1e13
  }).get('area');

  // Calculate canopy area (where binary = 1)
  var canopyAreaImage = canopyBinary.multiply(pixelArea);
  var canopyAreaResult = canopyAreaImage.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geometry,
    crs: statsCanLambert,
    scale: 1,
    maxPixels: 1e13
  });

  // Get the first (and only) value from the result
  var canopyArea = ee.Number(canopyAreaResult.values().get(0));

  // Convert to square kilometers
  var totalAreaKm2 = ee.Number(totalArea).divide(1e6);
  var canopyAreaKm2 = canopyArea.divide(1e6);

  // Calculate proportion as percentage
  var canopyProportion = canopyAreaKm2.divide(totalAreaKm2).multiply(100);

  // Add properties to feature
  return feature.set({
    'total_area_km2': totalAreaKm2,
    'canopy_area_km2': canopyAreaKm2,
    'canopy_proportion': canopyProportion
  });
};

// Calculate metrics for batch of CSDs
var censusWithCanopy = censusSubBatch.map(calculateCanopyMetrics);

// Set map center to Canada and zoom level
Map.setCenter(-96, 62, 4); // Centered on Canada

// Display the census subdivisions (showing full collection for reference)
Map.addLayer(censusSub, {color: 'blue'}, 'All Census Subdivisions', false);
Map.addLayer(censusSubBatch, {color: 'red'}, 'Current Batch', true);

// Print results
print('Census Subdivisions with Canopy Metrics:', censusWithCanopy);
print('Number of CSDs in batch:', censusWithCanopy.size());

// Export results to CSV with batch number in filename
Export.table.toDrive({
  collection: censusWithCanopy,
  description: 'canopy_cover_road_buffer_batch_' + batchNumber,
  fileFormat: 'CSV',
  selectors: ['CSDUID', 'total_area_km2', 'canopy_area_km2', 'canopy_proportion']
});

print('Export task created. Check the Tasks tab to run it.');