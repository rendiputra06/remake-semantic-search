from marshmallow import Schema, fields

class QuranIndexSchema(Schema):
    """Schema untuk validasi quran index"""
    id = fields.Integer()
    title = fields.String()
    description = fields.String(allow_none=True)
    parent_id = fields.Integer(allow_none=True)
    level = fields.Integer()
    sort_order = fields.Integer()
    has_children = fields.Boolean()
    has_ayat = fields.Boolean()
    ayat_count = fields.Integer()
    list_ayat = fields.List(fields.String(), allow_none=True)

class QuranIndexTreeSchema(Schema):
    """Schema untuk validasi tree structure"""
    id = fields.Integer()
    title = fields.String()
    has_children = fields.Boolean()
    has_ayat = fields.Boolean()
    ayat_count = fields.Integer()
    children = fields.List(fields.Nested(lambda: QuranIndexTreeSchema()))

class QuranIndexStatsSchema(Schema):
    """Schema untuk validasi statistik index"""
    total_categories = fields.Integer()
    total_ayat = fields.Integer()
    categories_with_ayat = fields.Integer()
    level_stats = fields.List(fields.Dict())
    parent_type_stats = fields.List(fields.Dict())
    surah_stats = fields.List(fields.Dict())
