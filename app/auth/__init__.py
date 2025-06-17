"""
Authentication module initialization.
"""
from flask import Blueprint
from .routes import auth_bp

# Export the blueprint
blueprint = auth_bp

# Additional initialization code can be added here
