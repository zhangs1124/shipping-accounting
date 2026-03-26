from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=func.now())

    employees = relationship("Employee", back_populates="department")


# 角色與權限的多對多關聯表
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True)
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False) # e.g., Admin, Accounting, Operator
    created_at = Column(DateTime, default=func.now())

    employees = relationship("Employee", back_populates="role")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False) # e.g., 'invoice:create', 'voyage:view'
    name = Column(String, nullable=False)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    email = Column(String)
    department_id = Column(Integer, ForeignKey("departments.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))
    is_active = Column(Integer, default=1) # 1: 啟用, 0: 停用
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    department = relationship("Department", back_populates="employees")
    role = relationship("Role", back_populates="employees")


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
    
    # 提醒中心擴充
    operator_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    ship = relationship("Ship", back_populates="voyages")
    operator = relationship("Employee")
    invoices = relationship("Invoice", back_populates="voyage")
    task_logs = relationship("VoyageTaskLog", back_populates="voyage")


class TaskCategory(Base):
    __tablename__ = "task_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)    # 任務名稱
    task_group = Column(String)             # 分組
    default_fee = Column(Numeric(18, 2), default=0) # 預設規費
    display_order = Column(Integer, default=0)
    is_active = Column(Integer, default=1)   # 1: 啟用, 0: 停用
    
    # 提醒中心擴充
    base_milestone = Column(String, nullable=True) # e.g., 'ETA', 'ETD'
    expected_offset_hours = Column(Integer, default=0) # 偏移小時 (正數代表之後，負數代表之前)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    task_logs = relationship("VoyageTaskLog", back_populates="task_category")


class VoyageTaskLog(Base):
    __tablename__ = "voyage_task_logs"

    id = Column(Integer, primary_key=True, index=True)
    voyage_id = Column(Integer, ForeignKey("voyages.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("task_categories.id"), nullable=False)
    recorded_time = Column(DateTime) # 實際動作時間
    recorded_by = Column(String) # 執行的使用者
    remarks = Column(String)     # 備註
    created_at = Column(DateTime, default=func.now())

    voyage = relationship("Voyage", back_populates="task_logs")
    task_category = relationship("TaskCategory", back_populates="task_logs")


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
    responsible = Column(String)
    invoice_prefix = Column(String, default="A", nullable=False)
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
    responsible = Column(String)  # 發票/帳務負責人（從客戶帶入）
    total_amount = Column(Numeric(18, 2), default=0)
    is_reminded = Column(Integer, default=0)  # 0:未提醒, 1:已提醒 (SQLite 不支援 Boolean 預設值時常用 Integer)
    last_reminded_at = Column(DateTime, nullable=True)
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


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(String)
    remind_type = Column(String, default="TASK_OVERDUE") # TASK_OVERDUE, TASK_UPCOMING, SYSTEM
    source_table = Column(String) # e.g., 'voyage_task_logs'
    source_id = Column(Integer)
    target_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    is_closed = Column(Integer, default=0) # 0: 處理中, 1: 已完成
    deadline = Column(DateTime)
    
    # 手動提醒擴充
    frequency = Column(String, default="ONCE") # 'ONCE', 'DAILY'
    last_reminded_at = Column(DateTime, nullable=True)
    next_remind_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    target_employee = relationship("Employee")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True) # 執行操作的員工/管理員 ID，系統則為 Null
    action = Column(String, nullable=False) # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, SEND_EMAIL 等
    table_name = Column(String, nullable=True) # 受影響的資料表名
    target_id = Column(String, nullable=True) # 被異動物件的主鍵
    old_value = Column(String, nullable=True) # 發生變更前的資料 (JSON format)
    new_value = Column(String, nullable=True) # 發生變更後的資料 (JSON format)
    timestamp = Column(DateTime, default=func.now())
    ip_address = Column(String, nullable=True) # 來源 IP

