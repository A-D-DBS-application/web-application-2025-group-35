import os
import secrets

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:[OpWielekes123]@db.iujvntadipxpwozzacty.supabase.co:5432/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

