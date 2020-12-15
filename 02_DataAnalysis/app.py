from flask import Flask, render_template, session, escape, request
from datetime import timedelta, datetime
from fbprophet import Prophet
import os
import pandas as pd 
import folium
import json
import pandas_datareader as pdr
import matplotlib as mpl 
import matplotlib.pyplot as plt 
# 한글폰트 사용
mpl.rc('font', family='Malgun Gothic')
mpl.rc('axes', unicode_minus=False)

from my_util.weather import get_weather
app = Flask(__name__)
app.secret_key = 'qwert12345'
kospi_dict, kosdaq_dict = {}, {}

def get_weather_main():
    weather = None
    try:
        weather = session['weather']
    except:
        app.logger.debug("get new weather info")
        weather = get_weather()
        session['weather'] = weather
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=60)
    return weather

@app.before_first_request
def before_first_request():
    kospi = pd.read_csv('./static/data/KOSPI.csv', dtype={'종목코드': str})
    for i in kospi.index:
        kospi_dict[kospi['종목코드'][i]] = kospi['종목명'][i]
    kosdaq = pd.read_csv('./static/data/KOSDAQ.csv', dtype={'종목코드': str})
    for i in kosdaq.index:
        kosdaq_dict[kosdaq['종목코드'][i]] = kosdaq['종목명'][i]

@app.before_request
def before_request():
    pass        # 모든 GET 요청을 처리하는 놈에 앞서서 공통적으로 뭔 일을 처리함

@app.route('/')
def index():
    menu = {'ho':1, 'da':0, 'ml':0, 'se':0, 'co':0, 'cg':0, 'cr':0, 'st':0, 'wc':0}
    return render_template('main.html', menu=menu, weather=get_weather_main())

@app.route('/park', methods=['GET', 'POST'])
def park():
    menu = {'ho':0, 'da':1, 'ml':0, 'se':1, 'co':0, 'cg':0, 'cr':0, 'st':0, 'wc':0}
    park_new = pd.read_csv('./static/data/park_info.csv')
    park_gu = pd.read_csv('./static/data/park_gu.csv')
    if request.method == 'GET':
        map = folium.Map(location=[37.5502, 126.982], zoom_start=11)
        for i in park_new.index:
            folium.CircleMarker([park_new.lat[i], park_new.lng[i]], 
                                radius=int(park_new['size'][i]),
                                tooltip=f"{park_new['공원명'][i]}({int(park_new.area[i])}㎡)",
                                color='#3186cc', fill_color='#3186cc').add_to(map)
        html_file = os.path.join(app.root_path, 'static/img/park.html')
        map.save(html_file)
        mtime = int(os.stat(html_file).st_mtime)
        return render_template('park.html', menu=menu, weather=get_weather_main(),
                                park_list=list(park_new['공원명'].values), 
                                gu_list = list(park_new['지역'].unique()), mtime=mtime)
    else:
        gubun = request.form['gubun']
        if gubun == 'name':
            park_name = request.form['name']
            df = park_new[park_new['공원명'] == park_name].reset_index()
            park_result = {'name':park_name, 'addr':df['공원주소'][0], 'area':df.area[0], 'desc':df['공원개요'][0]}
            map = folium.Map(location=[37.5502, 126.982], zoom_start=11)
            for i in park_new.index:
                folium.CircleMarker([park_new.lat[i], park_new.lng[i]], 
                                    radius=int(park_new['size'][i]),
                                    tooltip=f"{park_new['공원명'][i]}({int(park_new.area[i])}㎡)",
                                    color='#3186cc', fill_color='#3186cc').add_to(map)
            folium.CircleMarker([df.lat[0], df.lng[0]], radius=int(df['size'][0]),
                                    tooltip=f"{df['공원명'][0]}({int(df.area[0])}㎡)",
                                    color='crimson', fill_color='crimson').add_to(map)
            html_file = os.path.join(app.root_path, 'static/img/park_res.html')
            map.save(html_file)
            mtime = int(os.stat(html_file).st_mtime)
            return render_template('park_res.html', menu=menu, weather=get_weather_main(),
                                    park_result=park_result, mtime=mtime)
        else:
            gu_name = request.form['gu']
            df = park_gu[park_gu['구별'] == gu_name].reset_index()
            park_result2 = {'gu':gu_name, 'gu_area':df['구면적'][0], 
                            'park_area':df['공원총면적'][0], 
                            'park_cnt':df['공원수'][0]}
            select_gu = park_new[park_new['지역'] == gu_name]
            map = folium.Map(location=[select_gu['lat'].mean(), select_gu['lng'].mean()], zoom_start=12)
            for i in select_gu.index:
                folium.CircleMarker([select_gu.lat[i], select_gu.lng[i]], 
                                    radius=int(select_gu['size'][i])*2,
                                    tooltip=f"{select_gu['공원명'][i]}({int(select_gu.area[i])}㎡)",
                                    color='#3186cc', fill_color='#3186cc').add_to(map)
            html_file = os.path.join(app.root_path, 'static/img/park_res.html')
            map.save(html_file)
            mtime = int(os.stat(html_file).st_mtime)
            return render_template('park_res2.html', menu=menu, weather=get_weather_main(),
                                    park_result=park_result2, mtime=mtime)

@app.route('/park_gu/<option>')
def park_gu(option):
    menu = {'ho':0, 'da':1, 'ml':0, 'se':1, 'co':0, 'cg':0, 'cr':0, 'st':0, 'wc':0}
    park_new = pd.read_csv('./static/data/park_info.csv')
    park_gu_new = pd.read_csv('./static/data/park_gu_new.csv')
    geo_path = './static/data/skorea_municipalities_geo_simple.json'
    geo_str = json.load(open(geo_path, encoding='utf-8'))

    map = folium.Map(location=[37.5502, 126.982], zoom_start=11, tiles='Stamen Toner')
    if option == 'area':
        map.choropleth(geo_data = geo_str,
                       data = park_gu_new['공원총면적'],
                       columns = [park_gu_new.index, park_gu_new['공원총면적']],
                       fill_color = 'PuRd',
                       key_on = 'feature.id')
    elif option == 'count':
        map.choropleth(geo_data = geo_str,
                       data = park_gu_new['공원수'],
                       columns = [park_gu_new.index, park_gu_new['공원수']],
                       fill_color = 'PuRd',
                       key_on = 'feature.id')
    elif option == 'area_ratio':
        map.choropleth(geo_data = geo_str,
                       data = park_gu_new['공원면적비율'],
                       columns = [park_gu_new.index, park_gu_new['공원면적비율']],
                       fill_color = 'PuRd',
                       key_on = 'feature.id')
    elif option == 'per_person':
        map.choropleth(geo_data = geo_str,
                       data = park_gu_new['인당공원면적'],
                       columns = [park_gu_new.index, park_gu_new['인당공원면적']],
                       fill_color = 'PuRd',
                       key_on = 'feature.id')

    for i in park_new.index:
        folium.CircleMarker([park_new.lat[i], park_new.lng[i]], 
                        radius=int(park_new['size'][i]),
                        tooltip=f"{park_new['공원명'][i]}({int(park_new.area[i])}㎡)",
                        color='blue', fill_color='blue').add_to(map)
    html_file = os.path.join(app.root_path, 'static/img/park_gu.html')
    map.save(html_file)
    mtime = int(os.stat(html_file).st_mtime)
    option_dict = {'area':'공원면적', 'count':'공원수', 'area_ratio':'공원면적 비율', 'per_person':'인당 공원면적'}
    return render_template('park_gu.html', menu=menu, weather=get_weather_main(),
                            option=option, option_dict=option_dict, mtime=mtime)

@app.route('/stock', methods=['GET', 'POST'])
def stock():
    menu = {'ho':0, 'da':1, 'ml':0, 'se':0, 'co':0, 'cg':0, 'cr':0, 'st':1, 'wc':0}
    if request.method == 'GET':
        return render_template('stock.html', menu=menu, weather=get_weather_main(), 
                                kospi=kospi_dict, kosdaq=kosdaq_dict)
    else:
        market = request.form['market']
        if market == 'KS':
            code = request.form['kospi_code']
            company = kospi_dict[code]
            code += '.KS'
        else:
            code = request.form['kosdaq_code']
            company = kosdaq_dict[code]
            code += '.KQ'
        learn_period = int(request.form['learn'])
        pred_period = int(request.form['pred'])
        today = datetime.now()
        start_learn = today - timedelta(days=learn_period * 365)
        end_learn = today - timedelta(days=1)

        stock_data = pdr.DataReader(code, data_source='yahoo', start=start_learn, end=end_learn)
        app.logger.debug(f"get stock data: {code}")
        df = pd.DataFrame({'ds': stock_data.index, 'y': stock_data.Close})
        df.reset_index(inplace=True)
        del df['Date']

        model = Prophet(daily_seasonality=True)
        model.fit(df)
        future = model.make_future_dataframe(periods=pred_period)
        forecast = model.predict(future)
        
        fig = model.plot(forecast);
        img_file = os.path.join(app.root_path, 'static/img/stock.png')
        fig.savefig(img_file)
        mtime = int(os.stat(img_file).st_mtime)

        return render_template('stock_res.html', menu=menu, weather=get_weather_main(), 
                                mtime=mtime, company=company, code=code)

if __name__ == '__main__':
    app.run(debug=True)