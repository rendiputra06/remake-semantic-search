#!/usr/bin/env python
"""
File WSGI untuk menjalankan aplikasi dengan Gunicorn
"""
import sys
import os

# Tambahkan current directory ke Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import aplikasi Flask dari run.py
from run import app

if __name__ == "__main__":
    app.run() 