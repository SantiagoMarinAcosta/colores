"""Punto de entrada para desarrollo local: python app.py"""
import os

from app import create_app

app = create_app("development")

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=puerto, debug=True)
