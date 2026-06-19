# 🏄 pySurf — Go To Surf

> Dashboard de prévisions de surf pour la côte atlantique française.
> Pour chaque créneau, pySurf compare tous les spots d'une région et met en avant **le meilleur endroit où surfer**.

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Surfing_pictogram.svg/langfr-120px-Surfing_pictogram.svg.png" alt="Surf" width="90">
</p>

<p align="center">
  <a href="https://gschone-data.github.io/pySurf/"><strong>🌊 Voir le site en ligne »</strong></a>
</p>

---

## ✨ Fonctionnalités

- 🗺️ **4 régions** couvertes : Finistère (La Torche), Vendée, Charente-Maritime (La Rochelle), Gironde (Lacanau) — ~38 spots au total.
- ⭐ **Meilleur spot par créneau** : pour chaque demi-journée, le spot le mieux noté est mis en avant (notes en étoiles).
- 🔽 **Lignes dépliables** : cliquez sur un créneau pour voir **tous les spots** de la région à cet horaire, classés par note.
- 💨 **Données de vent détaillées** : type (Offshore / Onshore / Cross…), force et direction, avec **code couleur** (vert = offshore favorable, rouge = onshore défavorable).
- 🌊 **Houle & période** affichées séparément pour chaque créneau.
- 📅 **Séparateurs par jour** pour une lecture claire sur les 7 jours de prévision.
- 📱 **Responsive** : pensé pour le mobile comme pour le bureau.
- ⚙️ **100 % statique** : aucun serveur, aucun backend — du HTML/CSS généré, déployé sur GitHub Pages.

## 🚀 Comment ça marche

pySurf scrape [surf-forecast.com](https://www.surf-forecast.com), sélectionne les meilleures conditions
et génère une page HTML statique par région. Un workflow GitHub Actions relance la génération
**toutes les 3 heures** et à chaque push sur `main`, puis publie le résultat sur GitHub Pages.

Le rendu suit un pipeline en trois étapes :

| Étape | Module | Rôle |
|-------|--------|------|
| 1️⃣ Scraping | `webscrapping/load_data_f.py` | Récupère la prévision 6 jours d'un spot (houle, période, vent…). |
| 2️⃣ Agrégation | `webscrapping/load_data_all.py` | Concatène tous les spots d'une région, reconstruit les dates et les créneaux. |
| 3️⃣ Rendu | `main.py` + `templates/` | Construit les créneaux, choisit le meilleur spot et génère le HTML (Jinja2). |

## 🛠️ Installation & utilisation locale

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Générer le dashboard (effectue des requêtes réseau vers surf-forecast.com)
python main.py
```

Le site est généré dans `_site/` :

- `index.html` — région par défaut (Vendée)
- `finistere.html`, `charente.html`, `gironde.html` — autres régions
- `styles.css`

Ouvrez simplement `_site/index.html` dans votre navigateur.

> ⏳ Une génération complète interroge ~38 spots : c'est lent et dépendant du réseau.

## 🧩 Ajouter une région ou un spot

Tout est centralisé dans **`config.py`** — c'est la seule source de vérité.
Pour ajouter une région ou un spot, éditez uniquement `REGIONS` et `REGION_ORDER`.
Les noms de spots sont les slugs d'URL de surf-forecast (ex. `Pointdela-Torche`, `La-Cotiniere_Ile-D-Oleron`).

```python
REGIONS = {
    'ma-region': {
        'name': 'Ma Region',
        'slug': 'ma-region',
        'spots': ['Mon-Spot-1', 'Mon-Spot-2'],
    },
    # ...
}
REGION_ORDER = ['finistere', 'vendee', 'charente', 'gironde', 'ma-region']
```

## 📁 Structure du projet

```
pySurf/
├── main.py                      # Point d'entrée : génération du dashboard
├── config.py                    # Régions, spots, mappings (source de vérité)
├── webscrapping/
│   ├── load_data_f.py           # Scraping d'un spot
│   └── load_data_all.py         # Agrégation de tous les spots d'une région
├── templates/
│   ├── index.html               # Template Jinja2
│   └── styles.css               # Styles
├── _site/                       # Sortie générée (déployée sur GitHub Pages)
├── .github/workflows/deploy.yaml# CI : génération toutes les 3 h + déploiement
└── requirements.txt
```

## 🎨 Légende du vent

| Couleur | Type | Signification |
|---------|------|---------------|
| 🟢 Vert | Offshore / Glass | Vent de terre — **conditions favorables** |
| 🟩 Vert clair | Cross-off | Vent de travers côté terre — correct |
| 🟠 Orange | Cross / Cross-on | Vent de travers — moyen |
| 🔴 Rouge | Onshore | Vent de mer — **conditions défavorables** |

## 📜 Licence

Distribué sous licence [MIT](LICENSE).

Données issues de [surf-forecast.com](https://www.surf-forecast.com).
