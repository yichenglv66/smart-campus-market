from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.db.models import Item, Order, User
from app.db.session import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    user_count = db.query(func.count(User.user_id)).scalar() or 0
    item_count = db.query(func.count(Item.item_id)).scalar() or 0
    order_count = db.query(func.count(Order.order_id)).scalar() or 0
    sold_count = db.query(func.count(Item.item_id)).filter(Item.status == 1).scalar() or 0

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user_count": user_count,
            "item_count": item_count,
            "order_count": order_count,
            "sold_count": sold_count,
        },
    )


@router.get("/users")
def user_list(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.user_id.asc()).all()
    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context={"users": users},
    )


@router.get("/items")
def item_list(request: Request, db: Session = Depends(get_db)):
    items = (
        db.query(Item)
        .options(joinedload(Item.seller))
        .order_by(Item.item_id.asc())
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="items.html",
        context={
            "items": items,
            "users": db.query(User).order_by(User.user_id.asc()).all(),
            "message": request.query_params.get("message", ""),
            "message_type": request.query_params.get("message_type", ""),
        },
    )


@router.post("/items")
def create_item(
    seller_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    price: str = Form(...),
    db: Session = Depends(get_db),
):
    if not title.strip() or not description.strip():
        return RedirectResponse(
            url="/items?message=标题和描述不能为空&message_type=error",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    if not db.get(User, seller_id):
        return RedirectResponse(
            url="/items?message=卖家不存在&message_type=error",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    try:
        price_value = Decimal(price)
    except (InvalidOperation, ValueError):
        return RedirectResponse(
            url="/items?message=价格格式不正确&message_type=error",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    if price_value < 0:
        return RedirectResponse(
            url="/items?message=价格不能为负数&message_type=error",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    item = Item(
        seller_id=seller_id,
        title=title.strip(),
        description=description.strip(),
        price=price_value,
        status=0,
    )
    db.add(item)
    db.commit()
    return RedirectResponse(
        url="/items?message=商品新增成功&message_type=success",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/items/{item_id}/price")
def update_item_price(
    item_id: int,
    price: str = Form(...),
    db: Session = Depends(get_db),
):
    item = db.get(Item, item_id)
    if not item:
        return RedirectResponse(
            url="/items?message=商品不存在&message_type=error",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    try:
        price_value = Decimal(price)
    except (InvalidOperation, ValueError):
        return RedirectResponse(
            url="/items?message=价格格式不正确&message_type=error",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    if price_value < 0:
        return RedirectResponse(
            url="/items?message=价格不能为负数&message_type=error",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    item.price = price_value
    db.commit()
    return RedirectResponse(
        url="/items?message=商品价格修改成功&message_type=success",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/items/{item_id}/delete")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        return RedirectResponse(
            url="/items?message=商品不存在&message_type=error",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    if item.status == 1:
        return RedirectResponse(
            url="/items?message=删除失败：已售出商品不能删除&message_type=error",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    db.delete(item)
    db.commit()
    return RedirectResponse(
        url="/items?message=商品删除成功&message_type=success",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/orders")
def order_list(request: Request, db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .options(joinedload(Order.buyer), joinedload(Order.item).joinedload(Item.seller))
        .order_by(Order.order_id.asc())
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={"orders": orders},
    )
