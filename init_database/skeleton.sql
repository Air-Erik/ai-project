INSERT INTO workflow.skelet_pipe_data (id, skelet)
SELECT id, ST_CollectionExtract(ST_ApproximateMedialAxis(mask), 2)
FROM workflow.raw_mask_data;