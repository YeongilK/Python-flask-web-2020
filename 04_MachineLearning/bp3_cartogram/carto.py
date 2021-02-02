from flask import Blueprint, render_template, request, session, current_app
from datetime import timedelta, datetime
from werkzeug.utils import secure_filename
import matplotlib as mpl 
import matplotlib.pyplot as plt 
import os, folium, json, logging
import numpy as np 
import pandas as pd 
import pandas_datareader as pdr
from my_util.weather import get_weather

carto_bp = Blueprint('carto_bp', __name__)

menu = {'ho':0, 'da':1, 'ml':0, 
        'se':0, 'co':0, 'cg':1, 'cr':0, 'wc':0,
        'cf':0, 'ac':0, 're':0, 'cu':0, 'nl':0}

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

def drawKorea(targetData, blockedMap, cmapname, save_path):
    draw_korea = pd.read_csv('./static/data/draw_korea.csv')
    BORDER_LINES = [
        [(5, 1), (5,2), (6,2), (6,3), (11,3), (11,0)], # 인천
        [(5,4), (5,5), (2,5), (2,7), (4,7), (4,9), (7,9), 
        (7,7), (9,7), (9,5), (10,5), (10,4), (5,4)], # 서울
        [(1,7), (1,8), (3,8), (3,10), (10,10), (10,7), 
        (12,7), (12,6), (11,6), (11,5), (12, 5), (12,4), (11,4), (11,3)], # 경기
        [(8,10), (8,11), (6,11), (6,12)], # 강원
        [(12,5), (13,5), (13,4), (14,4), (14,5), (15,5), (15,4), (16,4), (16,2)], # 충북
        [(16,4), (17,4), (17,5), (16,5), (16,6), (19,6), 
        (19,5), (20,5), (20,4), (21,4), (21,3), (19,3), (19,1)], # 전북
        [(13,5), (13,6), (16,6)], # 대전
        [(13,5), (14,5)], #세종
        [(21,2), (21,3), (22,3), (22,4), (24,4), (24,2), (21,2)], #광주
        [(20,5), (21,5), (21,6), (23,6)], #전남
        [(10,8), (12,8), (12,9), (14,9), (14,8), (16,8), (16,6)], #충남
        [(14,9), (14,11), (14,12), (13,12), (13,13)], #경북
        [(15,8), (17,8), (17,10), (16,10), (16,11), (14,11)], #대구
        [(17,9), (18,9), (18,8), (19,8), (19,9), (20,9), (20,10), (21,10)], #부산
        [(16,11), (16,13)], #울산
        [(27,5), (27,6), (25,6)],
    ]
    
    datalabel = targetData

    vmin = min(blockedMap[targetData])
    vmax = max(blockedMap[targetData])
    
    mapdata = blockedMap.pivot_table(index='y', columns='x', values=targetData)
    masked_mapdata = np.ma.masked_where(np.isnan(mapdata), mapdata)

    plt.figure(figsize=(9, 11))
    plt.pcolor(masked_mapdata, vmin=vmin, vmax=vmax, cmap=cmapname, edgecolor='#aaaaaa', linewidth=0.5)

    for _, row in draw_korea.iterrows():
        if len(row['ID'].split())==2:
            dispname = '{}\n{}'.format(row['ID'].split()[0],row['ID'].split()[1])
        elif row['ID'][:2]=='고성':
            dispname = '고성'
        else:
            dispname = row['ID']

        if len(dispname.splitlines()[-1]) >= 3:
            fontsize, linespacing = 9.5, 1.5
        else:
            fontsize, linespacing = 11, 1.2
        plt.annotate(dispname, (row['x']+0.5,row['y']+0.5), weight='bold',
            fontsize=fontsize, ha='center', va='center',
            linespacing=linespacing)
    for path in BORDER_LINES:
        ys, xs = zip(*path)
        plt.plot(xs,ys,c='black', lw=1.5)
    plt.gca().invert_yaxis()

    plt.axis('off')
    cb = plt.colorbar(shrink=.1, aspect=10)
    cb.set_label(datalabel)

    plt.tight_layout()
    plt.savefig(save_path)

@carto_bp.route('/extinction', methods=['GET', 'POST'])
def extinction():
    if request.method == 'GET':
        return render_template('cartogram/extinction.html', menu=menu, weather=get_weather_main(),
        item_list=['인구수 계','여성비율','2030 여성비율','고령자 비율', '소멸위기지역'])
    else:
        item = request.form['item']
        f = request.files['csv']
        filename = os.path.join(current_app.root_path, 'static/upload/') + f.filename
        f.save(filename)
        current_app.logger.info(f'Selected item: {item}, Saved file Path: {filename}')

        extinction = pd.read_csv(filename)
        cmap_dict = {'인구수 계': 'Blues', '여성비율': 'PuRd', '2030 여성비율': 'Oranges',
                    '고령자 비율': 'Greens', '소멸위기지역': 'Reds'}

        img_file = os.path.join(current_app.root_path, 'static/img/extinction_res.png')
        drawKorea(item, extinction, cmap_dict[item], img_file)
        mtime = int(os.stat(img_file).st_mtime)

        return render_template('cartogram/extinction_res.html', menu=menu, weather=get_weather_main(),
                                item=item, mtime=mtime)

@carto_bp.route('/coffee', methods=['GET', 'POST'])
def coffee():
    item_list = ['커피지수','스타벅스 매장수','커피빈 매장수','이디야 매장수','빽다방 매장수']
    if request.method == 'GET':
        return render_template('cartogram/coffee.html', menu=menu, weather=get_weather_main(), item_list=item_list)
    else:
        item = request.form['item']
        f = request.files['csv']
        filename = os.path.join(current_app.root_path, 'static/upload/') + f.filename
        f.save(filename)
        current_app.logger.info(f'Selected item: {item}, Saved file Path: {filename}')
        coffee = pd.read_csv(filename, dtype={'스타벅스 매장수':int, '커피빈 매장수':int,
                                                '이디야 매장수':int, '빽다방 매장수':int})

        cmap_dict = {'커피지수': 'RdPu', '스타벅스 매장수': 'Greens', '커피빈 매장수': 'Oranges',
                    '이디야 매장수': 'Blues', '빽다방 매장수': 'Purples'}

        img_file = os.path.join(current_app.root_path, 'static/img/coffee_res.png')
        drawKorea(item, coffee, cmap_dict[item], img_file)
        mtime = int(os.stat(img_file).st_mtime)

        df = coffee.sort_values(by=item, ascending=False)[['ID',item]].reset_index()
        top10 = {}
        for i in range(10):
            top10[df['ID'][i]] = round(df[item][i], 2)

        return render_template('cartogram/coffee_res.html', menu=menu, weather=get_weather_main(),
                                item=item, top10=top10, mtime=mtime)

@carto_bp.route('/burger', methods=['GET', 'POST'])
def burger():
    item_list = ['버거 지수','버거킹 매장수','맥도날드 매장수','KFC 매장수','롯데리아 매장수']
    if request.method == 'GET':
        return render_template('cartogram/burger.html', menu=menu, weather=get_weather_main(), item_list=item_list)
    else:
        item = request.form['item']
        f = request.files['csv']
        filename = os.path.join(current_app.root_path, 'static/upload/') + f.filename
        f.save(filename)
        current_app.logger.info(f'Selected item: {item}, Saved file Path: {filename}')
        burger = pd.read_csv(filename)

        cmap_dict = {'버거 지수': 'RdPu', '버거킹 매장수': 'Greens', '맥도날드 매장수': 'Oranges',
                    'KFC 매장수': 'Blues', '롯데리아 매장수': 'Purples'}

        img_file = os.path.join(current_app.root_path, 'static/img/burger_res.png')
        drawKorea(item, burger, cmap_dict[item], img_file)
        mtime = int(os.stat(img_file).st_mtime)

        df = burger.sort_values(by=item, ascending=False)[['ID',item]].reset_index()
        top10 = {}
        for i in range(10):
            top10[df['ID'][i]] = round(df[item][i], 2)

        return render_template('cartogram/burger_res.html', menu=menu, weather=get_weather_main(),
                                item=item, top10=top10, mtime=mtime)