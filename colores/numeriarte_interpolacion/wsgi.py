"""Punto de entrada WSGI para Gunicorn (Render): gunicorn wsgi:app"""
from app import create_app

app = create_app("production")
