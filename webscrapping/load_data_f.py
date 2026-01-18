# Fonction pour charger les donnees d'un spot depuis surf-forecast.com
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import pandas as pd
import sys
sys.path.append('..')
from config import SURF_FORECAST_BASE_URL, REQUEST_TIMEOUT


def load_data(spot: str) -> pd.DataFrame:
    """
    Scrape les donnees de prevision pour un spot de surf.

    Args:
        spot: Nom du spot (ex: 'La-Sauzaie')

    Returns:
        DataFrame avec colonnes: spot, day, time, rating
        DataFrame vide en cas d'erreur
    """
    url = SURF_FORECAST_BASE_URL.format(spot=spot)
    empty_df = pd.DataFrame(columns=['spot', 'day', 'time', 'rating'])

    # Requete HTTP avec gestion d'erreurs
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except RequestException as e:
        print(f"Erreur lors du scraping de {spot}: {e}")
        return empty_df

    soup = BeautifulSoup(response.content, 'html.parser')

    # Extraction des jours
    days_row = soup.find('tr', {'data-row-name': 'days'})
    if not days_row:
        print(f"Structure HTML inattendue pour {spot}: ligne 'days' non trouvee")
        return empty_df

    days_cells = days_row.findChildren("td", recursive=False)
    days = []
    for day_cell in days_cells:
        colspan = int(day_cell.get('colspan', 1))
        day_name = day_cell.get('data-day-name', '')
        for _ in range(colspan):
            days.append(day_name)

    # Extraction des periodes (matin, apres-midi, soir)
    times_row = soup.find('tr', {'data-row-name': 'time'})
    if not times_row:
        print(f"Structure HTML inattendue pour {spot}: ligne 'time' non trouvee")
        return empty_df

    times_cells = times_row.findChildren("td", recursive=False)
    time_of_day = [time_cell.get_text() for time_cell in times_cells]

    # Extraction des ratings
    ratings_elements = soup.find_all('div', {'class': 'star-rating'})
    ratings = [rating_elem.get_text() for rating_elem in ratings_elements]

    # Verification de la coherence des donnees
    min_length = min(len(days), len(time_of_day), len(ratings))
    if min_length == 0:
        print(f"Donnees incompletes pour {spot}")
        return empty_df

    # Troncature si les longueurs different
    if not (len(days) == len(time_of_day) == len(ratings)):
        print(f"Attention: longueurs differentes pour {spot} - days:{len(days)}, times:{len(time_of_day)}, ratings:{len(ratings)}")
        days = days[:min_length]
        time_of_day = time_of_day[:min_length]
        ratings = ratings[:min_length]

    return pd.DataFrame({
        'spot': spot,
        'day': days,
        'time': time_of_day,
        'rating': ratings
    })
