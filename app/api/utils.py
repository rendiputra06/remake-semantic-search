"""
Utility functions for API standardization.
"""
from flask import jsonify, make_response
from werkzeug.http import HTTP_STATUS_CODES
from marshmallow import ValidationError

def create_response(success=True, data=None, message=None, error=None, status_code=200):
    """
    Create a standardized API response.
    Args:
        success (bool): Whether the request was successful
        data (any): The data to return
        message (str): A message to return
        error (str): Error message if any
        status_code (int): HTTP status code
    Returns:
        Response: A Flask response object with standardized format
    """
    response = {
        'success': success,
        'data': data,
        'message': message,
        'error': error
    }

    return make_response(jsonify(response), status_code)

def error_response(status_code, message=None):
    """
    Create an error response.
    Args:
        status_code (int): HTTP error status code
        message (str): Custom error message
    Returns:
        Response: A Flask error response with standardized format
    """
    payload = {
        'success': False,
        'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error'),
        'message': message,
        'data': None
    }
    
    return make_response(jsonify(payload), status_code)

def validation_error_response(messages):
    """
    Create a validation error response.
    Args:
        messages (dict): Dict of field validation errors
    Returns:
        Response: A Flask response for validation errors
    """
    return create_response(
        success=False,
        error='Validation error',
        message='Invalid input data',
        data={'errors': messages},
        status_code=400
    )
