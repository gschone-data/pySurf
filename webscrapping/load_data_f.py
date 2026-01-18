# Fonction pour charger les donnees d'un spot depuis surf-forecast.com
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import pandas as pd
import re
import sys
sys.path.append('..')
from config import SURF_FORECAST_BASE_URL, REQUEST_TIMEOUT


def parse_wave_height(text: str) -> tuple:
    """
    Parse la hauteur de vague depuis le format "1.5W" ou "1.5".

    Args:
        text: Texte contenant hauteur et direction (ex: "1.5W", "2.3WSW")

    Returns:
        Tuple (hauteur_float, direction_string)
    """
    text = text.strip()
    if not text:
        return (0.0, '')

    # Extraire le nombre et la direction
    match = re.match(r'^([\d.]+)\s*([A-Z]*)', text)
    if match:
        height = float(match.group(1))
        direction = match.group(2) if match.group(2) else ''
        return (height, direction)
    return (0.0, '')


def parse_wind(text: str) -> tuple:
    """
    Parse les donnees de vent depuis le format "15E" ou "10ESE".

    Args:
        text: Texte contenant vitesse et direction (ex: "15E", "10ESE")

    Returns:
        Tuple (vitesse_int, direction_string)
    """
    text = text.strip()
    if not text:
        return (0, '')

    # Extraire le nombre et la direction
    match = re.match(r'^(\d+)\s*([A-Z]*)', text)
    if match:
        speed = int(match.group(1))
        direction = match.group(2) if match.group(2) else ''
        return (speed, direction)
    return (0, '')


def translate_wind_state(state: str) -> str:
    """
    Traduit l'etat du vent en francais.

    Args:
        state: Etat du vent en anglais (ex: "offshore", "cross-on")

    Returns:
        Etat traduit en francais
    """
    translations = {
        'offshore': 'Offshore',
        'onshore': 'Onshore',
        'cross-off': 'Cross-off',
        'cross-on': 'Cross-on',
        'glass': 'Glass',
    }
    return translations.get(state.lower().strip(), state)


def load_data(spot: str) -> pd.DataFrame:
    """
    Scrape les donnees de prevision pour un spot de surf.

    Args:
        spot: Nom du spot (ex: 'La-Sauzaie')

    Returns:
        DataFrame avec colonnes: spot, day, time, rating, wave_height, wave_dir,
                                 period, wind_speed, wind_dir, wind_state
        DataFrame vide en cas d'erreur
    """
    url = SURF_FORECAST_BASE_URL.format(spot=spot)
    columns = ['spot', 'day', 'time', 'rating', 'wave_height', 'wave_dir',
               'period', 'wind_speed', 'wind_dir', 'wind_state']
    empty_df = pd.DataFrame(columns=columns)

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

    days_cells = days_row.find_all("td", recursive=False)
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

    times_cells = times_row.find_all("td", recursive=False)
    time_of_day = [time_cell.get_text(strip=True) for time_cell in times_cells]

    # Extraction des ratings
    ratings_elements = soup.find_all('div', {'class': 'star-rating'})
    ratings = [rating_elem.get_text(strip=True) for rating_elem in ratings_elements]

    # Extraction de la hauteur de vague
    wave_height_row = soup.find('tr', {'data-row-name': 'wave-height'})
    wave_heights = []
    wave_dirs = []
    if wave_height_row:
        wave_cells = wave_height_row.find_all("td", recursive=False)
        for cell in wave_cells:
            height, direction = parse_wave_height(cell.get_text(strip=True))
            wave_heights.append(height)
            wave_dirs.append(direction)

    # Extraction de la periode
    periods_row = soup.find('tr', {'data-row-name': 'periods'})
    periods = []
    if periods_row:
        period_cells = periods_row.find_all("td", recursive=False)
        for cell in period_cells:
            try:
                periods.append(int(cell.get_text(strip=True)))
            except ValueError:
                periods.append(0)

    # Extraction du vent
    wind_row = soup.find('tr', {'data-row-name': 'wind'})
    wind_speeds = []
    wind_dirs = []
    if wind_row:
        wind_cells = wind_row.find_all("td", recursive=False)
        for cell in wind_cells:
            speed, direction = parse_wind(cell.get_text(strip=True))
            wind_speeds.append(speed)
            wind_dirs.append(direction)

    # Extraction de l'etat du vent
    wind_state_row = soup.find('tr', {'data-row-name': 'wind-state'})
    wind_states = []
    if wind_state_row:
        wind_state_cells = wind_state_row.find_all("td", recursive=False)
        for cell in wind_state_cells:
            state = translate_wind_state(cell.get_text(strip=True))
            wind_states.append(state)

    # Verification de la coherence des donnees de base
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

    # Ajuster les donnees supplementaires a la meme longueur
    def pad_or_truncate(lst, target_len, default=0):
        if len(lst) < target_len:
            return lst + [default] * (target_len - len(lst))
        return lst[:target_len]

    wave_heights = pad_or_truncate(wave_heights, min_length, 0.0)
    wave_dirs = pad_or_truncate(wave_dirs, min_length, '')
    periods = pad_or_truncate(periods, min_length, 0)
    wind_speeds = pad_or_truncate(wind_speeds, min_length, 0)
    wind_dirs = pad_or_truncate(wind_dirs, min_length, '')
    wind_states = pad_or_truncate(wind_states, min_length, '')

    return pd.DataFrame({
        'spot': spot,
        'day': days,
        'time': time_of_day,
        'rating': ratings,
        'wave_height': wave_heights,
        'wave_dir': wave_dirs,
        'period': periods,
        'wind_speed': wind_speeds,
        'wind_dir': wind_dirs,
        'wind_state': wind_states
    })
