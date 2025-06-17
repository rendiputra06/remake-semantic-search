"""
Admin module initialization.
"""
from flask import Blueprint
from .routes import admin_bp

# Export the blueprint
blueprint = admin_bp
