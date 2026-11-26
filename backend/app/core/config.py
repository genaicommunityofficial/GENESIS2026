from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = ""
    jwt_secret: str = "dev"
    jwt_expire_min: int = 240
    admin_email: str = "admin@genesis.local"
    admin_password: str = "change_me"
    cors_origins: str = "*"
    # game constants (PRD §8, §10)
    starting_capital: float = 25000.0
    topup_amount: float = 5000.0
    max_concentration_pct: float = 0.35
    max_shares_per_user: int = 40
    price_floor: float = 10.0
    short_squeeze_mult: float = 1.80
    tick_min_s: float = 5.0
    tick_max_s: float = 8.0

settings = Settings()
