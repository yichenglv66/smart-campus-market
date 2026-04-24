from fastapi import APIRouter, Depends, Request
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
        context={"items": items},
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
