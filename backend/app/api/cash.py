"""现金账户 API"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import verify_token
from app.models.schemas import CashAccountCreate, CashAccountOut, CashAccountUpdate, CashAccountListOut
from app.repositories import cash_repo

router = APIRouter()


def _auth(authorization: str = ""):
    """简易认证依赖"""
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else ""
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="未授权")


@router.get("", response_model=CashAccountListOut)
async def list_cash_accounts():
    """获取所有现金账户列表及总额"""
    items = await cash_repo.get_all()
    total = await cash_repo.get_total_balance()
    return CashAccountListOut(
        items=[CashAccountOut(**item) for item in items],
        total_balance_cny=total,
    )


@router.post("", response_model=CashAccountOut)
async def create_cash_account(data: CashAccountCreate):
    """新增现金账户"""
    item = await cash_repo.create(data)
    return CashAccountOut(**item)


@router.put("/{item_id}", response_model=CashAccountOut)
async def update_cash_account(item_id: int, data: CashAccountUpdate):
    """修改现金账户"""
    item = await cash_repo.update(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="现金账户不存在")
    return CashAccountOut(**item)


@router.delete("/{item_id}")
async def delete_cash_account(item_id: int):
    """删除现金账户"""
    success = await cash_repo.delete(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="现金账户不存在")
    return {"detail": "删除成功"}
