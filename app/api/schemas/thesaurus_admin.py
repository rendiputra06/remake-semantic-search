"""
Thesaurus Admin schemas for request validation.
"""
from marshmallow import Schema, fields

class ThesaurusEnrichRequest(Schema):
    """Schema for thesaurus enrichment request."""
    wordlist = fields.Str(required=True)
    relation_type = fields.Str(required=True)
    min_score = fields.Float(required=True)
    max_relations = fields.Int(required=True)

class ThesaurusDataImportRequest(Schema):
    """Schema for thesaurus data import request."""
    relation_type = fields.Str(required=True)
    overwrite = fields.Bool(required=False, load_default=False)

class WordlistDeleteRequest(Schema):
    """Schema for wordlist deletion request."""
    filename = fields.Str(required=True)

class WordlistResponse(Schema):
    """Schema for wordlist deletion response."""
    success = fields.Bool(required=True)
    message = fields.Str(required=False)
    filename = fields.Str(required=False) 