import os
import secrets

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres.iujvntadipxpwozzacty:OpWielekes123@aws-1-eu-central-1.pooler.supabase.com:5432/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

#postgresql://postgres.iujvntadipxpwozzacty:OpWielekes123@aws-1-eu-central-1.pooler.supabase.com:5432/postgres
#postgresql://postgres:[OpWielekes123]@db.iujvntadipxpwozzacty.supabase.co:5432/postgres
#link is aangepast want het compiled anders niet