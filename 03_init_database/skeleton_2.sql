INSERT INTO pipe.raw_pipe (id, pipe, class_id, plan_id)
SELECT 
	m.id
	ST_SnapToGrid(ST_CollectionExtract(ST_ApproximateMedialAxis(ST_SimplifyPolygonHull(m.mask_join, 0.1)), 2), 0.01),
	m.class_id,
	m.plan_id 
FROM pipe.mask_join m;