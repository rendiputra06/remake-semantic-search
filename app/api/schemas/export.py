"""
Export request and response schemas.
"""
from marshmallow import Schema, fields, validate

class ExportRequestSchema(Schema):
    """Schema for export request parameters."""
    query = fields.String(required=True)
    searchType = fields.String(required=True, validate=validate.OneOf(['semantic', 'lexical', 'expanded']))
    data = fields.String(required=True)  # JSON string of search results
    model = fields.String(allow_none=True)
    expanded_queries = fields.List(fields.String(), allow_none=True)

class SearchResultExportSchema(Schema):
    """Schema for individual search result in export."""
    surah_number = fields.String(required=True)
    surah_name = fields.String(required=True)
    ayat_number = fields.String(required=True)
    reference = fields.String(required=True)
    arabic = fields.String(required=True)
    translation = fields.String(required=True)
    similarity = fields.Float(allow_none=True)
    source_query = fields.String(allow_none=True)
    match_type = fields.String(allow_none=True)
    category = fields.String(allow_none=True)
    classification_path = fields.String(allow_none=True)

class ExportInfoSchema(Schema):
    """Schema for export information sheet."""
    query = fields.String(required=True)
    search_type = fields.String(required=True)
    result_count = fields.Integer(required=True)
    export_time = fields.DateTime(required=True)
    expanded_queries = fields.String(allow_none=True)