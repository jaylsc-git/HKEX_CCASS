from django.contrib import admin
from django.db.models.functions import Length
from import_export.admin import ImportExportModelAdmin
from .models import Stock, Stockholding, Weekday
from .resources import StockResource, StockholdingResource, WeekdayResource
# Register your models here.


@admin.register(Stock)
class StockAdmin(ImportExportModelAdmin):
    resource_class = StockResource
    list_display = ['code', 'name']


@admin.register(Stockholding)
class StockholdingAdmin(ImportExportModelAdmin):
    resource_class = StockholdingResource
    list_display = [
        'id',
        'stock', 'date',
        'participant_id', 'name', 'address', 'share', 'share_percent',
    ]
    search_fields = ('participant_id', 'name')
    list_filter = ['date']
    date_hierarchy = 'date'


@admin.register(Weekday)
class WeekdayAdmin(ImportExportModelAdmin):
    resource_class = WeekdayResource
    list_display = ['date', 'holiday']
    list_filter = ['holiday']
    date_hierarchy = 'date'