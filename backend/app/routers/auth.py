from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..core import db
from ..core.security import verify_password, make_token, hash_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    reg_number: str = Field(min_length=2, max_length=50)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
class LoginIn(BaseModel):
    email: str; password: str

@router.post("/register")
async def register(body: RegisterIn):
    if "@" not in body.email or "." not in body.email.rsplit("@", 1)[-1]:
        raise HTTPException(422, "Enter a valid email address")
    async with db.pool.acquire() as c:
        try:
            await c.execute("INSERT INTO profiles(full_name,reg_number,email,password_hash,role,status) VALUES($1,$2,$3,$4,'PARTICIPANT','PENDING')",
                            body.full_name.strip(), body.reg_number.strip(), body.email.strip().lower(), hash_password(body.password))
        except Exception as exc:
            if "unique" in str(exc).lower(): raise HTTPException(409, "Email or registration number is already registered")
            raise
    return {"status": "PENDING", "message": "Registration submitted for admin approval."}

@router.post("/login")
async def login(body: LoginIn):
    async with db.pool.acquire() as c:
        u = await c.fetchrow("SELECT * FROM profiles WHERE email=$1", body.email.strip().lower())
    if not u or not verify_password(body.password, u["password_hash"]): raise HTTPException(401, "Bad credentials")
    if u["status"] != "ACTIVE": raise HTTPException(403, f"Account {u['status']}")
    return {"token": make_token(str(u["id"]), u["role"]), "role": u["role"], "name": u["full_name"]}
