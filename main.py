import pandas as pd
import numpy as np
import datetime
from webscrapping import load_data_all as lda
from jinja2 import Template
from pretty_html_table import build_table

#liste des spots fixe pour le moment
list_spots=['La-Sauzaie','Les-Dunes','Saint-Gilles-Croixde-Vie','Tanchet','La-Baie-Des-Sables','Plage-Des-Granges','Sion','L-Aubraie','Sauveterre']
# #recupération des données
res=lda.load_data_all(list_spots)
# #solution alternative tests
# res=pd.read_csv('test/res_fin.csv')

#ajout lien du spot
res.loc[:,'spot']="<a href='https://fr.surf-forecast.com/breaks/"+res['spot']+"/forecasts/latest/six_day' target='_blank'>"+res['spot']+"</a>"

#consolidation une ligne par créneau
res_fin=res.groupby(['key','date','time','rating'])['spot'].apply(lambda x: ' <br> '.join(x)).reset_index()

#on enlève les ratings à 0 ou -1 (saturation)
res_fin.loc[res_fin['rating'].isin([-1,0]), 'spot'] = ''
#ajout icone rating
def transform_rating(x):
    if x > 0:
        return '★' * x
    else:
        return ''


res_fin['rating_'] = res_fin['rating'].apply(transform_rating)

#mise en forme date
res_fin['date'] = pd.to_datetime(res_fin['date']).dt.strftime('%d/%m/%Y')
res_fin.sort_values(['key'], inplace=True)
#on stock le max pour le tableau résumé
res_fin_max=res_fin.loc[res_fin['rating'].idxmax()]

#on simplifie le tableau final
res_fin=res_fin[['date', 'time', 'rating_', 'spot']]

res_fin=res_fin.rename(columns={'rating_':'Rating','spot':'Spots','time':'Quand','date':'Date'})

#creation du tableau principal
styled_df = res_fin.style.hide(axis='index')
html_table=styled_df.to_html(index=False)       

#creation du tableau résumé
date_maj = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
html_resume='<table>'
html_resume += f'<tr><td><b>Dernière mise à jour :<b> {date_maj}</td></tr>'
html_resume += f'<tr><td><b>Meilleure session :<b> {res_fin_max["date"]} {res_fin_max["time"]} - {res_fin_max["rating_"]} - Spots : {res_fin_max["spot"]}</td></tr>'
html_resume += f'</table><br>'



#structure de la page html

template_str = """
<!DOCTYPE html>
<html>
<link rel="stylesheet" type="text/css" href="styles.css">
<head>
    <title>{{ title }}</title>
</head>
<body>
<div style="display: flex; align-items: left;">
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Surfing_pictogram.svg/langfr-120px-Surfing_pictogram.svg.png" alt="Go To Surf">
    <h1>{{ heading }}</h1></div>
    """

template_str += html_resume
template_str += html_table


template = Template(template_str)
html_output = template.render(title="Go To Surf Vendée",
                               heading="Go To Surf Vendée")
                               

with open("_site/index.html", "w", encoding="utf8") as f:
    f.write(html_output)

print("ok")