from flask import Blueprint, render_template, request, session, current_app
from datetime import timedelta, datetime
from fbprophet import Prophet
import pandas as pd 
import pandas_datareader as pdr
import os, folium, json, logging
from my_util.weather import get_weather

stock_bp = Blueprint('stock_bp', __name__)

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


kospi_dict, kosdaq_dict = {}, {}
kospi = pd.read_csv('./static/data/KOSPI.csv', dtype={'종목코드': str})
for i in kospi.index:
    kospi_dict[kospi['종목코드'][i]] = kospi['종목명'][i]
kosdaq = pd.read_csv('./static/data/KOSDAQ.csv', dtype={'종목코드': str})
for i in kosdaq.index:
    kosdaq_dict[kosdaq['종목코드'][i]] = kosdaq['종목명'][i]

@stock_bp.route('/stock', methods=['GET', 'POST'])
def stock():
    menu = {'ho':0, 'da':1, 'ml':0, 'se':0, 'co':0, 'cg':0, 'cr':0, 'st':1, 'wc':0}

    if request.method == 'GET':
        return render_template('stock/stock.html', menu=menu, weather=get_weather(), 
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

        
        df = pd.DataFrame({'ds': stock_data.index, 'y': stock_data.Close})
        df.reset_index(inplace=True)
        try:
            del df['Date']
        except:
            pass

        model = Prophet(daily_seasonality=True)
        model.fit(df)
        future = model.make_future_dataframe(periods=pred_period)
        forecast = model.predict(future)
        
        fig = model.plot(forecast);
        img_file = os.path.join(current_app.root_path, 'static/img/stock.png')
        fig.savefig(img_file)
        mtime = int(os.stat(img_file).st_mtime)

        current_app.logger.debug(f"get stock data: 주가지수: {market}, 종목명: {company}, 종목코드: {code}, 학습기간: {learn_period}년, 예측기간: {pred_period}일")
        return render_template('stock/stock_res.html', menu=menu, weather=get_weather_main(), 
                                mtime=mtime, company=company, code=code)