"""自动拉取任务 API"""

import sqlite3

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    FetchTaskCreate,
    FetchTaskListOut,
    FetchTaskMarketType,
    FetchTaskOut,
    FetchTaskRunsOut,
    FetchTaskRunSummary,
    FetchTaskToggleRequest,
    FetchTaskUpdate,
    FetchTaskRunStatus,
)
from app.repositories import fetch_task_repo, fetch_task_run_repo
from app.services.fetch_task_service import ActiveFetchTaskRunError, enqueue_manual_run

router = APIRouter()


def _build_run_summary(row: dict) -> FetchTaskRunSummary:
    return FetchTaskRunSummary(
        id=row["id"],
        scheduled_for=row["scheduled_for"],
        status=FetchTaskRunStatus(row["status"]),
        started_at=row.get("started_at"),
        finished_at=row.get("finished_at"),
        error_message=row.get("error_message"),
        price_date=row.get("price_date"),
        price_value=row.get("price_value"),
    )


def _build_task_out(row: dict) -> FetchTaskOut:
    latest_run = None
    if row.get("latest_run_id"):
        latest_run = _build_run_summary(
            {
                "id": row["latest_run_id"],
                "scheduled_for": row["latest_run_scheduled_for"],
                "status": row["latest_run_status"],
                "started_at": row.get("latest_run_started_at"),
                "finished_at": row.get("latest_run_finished_at"),
                "error_message": row.get("latest_run_error_message"),
                "price_date": row.get("latest_run_price_date"),
                "price_value": row.get("latest_run_price_value"),
            }
        )
    return FetchTaskOut(
        id=row["id"],
        code=row["code"],
        name=row["name"],
        market=FetchTaskMarketType(row["market"]),
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


@router.post("/{task_id}/run-now", response_model=FetchTaskRunSummary)
async def run_fetch_task_now(task_id: int):
    try:
        run = await enqueue_manual_run(task_id)
    except ActiveFetchTaskRunError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="任务已在排队或执行中，请勿重复提交") from exc
    if not run:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _build_run_summary(run)


@router.get("/{task_id}/runs", response_model=FetchTaskRunsOut)
async def list_fetch_task_runs(task_id: int, limit: int = Query(default=20, ge=1, le=100)):
    task = await fetch_task_repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    rows = await fetch_task_run_repo.list_runs_for_task(task_id, limit=limit)
    return FetchTaskRunsOut(
        items=[_build_run_summary(row) for row in rows]
    )
