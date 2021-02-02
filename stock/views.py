import datetime
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from django.core.management import call_command
from django.shortcuts import render

from .forms import ScrapeForm
from .models import Stock, Stockholding, Weekday

#callback funtion
def scrape_view(request):
    form = ScrapeForm()
    if request.method == 'POST':
        form = ScrapeForm(request.POST)
        if form.is_valid():
            get_hkex_holiday()
            res = get_hkex(**form.cleaned_data)
            context = {
                'form': form
            }
            context.update(res)
            return render(request, 'scrape.html', context)

    variables = {
        'form': form
    }
    return render(request, 'scrape.html', variables)

#query data from hkex ccass
def get_hkex(stock, start_date, end_date, task, threshold, **kwargs):
    cookies = {
        'TS6b4c3a62027': '08754bc291ab2000ff46ee968aa41b7dec45c5c4f00eb1aa66282e7d6de90846366c536ae70779d408caa4f0d6113000eb369bcd1d84ca38ee6ad7aa16718090eef1835ad5c832d3fdfb5883f045f5548e4cde3782d251448f9790f8400f1a77',
        'TSfff9c5ca027': '086f2721efab2000208d7a44f0b438054ccabdc2f24fd742bc37237e00694a8777df6ed1b94dd4d30844c60e90113000bc416d1da224c5b6225c0ba1890a79545323c226627ac56f57cd3993f8e5d3569c7b11686e2a24490974d9957a006187',
        'WT_FPC': 'id=104.84.150.76-2715731168.30861942:lv=1610632926105:ss=1610632623480',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:84.0) Gecko/20100101 Firefox/84.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.hkexnews.hk',
        'Connection': 'keep-alive',
        'Referer': 'https://www.hkexnews.hk/sdw/search/searchsdw.aspx',
        'Upgrade-Insecure-Requests': '1',
    }

    data = {
        '__EVENTTARGET': 'btnSearch',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': '/wEPDwULLTIwNTMyMzMwMThkZLiCLeQCG/lBVJcNezUV/J0rsyMr',
        '__VIEWSTATEGENERATOR': 'A7B2BBE2',
        'today': datetime.date.today().strftime("%Y%m%d"),
        'sortBy': 'shareholding',
        'sortDirection': 'desc',
        'alertMsg': '',
        'txtShareholdingDate': '',
        'txtStockCode': str(stock).zfill(5) or '00700',
        'txtParticipantID': '',
        'txtParticipantName': '',
        'txtSelPartID': ''
    }

    stock_obj, _ = Stock.objects.get_or_create(code=stock)

    def clean_df(df):
        for col in df.columns:
            df[col] = df[col].apply(lambda x: x.split(":")[1].strip())
        return df

    trading_day_range = Weekday.objects.filter(
        date__gte=start_date, date__lte=end_date, holiday=False).order_by('date').all()
    #Check whether it is a valid trading day
    if not trading_day_range:
        return {}
    for query_date in trading_day_range:
        if Stockholding.objects.filter(date=query_date.date, stock=stock_obj).exists():
            continue
        data['txtShareholdingDate'] = query_date.date.strftime("%Y/%m/%d")
        response = requests.post(
            'https://www.hkexnews.hk/sdw/search/searchsdw.aspx', headers=headers, cookies=cookies, data=data)
        try:
            soup = BeautifulSoup(response.content, 'lxml')
            total_shares = float(soup.findAll(
                "div", {"class": "summary-value"})[0].string.replace(',', ''))
            df = pd.read_html(response.text, header=0)[0]
        #skip if date range or stock code is invalid
        except (ValueError, IndexError):
            continue
        df.columns = ['participant_id', 'name',
                      'address', 'share', 'share_percent']
        df = clean_df(df)
        df['share'] = df['share'].apply(
            lambda x: x.replace(",", "")).astype('int64')
        df['total_shares'] = total_shares
        df['share_percent'] = (df['share']*100/(total_shares+0.00000)).round(5)
        mask = df['participant_id'] == ""
        df.loc[mask, 'participant_id'] = df.loc[mask, 'name'].apply(
            lambda x: f'Z{hash(x) % 10 ** 5}')
        new_Stockholding_objs = [
            Stockholding(stock=stock_obj,
                         date=query_date.date, **row.to_dict())
            for _, row in df.iterrows()
        ]
        Stockholding.objects.bulk_create(new_Stockholding_objs)

    first_trading_date = trading_day_range.first()
    last_trading_date = trading_day_range.last()
    line_chart_data = {}

    #Transform data based on mode - trend or transactions
    if task == "1":
        qs = Stockholding.objects.filter(
            date=last_trading_date.date, stock=stock_obj).order_by("-share_percent")[:10]
        for d in Stockholding.objects.filter(date__gte=start_date, date__lte=end_date, stock=stock_obj, participant_id__in=[q.participant_id for q in qs]).order_by('date').all():
            if d.participant_id in line_chart_data:
                line_chart_data[d.participant_id] += [d.share]
            else:
                line_chart_data[d.participant_id] = [d.share]
        for key, value in line_chart_data.items():
            line_chart_data[key] = ','.join(map(str, value))

    else:
        qs = Stockholding.objects.filter(date__gte=start_date, date__lte=end_date,
                                         stock=stock_obj, daily_percent_diff__gte=threshold).order_by('date').all()

        qs = qs.union(Stockholding.objects.filter(date__gte=start_date, date__lte=end_date,
                                         stock=stock_obj, daily_percent_diff__lte=-1*threshold).order_by('date').all())

    call_command('holding_change')
    return {"task": task, "stock": stock_obj, "first_trade_date": first_trading_date.date, "last_trade_date": last_trading_date.date, "data": qs, "line_chart_data": line_chart_data}


#query exchange holiday
def get_hkex_holiday():
    url = "https://www.hkex.com.hk/-/media/HKEX-Market/Mutual-Market/Stock-Connect/Reference-Materials/Trading-Hour,-Trading-and-Settlement-Calendar/{0}-Calendar_csv_e.csv?la=en"
    for i in range(datetime.datetime.today().year-1, datetime.datetime.today().year+1):
        if not Weekday.objects.filter(date__year=i).exists():
            df = pd.read_csv(url.format(i), header=2)[['Date', 'Hong Kong']]
            df.columns = ['date', 'holiday']
            df['holiday'] = np.where(df['holiday'] == 'Holiday', True, False)
            new_objs = [
                Weekday(**row.to_dict())
                for _, row in df.iterrows()
            ]
            Weekday.objects.bulk_create(new_objs)
