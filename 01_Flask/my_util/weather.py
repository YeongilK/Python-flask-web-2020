import requests
from urllib.parse import urlparse

def get_weather():
    key_fd = open('openweatherkey.txt', mode='r')
    oweather_key = key_fd.read(100)
    key_fd.close()

    lat = 37.550966; lng = 126.849532
    url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={oweather_key}&units=metric&lang=kr'
    result = requests.get(urlparse(url).geturl()).json()
    icon = result['weather'][0]['icon']
    desc = result['weather'][0]['description']
    temp = result['main']['temp']
    temp_min = result['main']['temp_min']
    temp_max = result['main']['temp_max']
    return f'''<img src="http://openweathermap.org/img/w/{icon}.png" height="32">
    <strong>{desc}&#8451</strong>, 
    온도: <strong>{temp}</strong>, {temp_min}/{temp_max}&#8451'''
