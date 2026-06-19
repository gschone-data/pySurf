# Fonction pour charger les donnees d'un spot depuis surf-forecast.com
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import pandas as pd
import re
import sys
sys.path.append('..')
from config import SURF_FORECAST_BASE_URL, REQUEST_TIMEOUT


def parse_swell(text: str) -> tuple:
    """
    Parse la houle depuis le format "1.2W9" (hauteur + direction + periode).

    surf-forecast fusionne desormais hauteur, direction et periode dans une
    seule cellule (ligne data-row="swell"). Une cellule vide vaut "—".

    Args:
        text: Texte contenant hauteur, direction et periode (ex: "1.2W9", "2.3WSW11")

    Returns:
        Tuple (hauteur_float, direction_string, periode_int)
    """
    text = text.strip()
    if not text:
        return (0.0, '', 0)

    # Extraire hauteur, direction (lettres) et periode (chiffres de fin)
    match = re.match(r'^([\d.]+)\s*([A-Z]*)\s*(\d+)?', text)
    if match:
        height = float(match.group(1))
        direction = match.group(2) if match.group(2) else ''
        period = int(match.group(3)) if match.group(3) else 0
        return (height, direction, period)
    return (0.0, '', 0)


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
    Normalise l'etat du vent renvoye par surf-forecast.

    Le site utilise des libelles courts (ex: "off", "on", "cross", "glassy")
    en plus des formes "cross-off"/"cross-on". On les ramene a une forme
    canonique stable (cle de WIND_QUALITY dans config.py).

    Args:
        state: Etat du vent brut (ex: "off", "cross-on", "glassy")

    Returns:
        Etat canonique (Offshore, Onshore, Cross, Cross-off, Cross-on, Glass)
    """
    translations = {
        'off': 'Offshore',
        'offshore': 'Offshore',
        'on': 'Onshore',
        'onshore': 'Onshore',
        'cross': 'Cross',
        'cross-shore': 'Cross',
        'cross-off': 'Cross-off',
        'cross-on': 'Cross-on',
        'glass': 'Glass',
        'glassy': 'Glass',
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

    # Helper: cellules de donnees d'une ligne data-row, en ignorant la
    # premiere cellule (en-tete/unite, parfois un <th>) presente sur toutes
    # les lignes sauf 'time'.
    def data_cells(row_name, skip_header=True):
        row = soup.find('tr', {'data-row': row_name})
        if not row:
            return None
        cells = row.find_all(["td", "th"], recursive=False)
        return cells[1:] if skip_header else cells

    # Extraction des jours
    days_cells = data_cells('days')
    if days_cells is None:
        print(f"Structure HTML inattendue pour {spot}: ligne 'days' non trouvee")
        return empty_df

    days = []
    for day_cell in days_cells:
        colspan = int(day_cell.get('colspan', 1))
        # data-day-name a disparu: on conserve le texte brut (ex: "Vendredi19")
        day_name = day_cell.get_text(strip=True)
        for _ in range(colspan):
            days.append(day_name)

    # Extraction des periodes (matin, apres-midi, soir): pas de cellule d'en-tete
    times_cells = data_cells('time', skip_header=False)
    if times_cells is None:
        print(f"Structure HTML inattendue pour {spot}: ligne 'time' non trouvee")
        return empty_df

    time_of_day = [time_cell.get_text(strip=True) for time_cell in times_cells]

    # Extraction des ratings (ligne data-row="rating", echelle 0-10)
    rating_cells = data_cells('rating')
    ratings = [c.get_text(strip=True) for c in rating_cells] if rating_cells else []

    # Extraction de la houle (hauteur + direction + periode fusionnees, ex: "1.2W9")
    swell_cells = data_cells('swell')
    wave_heights = []
    wave_dirs = []
    periods = []
    if swell_cells:
        for cell in swell_cells:
            height, direction, period = parse_swell(cell.get_text(strip=True))
            wave_heights.append(height)
            wave_dirs.append(direction)
            periods.append(period)

    # Extraction du vent
    wind_cells = data_cells('wind')
    wind_speeds = []
    wind_dirs = []
    if wind_cells:
        for cell in wind_cells:
            speed, direction = parse_wind(cell.get_text(strip=True))
            wind_speeds.append(speed)
            wind_dirs.append(direction)

    # Extraction de l'etat du vent
    wind_state_cells = data_cells('wind-state')
    wind_states = []
    if wind_state_cells:
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
