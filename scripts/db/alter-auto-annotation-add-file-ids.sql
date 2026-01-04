-- 为自动标注任务表添加 file_ids 字段
-- 用于存储用户选择的文件ID列表（JSON格式）

USE datamate;

-- 只有在表存在且字段不存在时才执行 ALTER，避免初始化阶段报错中断后续脚本
SET @table_exists := (
		SELECT COUNT(*)
		FROM information_schema.tables
		WHERE table_schema = DATABASE()
			AND table_name = 't_dm_auto_annotation_tasks'
);

SET @column_exists := (
		SELECT COUNT(*)
		FROM information_schema.columns
		WHERE table_schema = DATABASE()
			AND table_name = 't_dm_auto_annotation_tasks'
			AND column_name = 'file_ids'
);

SET @ddl := IF(
		@table_exists = 1 AND @column_exists = 0,
		'ALTER TABLE t_dm_auto_annotation_tasks ADD COLUMN file_ids JSON COMMENT "要处理的文件ID列表，为空则处理数据集所有图像" AFTER config',
		'SELECT 1'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
