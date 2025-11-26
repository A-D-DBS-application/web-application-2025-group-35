import os
import secrets

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres.iujvntadipxpwozzacty:OpWielekes123@aws-1-eu-central-1.pooler.supabase.com:5432/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Voeg engine opties toe om max clients te beperken
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,       # maximaal 5 gelijktijdige connecties
        "max_overflow": 0,    # geen extra tijdelijke connecties
        "pool_timeout": 30,   # wacht maximaal 30 sec als pool vol is
        "pool_recycle": 280,  # recycle connecties automatisch na 280 sec
    }
