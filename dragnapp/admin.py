from django.contrib import admin

# Register your models here.
from dragnapp.models import Paragraph, Closeness, Text, Alias, KbRelation, IndexRelation

class IndexRelationAdmin(admin.ModelAdmin):
    list_display = ("alias", "subject", "predicate", "object", "value", "paragraph")


admin.site.register(Paragraph)
admin.site.register(Closeness)
admin.site.register(Text)
admin.site.register(Alias)
admin.site.register(KbRelation)
admin.site.register(IndexRelation, IndexRelationAdmin)
