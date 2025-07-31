from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, DateTime, Numeric
from datetime import datetime
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # NOTE: This should store a HASHED password, not plain text.
    role = Column(String, default='consumer')

    # Relationships
    cart_items = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, index=True)
    image_name = Column(String)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    price = Column(Numeric(10, 2), nullable=False)  # Use Numeric for prices
    quantity = Column(Integer, nullable=False)
    category = Column(String)

    # Relationships (not strictly needed here but good for completeness)
    order_line_items = relationship("OrderItem", back_populates="item")
    carts_containing_item = relationship("Cart", back_populates="item")


class Cart(Base):
    __tablename__ = 'cart'
    __table_args__ = (UniqueConstraint('user_id', 'item_id', name='_user_item_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, default=1)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="cart_items")
    item = relationship("Item", back_populates="carts_containing_item")


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    customer_phone = Column(String)
    customer_address = Column(String)
    status = Column(String, default="pending")
    order_date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Numeric(10, 2))  # Use Numeric for total amount

    # Foreign Keys
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = 'order_items'
    __table_args__ = (UniqueConstraint('order_id', 'item_id', name='_order_item_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer)
    price = Column(Numeric(10, 2))  # Price of the item at the time of order

    # Foreign Keys
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    item = relationship("Item", back_populates="order_line_items")