INSERT INTO workflow.skelet_pipe_data (id, skelet)
SELECT id, ST_CollectionExtract(ST_ApproximateMedialAxis(ST_SimplifyPolygonHull(mask, 0.1)), 2)
FROM workflow.raw_mask_data;