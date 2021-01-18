from flask import Blueprint, render_template, request, session, current_app
from datetime import timedelta, datetime
import pandas as pd 
import numpy as np 
import os, folium, json, logging
import pandas_datareader as pdr
import matplotlib as mpl 
import matplotlib.pyplot as plt
from my_util.weather import get_weather
mpl.rc('font', family='Malgun Gothic')
mpl.rc('axes', unicode_minus=False)

seoul_bp = Blueprint('seoul_bp', __name__)

def get_weather_main():
    weather = None
    try:
        weather = session['weather']
    except:
        current_app.logger.debug("get new weather info")
        weather = get_weather()
        session['weather'] = weather
        session.permanent = True
        current_app.permanent_session_lifetime = timedelta(minutes=60)
    return weather

@seoul_bp.route('/park', methods=['GET', 'POST'])
def park():
    menu = {'ho':0, 'da':1, 'ml':0, 'se':1, 'co':0, 'cg':0, 'cr':0, 'st':0, 'wc':0}
    park_new = pd.read_csv('./static/data/park_info.csv')
    park_gu = pd.read_csv('./static/data/park_gu.csv')
    park_gu.set_index('지역', inplace=True)
    if request.method == 'GET':
        map = folium.Map(location=[37.5502, 126.982], zoom_start=11)
        for i in park_new.index:
            folium.CircleMarker([park_new.lat[i], park_new.lng[i]], 
                                radius=int(park_new['size'][i]),
                                tooltip=f"{park_new['공원명'][i]}({int(park_new.area[i])}㎡)",
                                color='#3186cc', fill_color='#3186cc').add_to(map)
        html_file = os.path.join(current_app.root_path, 'static/img/park.html')
        map.save(html_file)
        mtime = int(os.stat(html_file).st_mtime)
        return render_template('seoul/park.html', menu=menu, weather=get_weather_main(),
                                park_list=list(park_new['공원명'].values), 
                                gu_list = list(park_gu.index), mtime=mtime)
    else:
        gubun = request.form['gubun']
        if gubun == 'name':
            park_name = request.form['name']
            df = park_new[park_new['공원명'] == park_name].reset_index()
            park_result = {'name':park_name, 'addr':df['공원주소'][0], 'area':df.area[0], 'desc':df['공원개요'][0]}
            
            current_app.logger.debug(f"get park data: {gubun}, {park_name}")
            
            map = folium.Map(location=[37.5502, 126.982], zoom_start=11)
            for i in park_new.index:
                folium.CircleMarker([park_new.lat[i], park_new.lng[i]], 
                                    radius=int(park_new['size'][i]),
                                    tooltip=f"{park_new['공원명'][i]}({int(park_new.area[i])}㎡)",
                                    color='#3186cc', fill_color='#3186cc').add_to(map)
            folium.CircleMarker([df.lat[0], df.lng[0]], radius=int(df['size'][0]),
                                    tooltip=f"{df['공원명'][0]}({int(df.area[0])}㎡)",
                                    color='crimson', fill_color='crimson').add_to(map)
            html_file = os.path.join(current_app.root_path, 'static/img/park_res.html')
            map.save(html_file)
            mtime = int(os.stat(html_file).st_mtime)
            return render_template('seoul/park_res.html', menu=menu, weather=get_weather_main(),
                                    park_result=park_result, mtime=mtime)
        else:
            gu_name = request.form['gu']
            df = park_gu[park_gu.index == gu_name].reset_index()
            park_result2 = {'gu':gu_name, 'gu_area':df['구면적'][0], 
                            'park_area':df['공원면적'][0], 
                            'park_cnt':df['공원수'][0]}
            select_gu = park_new[park_new['지역'] == gu_name]

            current_app.logger.debug(f"get park data: {gubun}, {gu_name}")

            map = folium.Map(location=[select_gu['lat'].mean(), select_gu['lng'].mean()], zoom_start=12)
            for i in select_gu.index:
                folium.CircleMarker([select_gu.lat[i], select_gu.lng[i]], 
                                    radius=int(select_gu['size'][i])*2,
                                    tooltip=f"{select_gu['공원명'][i]}({int(select_gu.area[i])}㎡)",
                                    color='#3186cc', fill_color='#3186cc').add_to(map)
            html_file = os.path.join(current_app.root_path, 'static/img/park_res.html')
            map.save(html_file)
            mtime = int(os.stat(html_file).st_mtime)
            return render_template('seoul/park_res2.html', menu=menu, weather=get_weather_main(),
                                    park_result=park_result2, mtime=mtime)

@seoul_bp.route('/park_gu/<option>')
def park_gu(option):
    menu = {'ho':0, 'da':1, 'ml':0, 'se':1, 'co':0, 'cg':0, 'cr':0, 'st':0, 'wc':0}
    park_new = pd.read_csv('./static/data/park_info.csv')
    park_gu = pd.read_csv('./static/data/park_gu.csv')
    park_gu.set_index('지역', inplace=True)
    geo_path = './static/data/skorea_municipalities_geo_simple.json'
    geo_str = json.load(open(geo_path, encoding='utf-8'))
    option_dict = {
        'area':'공원면적', 'count':'공원수', 
        'area_ratio':'공원면적 비율', 'per_person':'인당 공원면적'
    }
    columns = option_dict[option].replace(' ', '')
    current_app.logger.debug(f"get park_gu data: {option_dict[option]}")

    map = folium.Map(location=[37.5502, 126.982], zoom_start=11, tiles='Stamen Toner')
    map.choropleth(geo_data = geo_str,
                    data = park_gu[columns],
                    columns = [park_gu.index, park_gu[columns]],
                    fill_color = 'PuRd',
                    key_on = 'feature.id')

    for i in park_new.index:
        folium.CircleMarker([park_new.lat[i], park_new.lng[i]], 
                        radius=int(park_new['size'][i]),
                        tooltip=f"{park_new['지역'][i]}-{park_new['공원명'][i]}({int(park_new.area[i])}㎡)",
                        color='blue', fill_color='blue').add_to(map)
    html_file = os.path.join(current_app.root_path, 'static/img/park_gu.html')
    map.save(html_file)
    mtime = int(os.stat(html_file).st_mtime)
    return render_template('seoul/park_gu.html', menu=menu, weather=get_weather_main(),
                            option=option, option_dict=option_dict, mtime=mtime)

@seoul_bp.route('/crime/<option>')
def crime(option):
    menu = {'ho':0, 'da':1, 'ml':0, 'se':1, 'co':0, 'cg':0, 'cr':0, 'st':0, 'wc':0}
    crime = pd.read_csv('./static/data/crime_result.csv')
    crime.set_index('구별', inplace=True)
    geo_path = './static/data/skorea_municipalities_geo_simple.json'
    geo_str = json.load(open(geo_path, encoding='utf-8'))
    option_dict = {
        'crime':'범죄 발생 건수', 'murder':'살인 발생 건수', 
        'rob':'강도 발생 건수', 'rape':'강간 발생 건수',
        'thief':'절도 발생 건수', 'force':'폭력 발생 건수',
        'a_crime':'범죄검거율', 'a_murder':'살인검거율', 
        'a_rob':'강도검거율', 'a_rape':'강간검거율',
        'a_thief':'절도검거율', 'a_force':'폭력검거율'
    }
    columns = option_dict[option].split()[0]
    current_app.logger.debug(f"get crime data: {option_dict[option]}")

    map = folium.Map(location=[37.5502, 126.982], zoom_start=11)
    if option in ['crime', 'murder', 'rob', 'rape', 'thief', 'force']:
        map.choropleth(
            geo_data = geo_str,
            data = crime[columns],
            columns = [crime.index, crime[columns]],
            fill_color = 'PuRd',
            key_on = 'feature.id'
        )
    else:
        map.choropleth(
            geo_data = geo_str,
            data = crime[columns],
            columns = [crime.index, crime[columns]],
            fill_color = 'YlGn',
            key_on = 'feature.id'
        )

    html_file = os.path.join(current_app.root_path, 'static/img/crime.html')
    map.save(html_file)
    mtime = int(os.stat(html_file).st_mtime)
    return render_template('seoul/crime.html', menu=menu, weather=get_weather_main(),
                            option=option, option_dict=option_dict, mtime=mtime)

@seoul_bp.route('/cctv/<option>')
def cctv(option):
    menu = {'ho':0, 'da':1, 'ml':0, 'se':1, 'co':0, 'cg':0, 'cr':0, 'st':0, 'wc':0}
    df = pd.read_csv('./static/data/cctv.csv')
    df.set_index('구별', inplace=True)
    df_sort = df.sort_values('오차', ascending=False)

    if option == 'graph':
        fp1 = np.polyfit(df['인구수'], df['소계'], 1)
        fx = np.array([100000, 700000])
        f1 = np.poly1d(fp1)
        fy = f1(fx)

        plt.figure(figsize=(12,8))
        plt.scatter(df['인구수'], df['소계'], c=df['오차'], s=50)
        plt.plot(fx, fy, ls='dashed', lw=3, color='g')

        for i in range(10): 
            plt.text(df_sort['인구수'][i]+5000, df_sort['소계'][i]-50,
                    df_sort.index[i], fontsize=15)

        plt.grid(True)
        plt.title('인구수와 CCTV 개수의 관계', fontsize=20)
        plt.xlabel('인구수')
        plt.ylabel('CCTV의 수')
        plt.colorbar()
        img_file = os.path.join(current_app.root_path, 'static/img/cctv.png')
        plt.savefig(img_file)
        mtime = int(os.stat(img_file).st_mtime)

        return render_template('seoul/cctv.html', menu=menu, weather=get_weather_main(), 
                                mtime=mtime)

    else:
        tbl = []
        for i in range(25):
            row =  {'idx':df.index[i], 'number':df['소계'][i], 'inc':df['최근증가율'][i], 
                    'population':df['인구수'][i], 'ratio':df['cctv비율'][i]}
            tbl.append(row)
        return render_template('seoul/cctv_table.html', menu=menu, weather=get_weather_main(), 
                                tbl=tbl)