# Point d'entree principal - Generation du dashboard de previsions surf
import pandas as pd
import shutil
import os
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from webscrapping import load_data_all as aggregator
from config import (
    REGIONS, REGION_ORDER, DEFAULT_REGION,
    SURF_FORECAST_BASE_URL, OUTPUT_DIR, WIND_QUALITY
)


def spot_link(spot: str) -> str:
    """
    Construit un lien cliquable vers la page surf-forecast.com d'un spot.

    Args:
        spot: Nom du spot (slug URL surf-forecast)

    Returns:
        Balise <a> HTML pointant vers la prevision du spot
    """
    url = SURF_FORECAST_BASE_URL.format(spot=spot)
    return f"<a href='{url}' target='_blank'>{spot}</a>"


def rating_to_stars(rating: int) -> str:
    """
    Convertit un rating numerique en symboles etoiles.

    Args:
        rating: Note de 0 a 5

    Returns:
        Chaine d'etoiles ou vide si rating <= 0
    """
    if rating > 0:
        return '\u2605' * rating  # Unicode star
    return ''


def format_wave_info(height: float, period: int) -> str:
    """
    Formate les informations de houle pour l'affichage.

    Args:
        height: Hauteur en metres
        period: Periode en secondes

    Returns:
        Chaine formatee (ex: "1.5m 12s")
    """
    if height <= 0:
        return '-'
    if period > 0:
        return f"{height}m // {period}s"
    return f"{height}m"


def format_wind(speed, state: str, direction: str = '') -> tuple:
    """
    Formate les informations de vent pour l'affichage.

    Args:
        speed: Vitesse du vent
        state: Etat du vent (Offshore, Onshore, Cross-on, Cross-off, Glass)
        direction: Direction (N, NE, SO...) optionnelle

    Returns:
        Tuple (label, css_class). Ex: ("Offshore // 15 (NE)", "wind-good").
        ("-", "wind-na") si aucune donnee de vent exploitable.
    """
    state = (state or '').strip()
    try:
        speed = int(round(float(speed)))
    except (TypeError, ValueError):
        speed = 0

    if not state and speed == 0:
        return ('-', 'wind-na')

    css_class = WIND_QUALITY.get(state, 'wind-na')

    parts = []
    if state:
        parts.append(state)
    parts.append(str(speed))
    label = ' // '.join(parts)

    direction = (direction or '').strip()
    if direction:
        label = f"{label} ({direction})"

    return (label, css_class)


def build_slots(df: pd.DataFrame) -> list:
    """
    Construit la liste des creneaux a afficher a partir du DataFrame brut.

    Chaque creneau (un horaire d'une journee) regroupe tous les spots: une ligne
    resume (meilleur spot + son vent/houle) et le detail de tous les spots tries
    par note decroissante.

    Args:
        df: DataFrame brut des previsions (tous les spots, cf. load_data_all)

    Returns:
        Liste de dicts, un par creneau, tries chronologiquement. Chaque dict:
        {key, date, time, rating, rating_stars, spots, wave_info,
         wind_label, wind_class, detail: [{spot, rating, rating_stars,
         wave_info, wind_label, wind_class}, ...]}
    """
    if df is None or df.empty:
        return []

    df = df.copy()

    # Colonnes supplementaires si absentes (compatibilite)
    for col in ['wave_height', 'wave_dir', 'period', 'wind_speed', 'wind_dir', 'wind_state']:
        if col not in df.columns:
            df[col] = 0 if col in ['wave_height', 'period', 'wind_speed'] else ''

    slots = []
    # groupby conserve l'ordre de tri par 'key' (sort=False) deja applique en amont
    for key, group in df.groupby('key', sort=True):
        # Tri des spots du creneau par note decroissante
        group = group.sort_values('rating', ascending=False)

        # Detail: tous les spots du creneau
        detail = []
        for _, row in group.iterrows():
            wind_label, wind_class = format_wind(
                row['wind_speed'], row['wind_state'], row['wind_dir']
            )
            detail.append({
                'spot': spot_link(row['spot']),
                'rating': int(row['rating']),
                'rating_stars': rating_to_stars(int(row['rating'])),
                'wave_info': format_wave_info(row['wave_height'], row['period']),
                'wind_label': wind_label,
                'wind_class': wind_class,
            })

        # Resume: meilleur(s) spot(s) du creneau
        best_rating = int(group['rating'].max())
        best_rows = group[group['rating'] == best_rating]
        best = best_rows.iloc[0]

        # Noms des meilleurs spots (blanchis si rating invalide: 0 ou -1)
        if best_rating > 0:
            spots_html = ' <br> '.join(spot_link(s) for s in best_rows['spot'])
        else:
            spots_html = ''

        wind_label, wind_class = format_wind(
            best['wind_speed'], best['wind_state'], best['wind_dir']
        )

        slots.append({
            'key': key,
            'date': pd.to_datetime(best['date']).strftime('%d/%m/%Y'),
            'time': best['time'],
            'rating': best_rating,
            'rating_stars': rating_to_stars(best_rating),
            'spots': spots_html,
            'wave_info': format_wave_info(
                best_rows['wave_height'].max(), best_rows['period'].max()
            ),
            'wind_label': wind_label,
            'wind_class': wind_class,
            'detail': detail,
        })

    return slots


def find_best_session(slots: list) -> dict:
    """
    Trouve la meilleure session (rating le plus eleve) parmi les creneaux.

    Args:
        slots: Liste des creneaux (cf. build_slots)

    Returns:
        Dictionnaire avec les infos de la meilleure session
    """
    valid = [s for s in slots if s['rating'] > 0]
    if not valid:
        return {'date': '-', 'time': '-', 'rating': '-', 'spots': '-'}

    best = max(valid, key=lambda s: s['rating'])
    return {
        'date': best['date'],
        'time': best['time'],
        'rating': best['rating_stars'],
        'spots': best['spots'],
    }


def generate_html(slots: list, best_session: dict,
                  region_key: str, all_regions: dict) -> str:
    """
    Genere le HTML final a partir du template et des donnees.

    Args:
        slots: Liste des creneaux a afficher (cf. build_slots)
        best_session: Infos sur la meilleure session
        region_key: Cle de la region actuelle
        all_regions: Dictionnaire de toutes les regions

    Returns:
        Contenu HTML complet
    """
    # Configuration Jinja2
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('index.html')

    region_info = all_regions[region_key]

    # Preparation des donnees des regions pour le selecteur
    regions_list = []
    for key in REGION_ORDER:
        reg = all_regions[key]
        regions_list.append({
            'key': key,
            'name': reg['name'],
            'url': 'index.html' if key == DEFAULT_REGION else f"{reg['slug']}.html",
            'is_current': key == region_key
        })

    # Rendu du template
    html_output = template.render(
        title=f"Go To Surf - {region_info['name']}",
        heading="Go To Surf",
        region_name=region_info['name'],
        regions=regions_list,
        current_region=region_key,
        last_update=datetime.now().strftime('%d/%m/%Y %H:%M'),
        best_session=best_session,
        slots=slots
    )

    return html_output


def process_region(region_key: str, all_regions: dict) -> tuple:
    """
    Traite une region complete: chargement des donnees et generation HTML.

    Args:
        region_key: Cle de la region a traiter
        all_regions: Dictionnaire de toutes les regions

    Returns:
        Tuple (html_content, output_filename)
    """
    region = all_regions[region_key]
    spots = region['spots']

    print(f"Traitement de {region['name']} ({len(spots)} spots)...")

    # Recuperation des donnees
    forecast_df = aggregator.load_data_all(spots)

    if forecast_df.empty:
        print(f"  Attention: Aucune donnee pour {region['name']}")
        slots = []
        best_session = {'date': '-', 'time': '-', 'rating': '-', 'spots': '-'}
    else:
        print(f"  {len(forecast_df)} previsions recuperees")
        slots = build_slots(forecast_df)
        best_session = find_best_session(slots)

    # Generation du HTML
    html_content = generate_html(slots, best_session, region_key, all_regions)

    # Nom du fichier de sortie
    if region_key == DEFAULT_REGION:
        output_filename = 'index.html'
    else:
        output_filename = f"{region['slug']}.html"

    return html_content, output_filename


def main():
    """Fonction principale d'execution."""
    print("=" * 50)
    print("Generation du dashboard de previsions surf")
    print("=" * 50)

    # Creer le dossier de sortie si necessaire
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Traiter chaque region
    for region_key in REGION_ORDER:
        html_content, output_filename = process_region(region_key, REGIONS)

        # Ecriture du fichier de sortie
        output_path = Path(OUTPUT_DIR) / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"  -> {output_path}")

    # Copie du CSS dans le dossier de sortie
    css_source = Path('templates/styles.css')
    css_dest = Path(OUTPUT_DIR) / 'styles.css'
    if css_source.exists():
        shutil.copy(css_source, css_dest)
        print(f"\nCSS copie: {css_dest}")

    print("\n" + "=" * 50)
    print("Generation terminee!")
    print("=" * 50)


if __name__ == '__main__':
    main()
