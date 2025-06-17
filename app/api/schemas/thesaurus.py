"""
Thesaurus request and response schemas.
"""
from marshmallow import Schema, fields, validate

class ThesaurusRequestSchema(Schema):
    """Schema for thesaurus word lookup request."""
    word = fields.String(required=True, validate=validate.Length(min=1))

class ThesaurusAddRequestSchema(Schema):
    """Schema for adding synonym request."""
    word = fields.String(required=True, validate=validate.Length(min=1))
    synonym = fields.String(required=True, validate=validate.Length(min=1))

class ThesaurusEnrichRequestSchema(Schema):
    """Schema for thesaurus enrichment request."""
    wordlist = fields.String(required=True)
    relation_type = fields.String(load_default='synonym', 
                                validate=validate.OneOf(['synonym', 'antonym', 'hypernym', 'hyponym']))
    min_score = fields.Float(load_default=0.7, validate=validate.Range(min=0, max=1))
    max_relations = fields.Integer(load_default=5, validate=validate.Range(min=1, max=20))

class ThesaurusResponseSchema(Schema):
    """Schema for thesaurus lookup response."""
    word = fields.String(required=True)
    synonyms = fields.List(fields.String())
    count = fields.Integer()

class RelationSchema(Schema):
    """Schema for word relations in visualization."""
    id = fields.String(required=True)
    label = fields.String(required=True)
    type = fields.String(required=True)
    strength = fields.Float()