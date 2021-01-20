from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta 

class ScrapeForm(forms.Form):
    from datetime import datetime 
    stock = forms.IntegerField(label='Stock Number',initial=700)
    start_date = forms.DateField(label='Start Date', widget=forms.SelectDateWidget(years=range(datetime.today().year-1, datetime.today().year+1)),initial=datetime.today()-timedelta(days=2))
    end_date = forms.DateField(label='End Date', widget=forms.SelectDateWidget(years=range(datetime.today().year-1, datetime.today().year+1)),initial=datetime.today()-timedelta(days=1))
    threshold =  forms.DecimalField(label='Minimum Threshold(for finding transactions only)',initial=1)
    
    STATUS_CHOICES = (
        (1, "Trend",),
        (2, "Transactions",),
    )
    
    task = forms.ChoiceField(choices = STATUS_CHOICES, label="", initial='', widget=forms.Select(), required=True)

    def clean(self):
        cleaned_data = super().clean()
        if not (cleaned_data.get("start_date") <= cleaned_data.get("end_date")):
            raise ValidationError('The start date must be before the end date')