# Configuration centralisee pour pySurf

# Definition des regions avec leurs spots de surf
# Chaque region contient: nom d'affichage, slug URL, liste des spots
REGIONS = {
    'finistere': {
        'name': 'Finistere (La Torche)',
        'slug': 'finistere',
        'spots': [
            'Pointdela-Torche',
            'Penhors',
            'Tronoen',
            'Ste-Anne-La-Palud',
            'La-Palue',
            'Pentrez-Plage',
            'Trez-Hir',
            'Anse-de-Pen-Hat',
            'Plage-de-Mesperleuc',
        ]
    },
    'vendee': {
        'name': 'Vendee',
        'slug': 'vendee',
        'spots': [
            'La-Sauzaie',
            'Les-Dunes',
            'Saint-Gilles-Croixde-Vie',
            'Tanchet',
            'La-Baie-Des-Sables',
            'Plage-Des-Granges',
            'Sion',
            'L-Aubraie',
            'Sauveterre',
            'La-Tranchesur-Mer',
            'Les-Conches',
        ]
    },
    'charente': {
        'name': 'Charente-Maritime (La Rochelle)',
        'slug': 'charente',
        'spots': [
            'La-Couarde-Mer_Ilede-Re',
            'Ile-de-Re-Le-Gouyot',
            'Ile-de-Re-Le-Lizay',
            'Ile-de-Re-Les-Grenettes',
            'Ile-de-Re-Petit-Bec',
            'Ile-de-re-Rivedoux',
            'Oleron-Vert-Bois-Les-Allassins',
            'Les-Huttes',
            'Saint-Trojan_Ile-D-Oleron',
            'La-Cotiniere_Ile-D-Oleron',
        ]
    },
    'gironde': {
        'name': 'Gironde (Lacanau)',
        'slug': 'gironde',
        'spots': [
            'Lacanau-Ocean',
            'Le-Truc-Vert',
            'Le-Grand-Crohot',
            'Carcans-Plage',
            'Hourtin-Plage',
            'Montalivetles-Bains',
            'Le-Porge',
            'Soulacsur-Mer',
        ]
    },
}

# Region par defaut
DEFAULT_REGION = 'vendee'

# Liste de toutes les regions pour l'iteration
REGION_ORDER = ['finistere', 'vendee', 'charente', 'gironde']

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

# Dossier de sortie pour les fichiers HTML generes
OUTPUT_DIR = '_site'

# Chemin du template HTML
TEMPLATE_PATH = 'templates/index.html'
