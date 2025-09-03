import requests
from bs4 import BeautifulSoup

url = 'https://fr.surf-forecast.com/breaks/Les-Dunes/forecasts/latest/six_day'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Extraire les jours
days_row=soup.find_all('td',{'data-day-name':True})
days = []
for day in days_row:
    days.append(day['data-day-name'])