import pytest

from app.module.ratio.schema.ratio_task import CreateRatioTaskRequest, FilterCondition


def test_filter_condition_rejects_bad_date_range_order() -> None:
    with pytest.raises(ValueError):
        FilterCondition(dateRange=["2025-01-02", "2025-01-01"])


def test_create_ratio_task_request_validates_numeric_totals() -> None:
    with pytest.raises(ValueError):
        CreateRatioTaskRequest(name="r1", totals="abc", config=[])


def test_create_ratio_task_request_accepts_valid_numeric_values() -> None:
    request = CreateRatioTaskRequest(
        name="ratio-task",
        totals="10",
        config=[
            {
                "datasetId": "ds-1",
                "counts": "5",
                "filterConditions": {
                    "dateRange": ["2025-01-01", "2025-01-31"],
                    "label": {"label": "intent", "value": "A"},
                },
            }
        ],
    )

    assert request.totals == "10"
    assert request.config[0].counts == "5"


def test_filter_condition_rejects_invalid_date_range_length() -> None:
    with pytest.raises(ValueError):
        FilterCondition(dateRange=["2025-01-01"])


def test_create_ratio_task_request_rejects_non_numeric_counts() -> None:
    with pytest.raises(ValueError):
        CreateRatioTaskRequest(
            name="ratio-task",
            totals="10",
            config=[
                {
                    "datasetId": "ds-1",
                    "counts": "x",
                    "filterConditions": {"dateRange": ["2025-01-01", "2025-01-02"]},
                }
            ],
        )


def test_filter_condition_accepts_none_date_range() -> None:
    cond = FilterCondition(dateRange=None)
    assert cond.date_range is None


def test_filter_condition_rejects_invalid_date_string() -> None:
    with pytest.raises(ValueError):
        FilterCondition(dateRange=["bad-date", "2025-01-01"])


def test_create_ratio_task_request_accepts_zero_totals() -> None:
    req = CreateRatioTaskRequest(name="r0", totals="0", config=[])
    assert req.totals == "0"


def test_create_ratio_task_request_rejects_negative_totals() -> None:
    with pytest.raises(ValueError):
        CreateRatioTaskRequest(name="r1", totals="-1", config=[])


def test_create_ratio_task_request_alias_mapping_for_dataset_id() -> None:
    req = CreateRatioTaskRequest(
        name="ratio-task",
        totals="2",
        config=[
            {
                "datasetId": "ds-alias",
                "counts": "1",
                "filterConditions": {"dateRange": ["2025-01-01", "2025-01-02"]},
            }
        ],
    )
    assert req.config[0].dataset_id == "ds-alias"
