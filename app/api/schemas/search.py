"""
Search request and response schemas.
"""
from marshmallow import Schema, fields, validate

class SearchRequestSchema(Schema):
    """Schema for search request parameters."""
    query = fields.String(required=True, validate=validate.Length(min=1))
    model = fields.String(load_default='word2vec', validate=validate.OneOf(['word2vec', 'fasttext', 'glove']))
    language = fields.String(load_default='id')
    limit = fields.Integer(load_default=10, validate=validate.Range(min=1, max=100))
    threshold = fields.Float(load_default=0.5, validate=validate.Range(min=0, max=1))

class LexicalSearchRequestSchema(Schema):
    """Schema for lexical search request parameters."""
    query = fields.String(required=True, validate=validate.Length(min=1))
    exact_match = fields.Boolean(load_default=False)
    use_regex = fields.Boolean(load_default=False)
    limit = fields.Integer(load_default=10, validate=validate.Range(min=1, max=100))

class SearchResultSchema(Schema):
    """Schema for individual search result."""
    verse_id = fields.String(required=True)
    surah_number = fields.String(required=True)
    surah_name = fields.String(required=True)
    ayat_number = fields.String(required=True)
    arabic = fields.String(required=True)
    translation = fields.String(required=True)
    similarity = fields.Float(allow_none=True)
    classification = fields.Dict(allow_none=True)
    related_classifications = fields.List(fields.Dict(), allow_none=True)

class SearchResponseSchema(Schema):
    """Schema for search response."""
    query = fields.String(required=True)
    model = fields.String(allow_none=True)
    search_type = fields.String(allow_none=True)
    results = fields.List(fields.Nested(SearchResultSchema))
    count = fields.Integer()
    
class SearchDistributionRequestSchema(Schema):
    """Schema for search distribution request."""
    results = fields.List(fields.Dict(), required=True, validate=validate.Length(min=1))

class SearchDistributionSchema(Schema):
    """Schema for search distribution response."""
    category = fields.String(required=True)
    count = fields.Integer(required=True)
