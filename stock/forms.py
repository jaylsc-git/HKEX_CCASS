from django import forms
from django.core.exceptions import ValidationError

class ScrapeForm(forms.Form):
    from datetime import datetime 
    stock = forms.IntegerField(label='Stock Number')
    start_date = forms.DateField(label='Start Date', widget=forms.SelectDateWidget(years=range(datetime.today().year-1, datetime.today().year+1)))
    end_date = forms.DateField(label='End Date', widget=forms.SelectDateWidget(years=range(datetime.today().year-1, datetime.today().year+1)))

    def clean(self):
        cleaned_data = super().clean()
        if not (cleaned_data.get("start_date") <= cleaned_data.get("end_date")):
            raise ValidationError('The start date must be before the end date')