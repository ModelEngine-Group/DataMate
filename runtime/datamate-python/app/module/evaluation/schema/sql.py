SELECT_EVALUATED_FILE = """
select task_id, file_id, total_count, evaluated_count, pending_count from
(select
    task_id,
    file_id,
    COUNT(*) OVER (PARTITION BY task_id, file_id) as total_count,
    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END)
        OVER (PARTITION BY task_id, file_id) as evaluated_count,
    SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END)
        OVER (PARTITION BY task_id, file_id) as pending_count
from t_de_eval_item
where task_id = :task_id) tmp
group by file_id, total_count, evaluated_count, pending_count
order by total_count DESC, evaluated_count DESC, file_id
limit :limit offset :offset;
"""

COUNT_EVALUATED_FILE = """
select COUNT(1) from
(select
    task_id,
    file_id
from t_de_eval_item
where task_id = :task_id
group by file_id) tmp
"""
