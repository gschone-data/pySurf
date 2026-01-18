# Configuration centralisee pour pySurf

# Liste des spots de surf a surveiller (Vendee)
SURF_SPOTS = [
    'La-Sauzaie',
    'Les-Dunes',
    'Saint-Gilles-Croixde-Vie',
    'Tanchet',
    'La-Baie-Des-Sables',
    'Plage-Des-Granges',
    'Sion',
    'L-Aubraie',
    'Sauveterre'
]

# Mapping des periodes de la journee vers des heures numeriques
TIME_MAPPING = {
    'matin': 9,
    'après-midi': 15,
    'soir': 18
}

# URL de base pour surf-forecast.com
SURF_FORECAST_BASE_URL = 'https://fr.surf-forecast.com/breaks/{spot}/forecasts/latest/six_day'

# Timeout pour les requetes HTTP (en secondes)
REQUEST_TIMEOUT = 10

# Chemin de sortie pour le fichier HTML genere
OUTPUT_PATH = '_site/index.html'

# Chemin du template HTML
TEMPLATE_PATH = 'templates/index.html'
