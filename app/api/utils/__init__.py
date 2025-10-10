"""
Utils package: expose both API response helpers and model utilities so that
imports like `from app.api.utils import create_response` keep working, and
`from app.api.utils.model_utils import init_model` is also supported.
"""
from flask import jsonify, make_response  # type: ignore
from werkzeug.http import HTTP_STATUS_CODES  # type: ignore

# Response helper functions (mirrored from legacy app/api/utils.py)
def create_response(success=True, data=None, message=None, error=None, status_code=200):
    response = {
        'success': success,
        'data': data,
        'message': message,
        'error': error
    }
    return make_response(jsonify(response), status_code)


def error_response(status_code, message=None):
    payload = {
        'success': False,
        'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error'),
        'message': message,
        'data': None
    }
    return make_response(jsonify(payload), status_code)


def validation_error_response(messages):
    return create_response(
        success=False,
        error='Validation error',
        message='Invalid input data',
        data={'errors': messages},
        status_code=400
    )


# Model utilities re-export
from .model_utils import init_model, get_classification_path  # noqa: E402,F401
