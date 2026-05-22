"""自动拉取任务 API"""

import sqlite3

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    FetchTaskCreate,
    FetchTaskListOut,
    FetchTaskOut,
    FetchTaskRunsOut,
    FetchTaskRunSummary,
    FetchTaskToggleRequest,
    FetchTaskUpdate,
    FetchTaskRunStatus,
    MarketType,
)
from app.repositories import fetch_task_repo, fetch_task_run_repo

router = APIRouter()


def _build_task_out(row: dict) -> FetchTaskOut:
    latest_run = None
    if row.get("latest_run_id"):
        latest_run = FetchTaskRunSummary(
            id=row["latest_run_id"],
            scheduled_for=row["latest_run_scheduled_for"],
            status=FetchTaskRunStatus(row["latest_run_status"]),
            started_at=row.get("latest_run_started_at"),
            finished_at=row.get("latest_run_finished_at"),
            error_message=row.get("latest_run_error_message"),
            price_date=row.get("latest_run_price_date"),
            price_value=row.get("latest_run_price_value"),
        )
    return FetchTaskOut(
        id=row["id"],
        code=row["code"],
        name=row["name"],
        market=MarketType(row["market"]),
        enabled=bool(row["enabled"]),
        run_time=row["run_time"],
        weekdays=fetch_task_repo.mask_to_weekdays(row["weekdays_mask"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        latest_run=latest_run,
    )


@router.get("", response_model=FetchTaskListOut)
async def list_fetch_tasks():
    rows = await fetch_task_repo.list_tasks()
    return FetchTaskListOut(items=[_build_task_out(row) for row in rows])


@router.post("", response_model=FetchTaskOut)
async def create_fetch_task(data: FetchTaskCreate):
    try:
        task = await fetch_task_repo.create_task(data)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="相同标的、时间和频率的任务已存在") from exc
    if not task:
        raise HTTPException(status_code=500, detail="创建任务失败")
    return _build_task_out({**task})


@router.get("/{task_id}", response_model=FetchTaskOut)
async def get_fetch_task(task_id: int):
    rows = await fetch_task_repo.list_tasks()
    for row in rows:
        if row["id"] == task_id:
            return _build_task_out(row)
    raise HTTPException(status_code=404, detail="任务不存在")


@router.put("/{task_id}", response_model=FetchTaskOut)
async def update_fetch_task(task_id: int, data: FetchTaskUpdate):
    try:
        task = await fetch_task_repo.update_task(task_id, data)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="更新后会与现有任务重复") from exc
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    rows = await fetch_task_repo.list_tasks()
    for row in rows:
        if row["id"] == task_id:
            return _build_task_out(row)
    return _build_task_out(task)


@router.delete("/{task_id}")
async def delete_fetch_task(task_id: int):
    success = await fetch_task_repo.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"detail": "删除成功"}


@router.post("/{task_id}/toggle", response_model=FetchTaskOut)
async def toggle_fetch_task(task_id: int, data: FetchTaskToggleRequest):
    task = await fetch_task_repo.update_task(task_id, FetchTaskUpdate(enabled=data.enabled))
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    rows = await fetch_task_repo.list_tasks()
    for row in rows:
        if row["id"] == task_id:
            return _build_task_out(row)
    return _build_task_out(task)


@router.get("/{task_id}/runs", response_model=FetchTaskRunsOut)
async def list_fetch_task_runs(task_id: int, limit: int = Query(default=20, ge=1, le=100)):
    task = await fetch_task_repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    rows = await fetch_task_run_repo.list_runs_for_task(task_id, limit=limit)
    return FetchTaskRunsOut(
        items=[
            FetchTaskRunSummary(
                id=row["id"],
                scheduled_for=row["scheduled_for"],
                status=FetchTaskRunStatus(row["status"]),
                started_at=row["started_at"],
                finished_at=row["finished_at"],
                error_message=row["error_message"],
                price_date=row["price_date"],
                price_value=row["price_value"],
            )
            for row in rows
        ]
    )
