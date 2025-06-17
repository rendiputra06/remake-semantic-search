"""
Statistics request and response schemas.
"""
from marshmallow import Schema, fields, validate
from datetime import datetime

class StatsDailyRequestSchema(Schema):
    """Schema for daily statistics request parameters."""
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)

class StatsDailyDataSchema(Schema):
    """Schema for daily statistics data."""
    date = fields.Date(required=True)
    total_searches = fields.Integer(required=True)
    unique_users = fields.Integer(required=True)
    avg_results = fields.Float()
    model_usage = fields.Dict(keys=fields.String(), values=fields.Integer())

class StatsOverallDataSchema(Schema):
    """Schema for overall statistics data."""
    total_searches = fields.Integer(required=True)
    total_users = fields.Integer(required=True)
    total_indexed_verses = fields.Integer(required=True)
    total_categories = fields.Integer(required=True)
    model_usage = fields.Dict(keys=fields.String(), values=fields.Integer())
    avg_results_per_search = fields.Float()
    last_updated = fields.DateTime(required=True)

class StatsOverallResponseSchema(Schema):
    """Schema for overall statistics response."""
    overall = fields.Nested(StatsOverallDataSchema)
    trends = fields.Dict(keys=fields.String(), values=fields.List(fields.Raw()))