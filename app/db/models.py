from datetime import datetime

from sqlalchemy import DateTime, DECIMAL, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    items: Mapped[list["Item"]] = relationship(back_populates="seller")
    orders: Mapped[list["Order"]] = relationship(back_populates="buyer")


class Item(Base):
    __tablename__ = "item"

    item_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    seller: Mapped[User] = relationship(back_populates="items")
    order: Mapped["Order | None"] = relationship(back_populates="item", uselist=False)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("item_id", name="uk_orders_item_id"),)

    order_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.item_id"), nullable=False, unique=True)
    deal_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    buyer: Mapped[User] = relationship(back_populates="orders")
    item: Mapped[Item] = relationship(back_populates="order")
