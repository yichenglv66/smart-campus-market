from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy import case, func, text
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


@router.post("/items/{item_id}/purchase")
def purchase_item(
    item_id: int,
    buyer_id: int = Form(...),
    db: Session = Depends(get_db),
):
    try:
        with db.begin():
            item = (
                db.query(Item)
                .filter(Item.item_id == item_id)
                .with_for_update()
                .first()
            )
            if not item:
                return RedirectResponse(
                    url="/items?message=购买失败：商品不存在&message_type=error",
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            if item.status == 1:
                return RedirectResponse(
                    url="/items?message=购买失败：商品已售出&message_type=error",
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            if item.seller_id == buyer_id:
                return RedirectResponse(
                    url="/items?message=购买失败：不能购买自己发布的商品&message_type=error",
                    status_code=status.HTTP_303_SEE_OTHER,
                )
            if not db.get(User, buyer_id):
                return RedirectResponse(
                    url="/items?message=购买失败：买家不存在&message_type=error",
                    status_code=status.HTTP_303_SEE_OTHER,
                )

            order = Order(
                buyer_id=buyer_id,
                item_id=item.item_id,
                deal_price=item.price,
            )
            db.add(order)
            item.status = 1
    except IntegrityError:
        db.rollback()
        return RedirectResponse(
            url="/items?message=购买失败：商品已被其他人抢先购买&message_type=error",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception:
        db.rollback()
        return RedirectResponse(
            url="/items?message=购买失败：事务执行异常，已回滚&message_type=error",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return RedirectResponse(
        url="/items?message=购买成功，已生成订单&message_type=success",
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


@router.get("/reports")
def reports_page(request: Request, db: Session = Depends(get_db)):
    # 类别统一：当前表结构无 category 字段，使用标题/描述关键字归类。
    category_case = case(
        (Item.title.like("%台灯%"), "生活用品"),
        (Item.title.like("%键盘%"), "生活用品"),
        (Item.title.like("%充电宝%"), "生活用品"),
        else_="其他",
    )

    # 一、基本查询
    unsold_items = db.query(Item).filter(Item.status == 0).order_by(Item.item_id.asc()).all()
    price_gt_30_items = db.query(Item).filter(Item.price > 30).order_by(Item.item_id.asc()).all()
    life_items = (
        db.query(Item)
        .filter(
            Item.title.like("%台灯%")
            | Item.title.like("%键盘%")
            | Item.title.like("%充电宝%")
            | Item.description.like("%宿舍%")
        )
        .order_by(Item.item_id.asc())
        .all()
    )
    u001_items = db.query(Item).filter(Item.seller_id == 1).order_by(Item.item_id.asc()).all()

    # 二、连接查询
    sold_with_buyer = (
        db.query(Item.title, User.username.label("buyer_name"))
        .join(Order, Order.item_id == Item.item_id)
        .join(User, User.user_id == Order.buyer_id)
        .filter(Item.status == 1)
        .order_by(Item.item_id.asc())
        .all()
    )
    order_item_buyer_date = (
        db.query(Order.order_id, Item.title, User.username.label("buyer_name"), Order.created_at)
        .join(Item, Item.item_id == Order.item_id)
        .join(User, User.user_id == Order.buyer_id)
        .order_by(Order.order_id.asc())
        .all()
    )
    u001_sold_status = (
        db.query(Item.item_id, Item.title, Order.order_id.is_not(None).label("is_purchased"))
        .outerjoin(Order, Order.item_id == Item.item_id)
        .filter(Item.seller_id == 1)
        .order_by(Item.item_id.asc())
        .all()
    )

    # 三、聚合与分组
    total_item_count = db.query(func.count(Item.item_id)).scalar() or 0
    category_counts = (
        db.query(category_case.label("category_name"), func.count(Item.item_id).label("count"))
        .group_by(category_case)
        .order_by(func.count(Item.item_id).desc())
        .all()
    )
    avg_price = db.query(func.avg(Item.price)).scalar()
    top_seller = (
        db.query(User.user_id, User.username, func.count(Item.item_id).label("item_count"))
        .join(Item, Item.seller_id == User.user_id)
        .group_by(User.user_id, User.username)
        .order_by(func.count(Item.item_id).desc(), User.user_id.asc())
        .first()
    )

    # 四、视图（原生 SQL）
    db.execute(
        text(
            """
            CREATE OR REPLACE VIEW v_sold_item_buyer AS
            SELECT i.title AS item_title, o.buyer_id
            FROM item i
            JOIN orders o ON o.item_id = i.item_id
            WHERE i.status = 1
            """
        )
    )
    db.execute(
        text(
            """
            CREATE OR REPLACE VIEW v_unsold_item AS
            SELECT item_id, title, seller_id, price, created_at
            FROM item
            WHERE status = 0
            """
        )
    )
    sold_view_rows = db.execute(text("SELECT item_title, buyer_id FROM v_sold_item_buyer ORDER BY item_title")).all()
    unsold_view_rows = db.execute(
        text("SELECT item_id, title, seller_id, price, created_at FROM v_unsold_item ORDER BY item_id")
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="reports.html",
        context={
            "unsold_items": unsold_items,
            "price_gt_30_items": price_gt_30_items,
            "life_items": life_items,
            "u001_items": u001_items,
            "sold_with_buyer": sold_with_buyer,
            "order_item_buyer_date": order_item_buyer_date,
            "u001_sold_status": u001_sold_status,
            "total_item_count": total_item_count,
            "category_counts": category_counts,
            "avg_price": avg_price,
            "top_seller": top_seller,
            "sold_view_rows": sold_view_rows,
            "unsold_view_rows": unsold_view_rows,
        },
    )
