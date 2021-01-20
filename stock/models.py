from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.


class Stock(models.Model):
    code = models.IntegerField(verbose_name='Stock Code')
    name = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"[{str(self.code).zfill(5)}] {self.name}"


class Stockholding(models.Model):
    stock = models.ForeignKey(
        'Stock', verbose_name="Stock", on_delete=models.CASCADE,)
    date = models.DateField(verbose_name='Date', db_index=True)
    participant_id = models.CharField(max_length=20,
                                      blank=True, verbose_name="Participant ID", db_index=True)
    name = models.CharField(blank=True, null=True,
                            max_length=200, verbose_name='Name')
    address = models.TextField(null=True, blank=True, verbose_name="Address")
    share = models.BigIntegerField(verbose_name="Shareholding", default=0)
    share_percent = models.FloatField(verbose_name="Percent of total issued number",
                                      validators=[MinValueValidator(0),
                                                  MaxValueValidator(100)],)
    total_shares = models.BigIntegerField(
        verbose_name="Total Shares", default=0)
    daily_diff = models.FloatField(
        blank=True, null=True, verbose_name="Daily Change")
    daily_percent_diff = models.FloatField(
        blank=True, null=True, verbose_name="Daily Change(%)")


class Weekday(models.Model):
    date = models.DateField(null=True, blank=True, verbose_name='Date')
    holiday = models.BooleanField(default=False, verbose_name='Holiday')

    def __str__(self):
        return f"{self.date}"
