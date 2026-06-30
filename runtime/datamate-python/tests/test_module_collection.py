import pytest
from types import SimpleNamespace
from app.module.collection.schema.collection import converter_to_response, converter_execution_to_response

from app.module.collection.schema.collection import (
    CollectionConfig,
    CollectionTaskCreate,
    CollectionTaskUpdate,
    SyncMode,
    convert_for_create,
)


def test_collection_task_update_rejects_blank_schedule_expression() -> None:
    with pytest.raises(ValueError):
        CollectionTaskUpdate(schedule_expression="   ")


def test_collection_task_update_rejects_non_positive_timeout() -> None:
    with pytest.raises(ValueError):
        CollectionTaskUpdate(timeout_seconds=0)


def test_convert_for_create_handles_sync_mode_schedule_expression() -> None:
    config = CollectionConfig(parameter={"k": "v"})

    scheduled = CollectionTaskCreate(
        name="task-scheduled",
        sync_mode=SyncMode.SCHEDULED,
        schedule_expression="0 0 * * *",
        config=config,
        template_id="tpl-1",
    )
    once = CollectionTaskCreate(
        name="task-once",
        sync_mode=SyncMode.ONCE,
        schedule_expression="0 0 * * *",
        config=config,
        template_id="tpl-1",
    )

    scheduled_record = convert_for_create(scheduled, "task-1")
    once_record = convert_for_create(once, "task-2")

    assert scheduled_record.schedule_expression == "0 0 * * *"
    assert once_record.schedule_expression is None
    assert scheduled_record.target_path == "/dataset/local/task-1"


def test_collection_task_update_accepts_positive_timeout() -> None:
    updated = CollectionTaskUpdate(timeout_seconds=30)
    assert updated.timeout_seconds == 30


def test_convert_for_create_sets_pending_status() -> None:
    config = CollectionConfig(parameter={"k": "v"})
    once = CollectionTaskCreate(
        name="task-once",
        sync_mode=SyncMode.ONCE,
        config=config,
        template_id="tpl-1",
    )

    record = convert_for_create(once, "task-3")

    assert record.status == "PENDING"


def test_collection_task_update_accepts_none_fields() -> None:
    updated = CollectionTaskUpdate()
    assert updated.timeout_seconds is None
    assert updated.config is None


def test_converter_to_response_maps_json_config() -> None:
    task = SimpleNamespace(
        id="t1",
        name="task",
        description="desc",
        sync_mode="ONCE",
        template_id="tpl",
        template_name="template",
        target_path="/dataset/local/t1",
        config='{"parameter": {"a": 1}}',
        schedule_expression=None,
        status="PENDING",
        retry_count=3,
        timeout_seconds=60,
        last_execution_id="e1",
        created_at=None,
        updated_at=None,
        created_by="u",
        updated_by="u",
    )

    response = converter_to_response(task)

    assert response.id == "t1"
    assert response.config.parameter == {"a": 1}
    assert response.status.value == "PENDING"


def test_converter_execution_to_response_maps_fields() -> None:
    execution = SimpleNamespace(
        id="e1",
        task_id="t1",
        task_name="task",
        status="RUNNING",
        log_path="/x.log",
        started_at=None,
        completed_at=None,
        duration_seconds=1,
        error_message=None,
        created_at=None,
        updated_at=None,
        created_by="u",
        updated_by="u",
    )

    response = converter_execution_to_response(execution)

    assert response.id == "e1"
    assert response.task_id == "t1"
    assert response.status == "RUNNING"

