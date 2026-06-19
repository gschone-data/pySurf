# Fonction pour charger les donnees de tous les spots et selectionner les meilleurs par creneau
from webscrapping import load_data_f as scraper
import pandas as pd
import re
from datetime import date, timedelta
import sys
sys.path.append('..')
from config import TIME_MAPPING


def build_date_sequence(day_numbers: list, start_date: date = None) -> list:
    """
    Construit une sequence de dates a partir de numeros de jours.
    Gere automatiquement les transitions de mois.

    Args:
        day_numbers: Liste des numeros de jours (ex: [28, 28, 28, 29, 29, 29, 30, 1, 1, 1])
        start_date: Date de depart (defaut: aujourd'hui)

    Returns:
        Liste de dates correspondantes
    """
    if start_date is None:
        start_date = date.today()

    if not day_numbers:
        return []

    # Trouver la bonne date de depart basee sur le premier jour
    first_day = day_numbers[0]
    tomorrow = start_date + timedelta(days=1)

    if first_day == start_date.day:
        current_date = start_date
    elif first_day == tomorrow.day:
        # Le premier creneau est demain (requete tardive)
        current_date = tomorrow
    else:
        # Fallback: assumer que c'est ce mois-ci
        try:
            current_date = start_date.replace(day=first_day)
        except ValueError:
            # Jour invalide pour ce mois, on utilise aujourd'hui
            current_date = start_date

    dates = [current_date]

    for day in day_numbers[1:]:
        last = dates[-1]
        if day < last.day:
            # Passage au mois suivant (ex: 31 -> 1)
            # Astuce: aller au 1er du mois + 32 jours garantit d'etre dans le mois suivant
            next_month_first = (last.replace(day=1) + timedelta(days=32)).replace(day=1)
            try:
                new_date = next_month_first.replace(day=day)
            except ValueError:
                # Jour invalide (ex: 31 fevrier), on prend le dernier jour du mois
                new_date = next_month_first + timedelta(days=27)
                while new_date.month != next_month_first.month:
                    new_date -= timedelta(days=1)
        elif day == last.day:
            # Meme jour (autre creneau horaire)
            new_date = last
        else:
            # Jour suivant dans le meme mois
            try:
                new_date = last.replace(day=day)
            except ValueError:
                # Jour invalide, on ajoute la difference
                new_date = last + timedelta(days=day - last.day)
        dates.append(new_date)

    return dates


def extract_day_number(day_string: str) -> int:
    """
    Extrait le numero du jour depuis le format surf-forecast.
    Format attendu: "Vendredi19" (nom du jour colle au numero).

    Args:
        day_string: Chaine contenant le jour (ex: "Vendredi19")

    Returns:
        Numero du jour (ex: 19)
    """
    # Recuperer les chiffres de fin de chaine
    match = re.search(r'(\d+)$', str(day_string))
    if match:
        return int(match.group(1))
    # Fallback: jour courant
    return date.today().day


def map_time_to_hour(time_period: str) -> int:
    """
    Convertit une periode de la journee en heure numerique.

    Args:
        time_period: 'matin', 'apres-midi', ou 'soir'

    Returns:
        Heure correspondante (9, 15, ou 18)
    """
    return TIME_MAPPING.get(time_period, 12)  # 12h par defaut


def load_data_all(list_spots: list) -> pd.DataFrame:
    """
    Charge les donnees pour tous les spots et les consolide par creneau.

    Tous les spots sont conserves (aucun filtrage par meilleur rating): le choix
    du meilleur spot et le detail de tous les spots se font a l'affichage
    (cf. build_slots dans main.py).

    Args:
        list_spots: Liste des noms de spots

    Returns:
        DataFrame avec toutes les previsions consolidees, colonnes incluant
        rating (numerique), date, hour, key.
    """
    # Collecte des donnees de tous les spots
    all_data = []
    for spot in list_spots:
        spot_data = scraper.load_data(spot)
        if not spot_data.empty:
            all_data.append(spot_data)

    if not all_data:
        print("Aucune donnee recuperee pour les spots")
        return pd.DataFrame()

    forecast_df = pd.concat(all_data, ignore_index=True)

    # Traitement des ratings
    # '!' indique une saturation/indisponibilite
    forecast_df['rating'] = forecast_df['rating'].replace('!', -1)
    forecast_df['rating'] = pd.to_numeric(forecast_df['rating'], errors='coerce').fillna(0).astype(int)

    # Conversion des periodes en heures
    forecast_df['hour'] = forecast_df['time'].apply(map_time_to_hour)

    # Creation d'un rang temporel pour le tri chronologique
    forecast_df['time_rank'] = forecast_df.groupby('spot').cumcount()
    forecast_df = forecast_df.sort_values('time_rank').reset_index(drop=True)

    # Extraction des numeros de jours et construction des dates
    day_numbers = forecast_df['day'].apply(extract_day_number).tolist()
    dates = build_date_sequence(day_numbers)

    # Attribution des dates
    forecast_df['date'] = pd.to_datetime(dates)

    # Creation de la cle de tri (date + heure)
    forecast_df['key'] = pd.to_datetime(
        forecast_df['date'].dt.strftime('%Y-%m-%d') + ' ' + forecast_df['hour'].astype(str) + ':00:00'
    )

    # Tri par cle temporelle (tous les spots sont conserves)
    forecast_df = forecast_df.sort_values('key')

    # Colonne supplementaire pour reference
    forecast_df['date_time'] = forecast_df['date'].dt.strftime('%Y-%m-%d') + '_' + forecast_df['time']

    return forecast_df
