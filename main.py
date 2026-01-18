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
    SURF_FORECAST_BASE_URL, OUTPUT_DIR
)


def add_spot_links(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute des liens cliquables vers surf-forecast.com pour chaque spot.

    Args:
        df: DataFrame avec une colonne 'spot'

    Returns:
        DataFrame avec les spots transformes en liens HTML
    """
    df = df.copy()
    df['spot'] = df['spot'].apply(
        lambda spot: f"<a href='{SURF_FORECAST_BASE_URL.format(spot=spot)}' target='_blank'>{spot}</a>"
    )
    return df


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


def prepare_display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare le DataFrame pour l'affichage HTML.

    Args:
        df: DataFrame brut des previsions

    Returns:
        DataFrame formate pour l'affichage
    """
    df = df.copy()

    # Ajout des liens vers les spots
    display_df = add_spot_links(df)

    # Colonnes supplementaires si absentes (compatibilite)
    for col in ['wave_height', 'wave_dir', 'period', 'wind_speed', 'wind_dir', 'wind_state']:
        if col not in display_df.columns:
            display_df[col] = 0 if col in ['wave_height', 'period', 'wind_speed'] else ''

    # Agreger par creneau: prendre les moyennes/max pour les donnees meteo
    agg_funcs = {
        'spot': lambda x: ' <br> '.join(x),
        'wave_height': 'max',
        'wave_dir': 'first',
        'period': 'max',
        'wind_speed': 'mean',
        'wind_dir': 'first',
        'wind_state': 'first'
    }

    display_df = display_df.groupby(['key', 'date', 'time', 'rating']).agg(agg_funcs).reset_index()

    # Masquer les spots pour les ratings invalides (0 ou -1)
    display_df.loc[display_df['rating'].isin([-1, 0]), 'spot'] = ''

    # Conversion des ratings en etoiles
    display_df['rating_stars'] = display_df['rating'].apply(rating_to_stars)

    # Formatage de la date
    display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%d/%m/%Y')

    # Formatage des donnees de houle (hauteur + periode uniquement)
    display_df['wave_info'] = display_df.apply(
        lambda row: format_wave_info(row['wave_height'], row['period']),
        axis=1
    )

    # Tri chronologique
    display_df = display_df.sort_values('key')

    return display_df


def find_best_session(df: pd.DataFrame) -> dict:
    """
    Trouve la meilleure session (rating le plus eleve).

    Args:
        df: DataFrame des previsions

    Returns:
        Dictionnaire avec les infos de la meilleure session
    """
    if df.empty:
        return {'date': '-', 'time': '-', 'rating': '-', 'spots': '-'}

    best_row = df.loc[df['rating'].idxmax()]
    return {
        'date': best_row['date'],
        'time': best_row['time'],
        'rating': best_row['rating_stars'],
        'spots': best_row['spot']
    }


def generate_html(display_df: pd.DataFrame, best_session: dict,
                  region_key: str, all_regions: dict) -> str:
    """
    Genere le HTML final a partir du template et des donnees.

    Args:
        display_df: DataFrame formate pour l'affichage
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

    # Selection et renommage des colonnes pour le tableau
    table_df = display_df[['date', 'time', 'rating_stars', 'wave_info', 'spot']].copy()
    table_df.columns = ['Date', 'Quand', 'Rating', 'Houle // Periode ', 'Spots']

    # Generation du tableau HTML
    styled_table = table_df.style.hide(axis='index')
    html_table = styled_table.to_html(index=False)

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
        forecast_table=html_table
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
        # Creer un DataFrame vide avec les bonnes colonnes
        display_df = pd.DataFrame(columns=[
            'key', 'date', 'time', 'rating', 'spot', 'rating_stars', 'wave_info'
        ])
        best_session = {'date': '-', 'time': '-', 'rating': '-', 'spots': '-'}
    else:
        print(f"  {len(forecast_df)} previsions recuperees")
        display_df = prepare_display_dataframe(forecast_df)
        best_session = find_best_session(display_df)

    # Generation du HTML
    html_content = generate_html(display_df, best_session, region_key, all_regions)

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
