"""
Public Thesaurus schemas for request validation.
"""
from marshmallow import Schema, fields, validate

class ThesaurusSearchSchema(Schema):
    """Schema for thesaurus search request."""
    word = fields.String(required=True, validate=validate.Length(min=1, max=100))

class ThesaurusBrowseSchema(Schema):
    """Schema for thesaurus browse request."""
    page = fields.Integer(load_default=1, validate=validate.Range(min=1, max=1000))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
    sort_by = fields.String(load_default='word', validate=validate.OneOf(['word', 'relations', 'score']))
    filter_type = fields.String(load_default='all', validate=validate.OneOf(['all', 'synonym', 'antonym', 'hyponym', 'hypernym']))

class ThesaurusRandomSchema(Schema):
    """Schema for random words request."""
    count = fields.Integer(load_default=10, validate=validate.Range(min=1, max=50))

class ThesaurusPopularSchema(Schema):
    """Schema for popular words request."""
    limit = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))

class ThesaurusSuggestionsSchema(Schema):
    """Schema for search suggestions request."""
    q = fields.String(required=True, validate=validate.Length(min=2, max=100))
    limit = fields.Integer(load_default=10, validate=validate.Range(min=1, max=20)) 