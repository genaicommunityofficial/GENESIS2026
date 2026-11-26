"""python -m app.seed  → inserts 30 companies/stocks and the admin account."""
import asyncio, asyncpg
from .core.config import settings
from .core.security import hash_password
from .companies_seed import COMPANIES

async def main():
    c = await asyncpg.connect(settings.database_url)
    for sym, name, sector, price, pe in COMPANIES:
        cid = await c.fetchval(
            "INSERT INTO companies(name,symbol,sector,pe_ratio) VALUES($1,$2,$3,$4) "
            "ON CONFLICT (symbol) DO UPDATE SET name=EXCLUDED.name RETURNING id", name, sym, sector, pe)
        await c.execute(
            "INSERT INTO stocks(company_id,current_price,anchor_price,day_high,day_low) "
            "VALUES($1,$2,$2,$2,$2) ON CONFLICT DO NOTHING", cid, price)
    await c.execute(
        "INSERT INTO profiles(full_name,email,password_hash,role,status) VALUES('Admin',$1,$2,'ADMIN','ACTIVE') "
        "ON CONFLICT (email) DO NOTHING", settings.admin_email, hash_password(settings.admin_password))
    await c.close(); print("seeded")

if __name__ == "__main__": asyncio.run(main())
