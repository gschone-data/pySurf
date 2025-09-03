import requests
from bs4 import BeautifulSoup
import pandas as pd


url = 'https://fr.surf-forecast.com/breaks/La-Sauzaie/forecasts/latest/six_day'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Extraire les jours

#days_row=soup.find_all('td',{'data-day-name':True})
days_row= soup.find('tr',{'data-row-name':'days'})
days_ = days_row.findChildren("td" , recursive=False)
days = []
#cols=[]
for day in days_:
    # days.append(day['data-day-name'])
    # cols.append(day['colspan'])
    nb_=int(day['colspan'])
    day_=day['data-day-name']
    while nb_ !=0:
        days.append(day_)
        nb_-=1

# Extraction time
times_row=soup.find('tr',{'data-row-name':'time'})
times = times_row.findChildren("td" , recursive=False)
timeofday=[]
for time in times:
    timeofday.append(time.get_text())


# Extraction des ratings

ratings_row = soup.find_all('div',{'class':'star-rating'})

ratings=[]
for rating in ratings_row:
    ratings.append(rating.get_text())

df=pd.DataFrame({'day':days,'time':timeofday,'rating':ratings})
print(df)