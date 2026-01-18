# Point d'entree principal - Generation du dashboard de previsions surf
import pandas as pd
import shutil
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from webscrapping import load_data_all as aggregator
from config import SURF_SPOTS, OUTPUT_PATH, SURF_FORECAST_BASE_URL


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


def prepare_display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare le DataFrame pour l'affichage HTML.

    Args:
        df: DataFrame brut des previsions

    Returns:
        DataFrame formate pour l'affichage
    """
    # Ajout des liens vers les spots
    display_df = add_spot_links(df)

    # Consolidation: une ligne par creneau avec tous les spots
    display_df = display_df.groupby(['key', 'date', 'time', 'rating'])['spot'].apply(
        lambda x: ' <br> '.join(x)
    ).reset_index()

    # Masquer les spots pour les ratings invalides (0 ou -1)
    display_df.loc[display_df['rating'].isin([-1, 0]), 'spot'] = ''

    # Conversion des ratings en etoiles
    display_df['rating_stars'] = display_df['rating'].apply(rating_to_stars)

    # Formatage de la date
    display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%d/%m/%Y')

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


def generate_html(display_df: pd.DataFrame, best_session: dict) -> str:
    """
    Genere le HTML final a partir du template et des donnees.

    Args:
        display_df: DataFrame formate pour l'affichage
        best_session: Infos sur la meilleure session

    Returns:
        Contenu HTML complet
    """
    # Configuration Jinja2
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('index.html')

    # Selection et renommage des colonnes pour le tableau
    table_df = display_df[['date', 'time', 'rating_stars', 'spot']].copy()
    table_df.columns = ['Date', 'Quand', 'Rating', 'Spots']

    # Generation du tableau HTML
    styled_table = table_df.style.hide(axis='index')
    html_table = styled_table.to_html(index=False)

    # Rendu du template
    html_output = template.render(
        title="Go To Surf Vendee",
        heading="Go To Surf Vendee",
        last_update=datetime.now().strftime('%d/%m/%Y %H:%M'),
        best_session=best_session,
        forecast_table=html_table
    )

    return html_output


def main():
    """Fonction principale d'execution."""
    print("Recuperation des donnees de surf...")

    # Recuperation et traitement des donnees
    forecast_df = aggregator.load_data_all(SURF_SPOTS)

    if forecast_df.empty:
        print("Erreur: Aucune donnee recuperee")
        return

    print(f"Donnees recuperees pour {len(SURF_SPOTS)} spots")

    # Preparation pour l'affichage
    display_df = prepare_display_dataframe(forecast_df)

    # Identification de la meilleure session
    best_session = find_best_session(display_df)

    # Generation du HTML
    html_content = generate_html(display_df, best_session)

    # Ecriture du fichier de sortie
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Copie du CSS dans le dossier de sortie
    css_source = Path('templates/styles.css')
    css_dest = Path('_site/styles.css')
    if css_source.exists():
        shutil.copy(css_source, css_dest)
        print(f"CSS copie: {css_dest}")

    print(f"Dashboard genere: {OUTPUT_PATH}")
    print("ok")


if __name__ == '__main__':
    main()
