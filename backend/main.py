"""
社保局店工资管理系统 - Web 版后端
FastAPI + SQLAlchemy + MySQL
全局参数（商铺/部门/职务/提成规则）统一由管理员维护。
"""
import os, re
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import (create_engine, Column, Integer, String, Float, Text,
                        ForeignKey, UniqueConstraint, func)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ---------- 数据库连接 ----------
DB_USER = os.environ.get("SALARY_DB_USER", "root")
DB_PASS = os.environ.get("SALARY_DB_PASS", "123456")
DB_HOST = os.environ.get("SALARY_DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("SALARY_DB_PORT", "3306")
DB_NAME = os.environ.get("SALARY_DB_NAME", "salary_system")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- 业务工具 ----------
def rnd(v):
    """四舍五入取整（规避银行家舍入）"""
    return int(Decimal(str(v)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def parse_id_card(idc):
    """解析身份证：返回 (性别, 出生日期, 年龄)，非法返回 (None,None,None)"""
    idc = (idc or "").strip()
    if len(idc) == 18 and re.match(r"^\d{17}[\dXx]$", idc):
        g = "男" if int(idc[16]) % 2 else "女"
        b = f"{idc[6:10]}-{idc[10:12]}-{idc[12:14]}"
    elif len(idc) == 15 and re.match(r"^\d{15}$", idc):
        g = "男" if int(idc[14]) % 2 else "女"
        b = f"19{idc[6:8]}-{idc[8:10]}-{idc[10:12]}"
    else:
        return None, None, None
    try:
        bd = datetime.strptime(b, "%Y-%m-%d").date()
    except:
        return None, None, None
    today = date.today()
    age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    return g, b, age


def month_days(month):
    """当月自然天数（yyyymm 或 yyyy-mm）"""
    m = month.replace("-", "")
    y, mo = int(m[:4]), int(m[4:6])
    if mo == 2:
        d = 29 if (y % 4 == 0 and y % 100 != 0) or y % 400 == 0 else 28
    elif mo in (4, 6, 9, 11):
        d = 30
    else:
        d = 31
    return d


def calc_salary_fields(data):
    """工资自动计算（严格按用户锁定口径）"""
    f = lambda k: float(data.get(k) or 0)
    # 计薪基数 = 基本 + 业绩 + 职级补助 + 节假日 + 绩效 + 销售提成
    base = f("base_salary") + f("performance_salary") + f("position_allowance") + \
           f("holiday_salary") + f("bonus_salary") + f("sales_commission")
    days = month_days(data.get("month", datetime.now().strftime("%Y-%m")))
    day_wage = base / days if days else 0
    hour_wage = day_wage / 10
    overtime_pay = rnd(f("overtime_hours") * hour_wage * 2)
    leave_deduction = rnd(f("leave_days") * day_wage)
    outing_deduction = rnd(f("outing_hours") * hour_wage)
    absent_deduction = rnd(f("absent_days") * day_wage * 1.5)
    subtotal1 = rnd(f("base_salary") + f("ss_return") + f("performance_salary") +
                    f("position_allowance") + f("holiday_salary"))
    subtotal2 = rnd(f("bonus_salary") + f("sales_commission") + overtime_pay +
                    f("other_allowance") + f("full_attendance") + f("award"))
    total = subtotal1 + subtotal2
    deduction = leave_deduction + absent_deduction + outing_deduction + \
                f("discipline_deduction") + f("quality_deduction") + f("ss_paid")
    actual = total - deduction - f("tax")
    return {"overtime_pay": overtime_pay, "leave_deduction": leave_deduction,
            "outing_deduction": outing_deduction, "absent_deduction": absent_deduction,
            "subtotal1": subtotal1, "subtotal2": subtotal2, "total_salary": total,
            "total_deduction": deduction, "actual_salary": actual}


# ---------- 模型 ----------
class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(String(30), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), default="operator")  # super_admin / operator
    created_at = Column(String(30), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    id_card = Column(String(20), default="")
    gender = Column(String(4), default="")
    birth_date = Column(String(10), default="")
    age = Column(Integer, default=0)
    status = Column(String(10), default="在职")
    department = Column(String(50), default="")
    position = Column(String(50), default="")
    phone = Column(String(30), default="")
    address = Column(String(200), default="")
    bank_card = Column(String(50), default="")
    bank_name = Column(String(100), default="")
    is_bocom = Column(String(4), default="否")
    payment_method = Column(String(20), default="银行卡")
    social_security = Column(String(20), default="有社保")
    contract_start = Column(String(10), default="")
    contract_end = Column(String(10), default="")
    created_at = Column(String(30), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at = Column(String(30), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class SalaryDetail(Base):
    __tablename__ = "salary_details"
    __table_args__ = (UniqueConstraint("employee_id", "month"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    month = Column(String(7), nullable=False)
    attendance_days = Column(Float, default=0)
    base_salary = Column(Float, default=0)
    ss_return = Column(Float, default=0)
    performance_salary = Column(Float, default=0)
    position_allowance = Column(Float, default=0)
    holiday_salary = Column(Float, default=0)
    subtotal1 = Column(Float, default=0)
    bonus_salary = Column(Float, default=0)
    sales_commission = Column(Float, default=0)
    overtime_hours = Column(Float, default=0)
    overtime_pay = Column(Float, default=0)
    other_allowance = Column(Float, default=0)
    full_attendance = Column(Float, default=0)
    award = Column(Float, default=0)
    subtotal2 = Column(Float, default=0)
    total_salary = Column(Float, default=0)
    leave_days = Column(Float, default=0)
    leave_deduction = Column(Float, default=0)
    absent_days = Column(Float, default=0)
    absent_deduction = Column(Float, default=0)
    outing_hours = Column(Float, default=0)
    outing_deduction = Column(Float, default=0)
    discipline_deduction = Column(Float, default=0)
    quality_deduction = Column(Float, default=0)
    ss_paid = Column(Float, default=0)
    total_deduction = Column(Float, default=0)
    tax = Column(Float, default=0)
    actual_salary = Column(Float, default=0)
    notes = Column(Text, default="")
    created_at = Column(String(30), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at = Column(String(30), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class SalaryPayment(Base):
    __tablename__ = "salary_payments"
    __table_args__ = (UniqueConstraint("employee_id", "month"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    month = Column(String(7), nullable=False)
    should_pay = Column(Float, default=0)
    actual_pay = Column(Float, default=0)
    bocom_pay = Column(Float, default=0)
    payment_method = Column(String(20), default="")


class CommissionRule(Base):
    __tablename__ = "commission_rules"
    __table_args__ = (UniqueConstraint("position"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    position = Column(String(50), nullable=False)
    perf_rate = Column(Float, default=0)
    sales_rate = Column(Float, default=0)
    description = Column(String(200), default="")


class GlobalPosition(Base):
    """全局职务（含职务工资/职级补助），管理员统一维护"""
    __tablename__ = "global_positions"
    __table_args__ = (UniqueConstraint("name"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    allowance = Column(Float, default=0)
    description = Column(String(200), default="")


class GlobalDepartment(Base):
    """全局部门，管理员统一维护"""
    __tablename__ = "global_departments"
    __table_args__ = (UniqueConstraint("name"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, nullable=True)
    username = Column(String(50), default="")
    action = Column(String(50), default="")
    detail = Column(Text, default="")
    created_at = Column(String(30), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


# ---------- 鉴权 ----------
def get_current_user(x_user_id: int, db=Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if not u:
        raise HTTPException(401, "未登录")
    return u


def log_action(db, store_id, username, action, detail=""):
    db.add(AuditLog(store_id=store_id, username=username, action=action, detail=detail))
    db.commit()


app = FastAPI(title="社保局店工资管理系统")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ========== 认证 ==========
class LoginReq(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(req: LoginReq, db: SessionLocal = Depends(get_db)):
    u = db.query(User).filter(User.username == req.username, User.password == req.password).first()
    if not u:
        raise HTTPException(400, "用户名或密码错误")
    return {"id": u.id, "username": u.username, "role": u.role,
            "store_id": u.store_id,
            "store_name": db.query(Store.name).filter(Store.id == u.store_id).scalar() if u.store_id else None}

@app.post("/api/logout")
def logout(x_user_id: int, db: SessionLocal = Depends(get_db)):
    return {"ok": True}


# ========== 商铺 ==========
@app.get("/api/stores")
def list_stores(x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    return [{"id": s.id, "name": s.name,
             "employees": db.query(Employee).filter(Employee.store_id == s.id).count(),
             "active": db.query(Employee).filter(Employee.store_id == s.id, Employee.status == "在职").count(),
             "salary_records": db.query(SalaryDetail).filter(SalaryDetail.store_id == s.id).count()}
            for s in db.query(Store).order_by(Store.id)]

class StoreReq(BaseModel):
    name: str

@app.post("/api/stores")
def add_store(req: StoreReq, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    if db.query(Store).filter(Store.name == req.name).first():
        raise HTTPException(400, "商铺已存在")
    s = Store(name=req.name)
    db.add(s); db.commit(); db.refresh(s)
    log_action(db, None, u.username, "新增商铺", req.name)
    return {"id": s.id, "name": s.name}

@app.delete("/api/stores/{sid}")
def del_store(sid: int, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    s = db.query(Store).get(sid)
    if not s:
        raise HTTPException(404, "商铺不存在")
    db.delete(s); db.commit()
    log_action(db, None, u.username, "删除商铺", s.name)
    return {"ok": True}


# ========== 用户(操作员) ==========
class UserReq(BaseModel):
    store_id: int
    username: str
    password: str

@app.get("/api/users")
def list_users(x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    return [{"id": x.id, "username": x.username, "role": x.role, "store_id": x.store_id,
             "store_name": db.query(Store.name).filter(Store.id == x.store_id).scalar() if x.store_id else None}
            for x in db.query(User).all()]

@app.post("/api/users")
def add_user(req: UserReq, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "用户名已存在")
    x = User(store_id=req.store_id, username=req.username, password=req.password, role="operator")
    db.add(x); db.commit()
    log_action(db, None, u.username, "新增操作员", req.username)
    return {"id": x.id, "username": x.username}

@app.delete("/api/users/{uid}")
def del_user(uid: int, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    x = db.query(User).get(uid)
    if not x:
        raise HTTPException(404, "用户不存在")
    db.delete(x); db.commit()
    log_action(db, None, u.username, "删除操作员", x.username)
    return {"ok": True}


# ========== 全局参数（管理员统一维护）==========
class DepartmentReq(BaseModel):
    name: str

@app.get("/api/global/departments")
def list_departments(x_user_id: int, db: SessionLocal = Depends(get_db)):
    return [{"id": d.id, "name": d.name} for d in db.query(GlobalDepartment).order_by(GlobalDepartment.name)]

@app.post("/api/global/departments")
def add_department(req: DepartmentReq, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    if not req.name.strip():
        raise HTTPException(400, "名称不能为空")
    if db.query(GlobalDepartment).filter(GlobalDepartment.name == req.name).first():
        raise HTTPException(400, "部门已存在")
    d = GlobalDepartment(name=req.name)
    db.add(d); db.commit(); db.refresh(d)
    log_action(db, None, u.username, "新增全局部门", req.name)
    return {"id": d.id, "name": d.name}

@app.delete("/api/global/departments/{did}")
def del_department(did: int, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    d = db.query(GlobalDepartment).get(did)
    if not d:
        raise HTTPException(404, "部门不存在")
    db.delete(d); db.commit()
    log_action(db, None, u.username, "删除全局部门", d.name)
    return {"ok": True}


class PositionReq(BaseModel):
    name: str
    allowance: float = 0

@app.get("/api/global/positions")
def list_positions(x_user_id: int, db: SessionLocal = Depends(get_db)):
    return [{"id": p.id, "name": p.name, "allowance": p.allowance} for p in db.query(GlobalPosition).order_by(GlobalPosition.name)]

@app.post("/api/global/positions")
def add_position(req: PositionReq, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    if not req.name.strip():
        raise HTTPException(400, "名称不能为空")
    if db.query(GlobalPosition).filter(GlobalPosition.name == req.name).first():
        raise HTTPException(400, "职务已存在")
    p = GlobalPosition(name=req.name, allowance=req.allowance)
    db.add(p); db.commit(); db.refresh(p)
    log_action(db, None, u.username, "新增全局职务", f"{req.name}(职级补助{req.allowance:g})")
    return {"id": p.id, "name": p.name, "allowance": p.allowance}

@app.put("/api/global/positions/{pid}")
def update_position(pid: int, req: PositionReq, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    p = db.query(GlobalPosition).get(pid)
    if not p:
        raise HTTPException(404, "职务不存在")
    p.allowance = req.allowance
    if req.name: p.name = req.name
    db.commit()
    log_action(db, None, u.username, "修改全局职务", f"{p.name}(职级补助{p.allowance:g})")
    return {"id": p.id, "name": p.name, "allowance": p.allowance}

@app.delete("/api/global/positions/{pid}")
def del_position(pid: int, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    p = db.query(GlobalPosition).get(pid)
    if not p:
        raise HTTPException(404, "职务不存在")
    db.delete(p); db.commit()
    log_action(db, None, u.username, "删除全局职务", p.name)
    return {"ok": True}


# ========== 员工 ==========
class EmployeeReq(BaseModel):
    id: int = 0
    store_id: int
    name: str
    id_card: str = ""
    gender: str = ""
    birth_date: str = ""
    age: int = 0
    status: str = "在职"
    department: str = ""
    position: str = ""
    phone: str = ""
    address: str = ""
    bank_card: str = ""
    bank_name: str = ""
    is_bocom: str = "否"
    payment_method: str = "银行卡"
    social_security: str = "有社保"
    contract_start: str = ""
    contract_end: str = ""

@app.get("/api/employees")
def list_employees(store_id: int, x_user_id: int, db: SessionLocal = Depends(get_db)):
    rows = db.query(Employee).filter(Employee.store_id == store_id).all()
    # 在职排前
    rows = sorted(rows, key=lambda e: (e.status != "在职", e.department, e.position, e.name))
    return [{"id": e.id, "name": e.name, "id_card": e.id_card, "gender": e.gender,
             "birth_date": e.birth_date, "age": e.age, "status": e.status,
             "department": e.department, "position": e.position, "phone": e.phone,
             "address": e.address, "bank_card": e.bank_card, "bank_name": e.bank_name,
             "is_bocom": e.is_bocom, "payment_method": e.payment_method,
             "social_security": e.social_security, "contract_start": e.contract_start,
             "contract_end": e.contract_end} for e in rows]

@app.post("/api/employees")
def upsert_employee(req: EmployeeReq, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    g, b, a = parse_id_card(req.id_card)
    if g:
        req.gender, req.birth_date, req.age = g, b, a
    if req.id:
        e = db.query(Employee).get(req.id)
        if not e:
            raise HTTPException(404, "员工不存在")
        for k, v in req.dict().items():
            if k in ("id", "store_id"): continue
            setattr(e, k, v)
        e.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        e = Employee(store_id=req.store_id, name=req.name, id_card=req.id_card, gender=req.gender,
                     birth_date=req.birth_date, age=req.age, status=req.status,
                     department=req.department, position=req.position, phone=req.phone,
                     address=req.address, bank_card=req.bank_card, bank_name=req.bank_name,
                     is_bocom=req.is_bocom, payment_method=req.payment_method,
                     social_security=req.social_security, contract_start=req.contract_start,
                     contract_end=req.contract_end)
        db.add(e)
    db.commit(); db.refresh(e)
    log_action(db, req.store_id, u.username, "新增/修改员工", e.name)
    return {"id": e.id}

@app.delete("/api/employees/{eid}")
def del_employee(eid: int, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    e = db.query(Employee).get(eid)
    if not e:
        raise HTTPException(404, "员工不存在")
    log_action(db, e.store_id, u.username, "删除员工", e.name)
    db.delete(e); db.commit()
    return {"ok": True}


# ========== 工资明细 ==========
class SalaryReq(BaseModel):
    id: int = 0
    store_id: int
    employee_id: int
    month: str
    attendance_days: float = 0
    base_salary: float = 0
    ss_return: float = 0
    performance_salary: float = 0
    position_allowance: float = 0
    holiday_salary: float = 0
    bonus_salary: float = 0
    sales_commission: float = 0
    overtime_hours: float = 0
    other_allowance: float = 0
    full_attendance: float = 0
    award: float = 0
    leave_days: float = 0
    absent_days: float = 0
    outing_hours: float = 0
    discipline_deduction: float = 0
    quality_deduction: float = 0
    ss_paid: float = 0
    tax: float = 0
    notes: str = ""

@app.get("/api/salaries")
def list_salaries(store_id: int, x_user_id: int, month: str = "", dept: str = "",
                  db: SessionLocal = Depends(get_db)):
    q = db.query(SalaryDetail).filter(SalaryDetail.store_id == store_id)
    if month:
        q = q.filter(SalaryDetail.month == month)
    rows = q.order_by(SalaryDetail.month.desc(), SalaryDetail.id).all()
    out = []
    for s in rows:
        e = db.query(Employee).get(s.employee_id)
        out.append({"id": s.id, "month": s.month, "employee_id": s.employee_id,
                    "name": e.name if e else "", "department": e.department if e else "",
                    "position": e.position if e else "", "attendance_days": s.attendance_days,
                    "base_salary": s.base_salary, "ss_return": s.ss_return,
                    "performance_salary": s.performance_salary, "position_allowance": s.position_allowance,
                    "holiday_salary": s.holiday_salary, "subtotal1": s.subtotal1,
                    "bonus_salary": s.bonus_salary, "sales_commission": s.sales_commission,
                    "overtime_hours": s.overtime_hours, "overtime_pay": s.overtime_pay,
                    "other_allowance": s.other_allowance, "full_attendance": s.full_attendance,
                    "award": s.award, "subtotal2": s.subtotal2, "total_salary": s.total_salary,
                    "leave_days": s.leave_days, "leave_deduction": s.leave_deduction,
                    "absent_days": s.absent_days, "absent_deduction": s.absent_deduction,
                    "outing_hours": s.outing_hours, "outing_deduction": s.outing_deduction,
                    "discipline_deduction": s.discipline_deduction,
                    "quality_deduction": s.quality_deduction, "ss_paid": s.ss_paid,
                    "total_deduction": s.total_deduction, "tax": s.tax,
                    "actual_salary": s.actual_salary, "notes": s.notes})
    return out

@app.get("/api/salaries/months")
def list_months(store_id: int, x_user_id: int, db: SessionLocal = Depends(get_db)):
    rows = db.query(SalaryDetail.month).filter(SalaryDetail.store_id == store_id).distinct().order_by(SalaryDetail.month.desc()).all()
    return [r[0] for r in rows]

@app.post("/api/salaries")
def upsert_salary(req: SalaryReq, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    data = req.dict()
    calc = calc_salary_fields(data)
    data.update(calc)
    e = db.query(Employee).get(req.employee_id)
    is_bocom = e.is_bocom == "是" if e else False
    # 交行代付：仅是否交行=是才记实发，否则0
    bocom_pay = data["actual_salary"] if is_bocom else 0
    if req.id:
        s = db.query(SalaryDetail).get(req.id)
        if not s:
            raise HTTPException(404, "工资记录不存在")
        for k in ["attendance_days","base_salary","ss_return","performance_salary","position_allowance",
                  "holiday_salary","subtotal1","bonus_salary","sales_commission","overtime_hours",
                  "overtime_pay","other_allowance","full_attendance","award","subtotal2","total_salary",
                  "leave_days","leave_deduction","absent_days","absent_deduction","outing_hours",
                  "outing_deduction","discipline_deduction","quality_deduction","ss_paid","total_deduction",
                  "tax","actual_salary"]:
            setattr(s, k, data[k])
        s.notes = req.notes
        s.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.commit()
    else:
        s = SalaryDetail(store_id=req.store_id, employee_id=req.employee_id, month=req.month,
                         attendance_days=req.attendance_days, base_salary=req.base_salary,
                         ss_return=req.ss_return, performance_salary=req.performance_salary,
                         position_allowance=req.position_allowance, holiday_salary=req.holiday_salary,
                         subtotal1=calc["subtotal1"], bonus_salary=req.bonus_salary,
                         sales_commission=req.sales_commission, overtime_hours=req.overtime_hours,
                         overtime_pay=calc["overtime_pay"], other_allowance=req.other_allowance,
                         full_attendance=req.full_attendance, award=req.award,
                         subtotal2=calc["subtotal2"], total_salary=calc["total_salary"],
                         leave_days=req.leave_days, leave_deduction=calc["leave_deduction"],
                         absent_days=req.absent_days, absent_deduction=calc["absent_deduction"],
                         outing_hours=req.outing_hours, outing_deduction=calc["outing_deduction"],
                         discipline_deduction=req.discipline_deduction,
                         quality_deduction=req.quality_deduction, ss_paid=req.ss_paid,
                         total_deduction=calc["total_deduction"], tax=req.tax,
                         actual_salary=calc["actual_salary"], notes=req.notes)
        db.add(s)
        db.flush()
    # 同步发放记录
    payment = db.query(SalaryPayment).filter(SalaryPayment.employee_id == req.employee_id,
                                             SalaryPayment.month == req.month).first()
    if not payment:
        payment = SalaryPayment(store_id=req.store_id, employee_id=req.employee_id, month=req.month)
        db.add(payment)
    payment.should_pay = calc["total_salary"]
    payment.actual_pay = calc["actual_salary"]
    payment.bocom_pay = bocom_pay
    payment.payment_method = e.payment_method if e else ""
    db.commit()
    log_action(db, req.store_id, u.username, "保存工资明细", f"{e.name if e else ''} {req.month}")
    return {"id": s.id}

@app.delete("/api/salaries/{sid}")
def del_salary(sid: int, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    s = db.query(SalaryDetail).get(sid)
    if not s:
        raise HTTPException(404, "工资记录不存在")
    db.query(SalaryPayment).filter(SalaryPayment.employee_id == s.employee_id,
                                   SalaryPayment.month == s.month).delete()
    db.delete(s); db.commit()
    log_action(db, s.store_id, u.username, "删除工资明细", f"id={sid}")
    return {"ok": True}


# ========== 提成规则（全局）==========
class RuleReq(BaseModel):
    position: str
    perf_rate: float = 0
    sales_rate: float = 0
    description: str = ""

@app.get("/api/rules")
def list_rules(x_user_id: int, db: SessionLocal = Depends(get_db)):
    return [{"id": r.id, "position": r.position, "perf_rate": r.perf_rate,
             "sales_rate": r.sales_rate, "description": r.description}
            for r in db.query(CommissionRule).order_by(CommissionRule.position)]

@app.post("/api/rules")
def add_rule(req: RuleReq, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    if db.query(CommissionRule).filter(CommissionRule.position == req.position).first():
        raise HTTPException(400, "该职务提成规则已存在")
    r = CommissionRule(position=req.position, perf_rate=req.perf_rate,
                       sales_rate=req.sales_rate, description=req.description)
    db.add(r); db.commit(); db.refresh(r)
    log_action(db, None, u.username, "新增提成规则", req.position)
    return {"id": r.id}

@app.put("/api/rules/{rid}")
def update_rule(rid: int, req: RuleReq, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    r = db.query(CommissionRule).get(rid)
    if not r:
        raise HTTPException(404, "规则不存在")
    r.position, r.perf_rate, r.sales_rate, r.description = req.position, req.perf_rate, req.sales_rate, req.description
    db.commit()
    log_action(db, None, u.username, "修改提成规则", req.position)
    return {"id": r.id}

@app.delete("/api/rules/{rid}")
def del_rule(rid: int, x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    r = db.query(CommissionRule).get(rid)
    if not r:
        raise HTTPException(404, "规则不存在")
    db.delete(r); db.commit()
    log_action(db, None, u.username, "删除提成规则", r.position)
    return {"ok": True}


# ========== 发放/统计/审计 ==========
@app.get("/api/payments")
def list_payments(store_id: int, month: str, x_user_id: int, db: SessionLocal = Depends(get_db)):
    q = db.query(SalaryPayment).filter(SalaryPayment.store_id == store_id, SalaryPayment.month == month)
    rows = q.all()
    out = []
    for p in rows:
        e = db.query(Employee).get(p.employee_id)
        out.append({"id": p.id, "month": p.month, "employee_id": p.employee_id,
                    "name": e.name if e else "", "department": e.department if e else "",
                    "should_pay": p.should_pay, "actual_pay": p.actual_pay,
                    "bocom_pay": p.bocom_pay, "payment_method": p.payment_method})
    return out

@app.get("/api/dashboard")
def dashboard(store_id: int, x_user_id: int, db: SessionLocal = Depends(get_db)):
    total = db.query(Employee).filter(Employee.store_id == store_id).count()
    active = db.query(Employee).filter(Employee.store_id == store_id, Employee.status == "在职").count()
    latest = db.query(SalaryDetail.month).filter(SalaryDetail.store_id == store_id).order_by(SalaryDetail.month.desc()).first()
    latest = latest[0] if latest else None
    should = actual = 0
    monthly = []
    if latest:
        for s in db.query(SalaryDetail).filter(SalaryDetail.store_id == store_id, SalaryDetail.month == latest):
            should += s.total_salary; actual += s.actual_salary
        # 各月实发趋势
        months = db.query(SalaryDetail.month).filter(SalaryDetail.store_id == store_id).distinct().order_by(SalaryDetail.month).all()
        for (m,) in months:
            act = sum(s.actual_salary for s in db.query(SalaryDetail).filter(SalaryDetail.store_id == store_id, SalaryDetail.month == m))
            monthly.append({"month": m, "actual": act})
    return {"total_emp": total, "active_emp": active, "latest_month": latest,
            "latest_should": should, "latest_actual": actual, "monthly": monthly}


@app.get("/api/admin/stats")
def admin_stats(x_user_id: int, db: SessionLocal = Depends(get_db)):
    """超管全局统计：各店铺收入/人员、全系统人员分布、年龄分布"""
    u = db.query(User).get(x_user_id)
    if u.role != "super_admin":
        raise HTTPException(403, "无权限")
    # 各店铺：员工/在职/工资记录/累计应发/累计实发/最新月
    store_stats = []
    for s in db.query(Store).order_by(Store.id):
        emps = db.query(Employee).filter(Employee.store_id == s.id)
        total_emp = emps.count()
        active = emps.filter(Employee.status == "在职").count()
        recs = db.query(SalaryDetail).filter(SalaryDetail.store_id == s.id).count()
        should = sum(x.total_salary for x in db.query(SalaryDetail).filter(SalaryDetail.store_id == s.id))
        actual = sum(x.actual_salary for x in db.query(SalaryDetail).filter(SalaryDetail.store_id == s.id))
        latest = db.query(SalaryDetail.month).filter(SalaryDetail.store_id == s.id).order_by(SalaryDetail.month.desc()).first()
        store_stats.append({"store_id": s.id, "name": s.name, "total_emp": total_emp,
                            "active_emp": active, "salary_records": recs,
                            "total_should": round(should), "total_actual": round(actual),
                            "latest_month": latest[0] if latest else None})
    # 全系统人员分布：按商铺/在职离职/部门
    by_store = [{"name": s["name"], "value": s["total_emp"]} for s in store_stats]
    status_dist = {"在职": 0, "离职": 0}
    for e in db.query(Employee):
        status_dist[e.status] = status_dist.get(e.status, 0) + 1
    dept_dist = {}
    for e in db.query(Employee):
        d = e.department or "未分配"
        dept_dist[d] = dept_dist.get(d, 0) + 1
    # 年龄段分布
    age_bins = {"18-25": 0, "26-30": 0, "31-35": 0, "36-40": 0, "41-45": 0, "46-50": 0, "50+": 0}
    for e in db.query(Employee):
        a = e.age or 0
        if 18 <= a <= 25: age_bins["18-25"] += 1
        elif a <= 30: age_bins["26-30"] += 1
        elif a <= 35: age_bins["31-35"] += 1
        elif a <= 40: age_bins["36-40"] += 1
        elif a <= 45: age_bins["41-45"] += 1
        elif a <= 50: age_bins["46-50"] += 1
        else: age_bins["50+"] += 1
    return {"store_stats": store_stats, "by_store": by_store, "status_dist": status_dist,
            "dept_dist": [{"name": k, "value": v} for k, v in sorted(dept_dist.items())],
            "age_dist": [{"name": k, "value": v} for k, v in age_bins.items()]}

@app.get("/api/audit")
def list_audit(x_user_id: int, db: SessionLocal = Depends(get_db)):
    u = db.query(User).get(x_user_id)
    q = db.query(AuditLog)
    if u.role != "super_admin":
        q = q.filter(AuditLog.store_id == u.store_id)
    return [{"id": a.id, "created_at": a.created_at, "username": a.username,
             "action": a.action, "detail": a.detail}
            for a in q.order_by(AuditLog.id.desc()).limit(500).all()]


# ---------- 启动时建表 ----------
def init_schema():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.role == "super_admin").first():
            db.add(User(store_id=None, username="admin", password="admin2555", role="super_admin"))
            db.commit()
        # 默认部门
        for dep in ["生鲜部", "百货部", "收银部", "后勤部"]:
            if not db.query(GlobalDepartment).filter(GlobalDepartment.name == dep).first():
                db.add(GlobalDepartment(name=dep))
        # 默认职务+职级补助
        for name, alw in [("店长", 2000), ("主管", 1200), ("收银员", 300), ("理货员", 300), ("小时工", 0)]:
            if not db.query(GlobalPosition).filter(GlobalPosition.name == name).first():
                db.add(GlobalPosition(name=name, allowance=alw))
        db.commit()
    finally:
        db.close()


init_schema()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
