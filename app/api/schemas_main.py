"""
API request/response schemas.
"""
from marshmallow import Schema, fields

class ApiResponse(Schema):
    """Base API response schema."""
    success = fields.Bool(required=True)
    message = fields.Str(required=False)

class ThesaurusEnrichRequest(Schema):
    """Schema for thesaurus enrichment request."""
    wordlist = fields.Str(required=True)
    relation_type = fields.Str(required=True)
    min_score = fields.Float(required=True)
    max_relations = fields.Int(required=True)

class QuranIndexImportRequest(Schema):
    """Schema for Quran index import request."""
    sheet_name = fields.Str(required=True)
    parent_id = fields.Int(required=False, allow_none=True)

class ThesaurusEnrichResponse(ApiResponse):
    """Schema for thesaurus enrichment response."""
    output = fields.Str(required=False)
    error = fields.Str(required=False)

class QuranIndexTreeResponse(ApiResponse):
    """Schema for Quran index tree response."""
    data = fields.List(fields.Dict(), required=True)

class StatisticsResponse(ApiResponse):
    """Schema for statistics response."""
    total_categories = fields.Int(required=True)
    root_categories = fields.Int(required=True)
    categories_with_ayat = fields.Int(required=True)
    total_verses = fields.Int(required=True)
    level_stats = fields.List(fields.Dict(), required=True)
    surah_stats = fields.List(fields.Dict(), required=True)

class LexicalDataImportRequest(Schema):
    """Schema for lexical data import request."""
    overwrite = fields.Bool(required=False, load_default=False)

class ThesaurusDataImportRequest(Schema):
    """Schema for thesaurus data import request."""
    relation_type = fields.Str(required=True)
    overwrite = fields.Bool(required=False, load_default=False)

class WordlistDeleteRequest(Schema):
    """Schema for wordlist deletion request."""
    filename = fields.Str(required=True)

class WordlistResponse(ApiResponse):
    """Schema for wordlist deletion response."""
    filename = fields.Str(required=False)

class ThesaurusSearchResult(Schema):
    """Schema for a single thesaurus search result."""
    word = fields.Str(required=True)
    score = fields.Float(required=True)

class ThesaurusSearchResults(Schema):
    """Schema for thesaurus search results by relation type."""
    synonyms = fields.List(fields.Nested(ThesaurusSearchResult), required=True)
    antonyms = fields.List(fields.Nested(ThesaurusSearchResult), required=True)
    hyponyms = fields.List(fields.Nested(ThesaurusSearchResult), required=True)
    hypernyms = fields.List(fields.Nested(ThesaurusSearchResult), required=True)

class ThesaurusSearchResponse(ApiResponse):
    """Schema for thesaurus search response."""
    results = fields.Nested(ThesaurusSearchResults, required=False)
