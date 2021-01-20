from import_export import resources
from .models import Stock, Stockholding, Weekday


class StockholdingResource(resources.ModelResource):
    class Meta:
        model = Stockholding


class StockResource(resources.ModelResource):
    class Meta:
        model = Stock


class WeekdayResource(resources.ModelResource):
    class Meta:
        model = Weekday