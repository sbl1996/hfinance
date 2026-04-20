"""负债 API"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import LiabilityCreate, LiabilityOut, LiabilityUpdate, LiabilityListOut
from app.repositories import liability_repo

router = APIRouter()


@router.get("", response_model=LiabilityListOut)
async def list_liabilities():
    """获取所有负债列表及总额"""
    items = await liability_repo.get_all()
    total = await liability_repo.get_total_amount()
    return LiabilityListOut(
        items=[LiabilityOut(**item) for item in items],
        total_amount_cny=total,
    )


@router.post("", response_model=LiabilityOut)
async def create_liability(data: LiabilityCreate):
    """新增负债"""
    item = await liability_repo.create(data)
    return LiabilityOut(**item)


@router.put("/{item_id}", response_model=LiabilityOut)
async def update_liability(item_id: int, data: LiabilityUpdate):
    """修改负债"""
    item = await liability_repo.update(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="负债不存在")
    return LiabilityOut(**item)


@router.delete("/{item_id}")
async def delete_liability(item_id: int):
    """删除负债"""
    success = await liability_repo.delete(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="负债不存在")
    return {"detail": "删除成功"}
