"""
Error response schemas for API endpoints.
"""
from marshmallow import Schema, fields

class ErrorSchema(Schema):
    """Schema for error responses."""
    success = fields.Boolean(default=False)
    error = fields.String(required=True)
    message = fields.String(allow_none=True)
    
class ValidationErrorSchema(ErrorSchema):
    """Schema for validation error responses."""
    errors = fields.Dict(keys=fields.String(), values=fields.List(fields.String()))

class APIResponseSchema(Schema):
    """Base schema for all API responses."""
    success = fields.Boolean(required=True)
    data = fields.Raw(allow_none=True)
    message = fields.String(allow_none=True)
    error = fields.String(allow_none=True)