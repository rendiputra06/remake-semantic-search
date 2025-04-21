#!/usr/bin/env python
"""
File WSGI untuk menjalankan aplikasi dengan Gunicorn
"""
from app import app

if __name__ == "__main__":
    app.run() 