import os
from datetime import datetime, timedelta
from typing import Optional, List, Union
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from dotenv import load_dotenv

import models
from database import get_db

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 支援從 Header 或 Cookie 取得 Token
class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        # 優先從 Header 取得 (Bearer Token)
        authorization: str = request.headers.get("Authorization")
        if authorization:
            scheme, param = authorization.split()
            if scheme.lower() == "bearer":
                return param
        
        # 其次從 Cookie 取得 (常用於瀏覽器導向的應用)
        token = request.cookies.get("access_token")
        if token:
            return token
            
        return None

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="auth/login", auto_error=False)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        # 如果是網頁請求且未登入，這裡可以拋出異常讓前端導向登入頁
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="請先登入系統",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="憑證內容無效")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="憑證已過期或無效")
        
    user = db.query(models.Employee).filter(models.Employee.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="找不到使用者")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="使用者帳號已停用")
    return user

def check_permissions(required_permissions: Union[str, List[str]]):
    """
    權限檢查器。
    用法: Depends(check_permissions("invoice:create")) 或 Depends(check_permissions(["invoice:read", "invoice:write"]))
    """
    if isinstance(required_permissions, str):
        required_permissions = [required_permissions]

    async def permission_dependency(current_user: models.Employee = Depends(get_current_user)):
        # 管理者 (Admin) 擁有一切權限
        if current_user.role and current_user.role.name == "Admin":
            return current_user
            
        # 取得使用者擁有的所有權限代碼
        user_perms = []
        if current_user.role:
            user_perms = [p.code for p in current_user.role.permissions]
            
        # 只要符合其中一個權限即可通過
        for perm in required_permissions:
            if perm in user_perms:
                return current_user
                
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限"
        )
    return permission_dependency
