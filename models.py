from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base


class Ship(Base):
    __tablename__ = "ships"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    flag = Column(String)
    ship_type = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    voyages = relationship("Voyage", back_populates="ship")


class Voyage(Base):
    __tablename__ = "voyages"

    id = Column(Integer, primary_key=True, index=True)
    voyage_no = Column(String, unique=True, nullable=False, index=True)
    ship_id = Column(Integer, ForeignKey("ships.id"), nullable=False)
    port_of_loading = Column(String)
    port_of_discharge = Column(String)
    etd = Column(Date)
    eta = Column(Date)
    status = Column(String, default="計畫中")  # 計畫中/進行中/已完成
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    ship = relationship("Ship", back_populates="voyages")
    invoices = relationship("Invoice", back_populates="voyage")


class ChargeItem(Base):
    __tablename__ = "charge_items"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    currency = Column(String, nullable=False, default="TWD")
    default_unit_price = Column(Numeric(18, 2), default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    invoice_lines = relationship("InvoiceLine", back_populates="charge_item")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    contact = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String, unique=True, nullable=False, index=True)
    voyage_id = Column(Integer, ForeignKey("voyages.id"), nullable=False)
    customer_name = Column(String, nullable=False)
    invoice_date = Column(Date, nullable=False)
    status = Column(String, default="草稿")  # 草稿/已開立/已收款
    total_amount = Column(Numeric(18, 2), default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    voyage = relationship("Voyage", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    charge_item_id = Column(Integer, ForeignKey("charge_items.id"), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False, default=1)
    unit_price = Column(Numeric(18, 2), nullable=False, default=0)
    currency = Column(String, nullable=False, default="TWD")
    subtotal = Column(Numeric(18, 2), default=0)
    remark = Column(String, default="")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    invoice = relationship("Invoice", back_populates="lines")
    charge_item = relationship("ChargeItem", back_populates="invoice_lines")
