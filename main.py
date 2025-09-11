import pandas as pd
import numpy as np
from datetime import date, timedelta

from webscrapping import load_data_all as lda
from jinja2 import Template


list_spots=['La-Sauzaie','Les-Dunes','Saint-Gilles-Croixde-Vie','Tanchet','La-Baie-Des-Sables','Plage-Des-Granges','Sion']
res=lda.load_data_all(list_spots)
#res=pd.read_csv('res_fin.csv')
res.loc[:,'spot']="<a href='https://fr.surf-forecast.com/breaks/"+res['spot']+"/forecasts/latest/six_day' target='_blank'>"+res['spot']+"</a>"

res_fin=res.groupby(['date_time','rating'])['spot'].apply(lambda x: ' \n '.join(x)).reset_index()

res_fin.loc[res_fin['rating'].isin([-1,0]), 'spot'] = ''



title="Go To Surf Vendée"




# Construire un tableau HTML simple
html_table = '<table>'
html_table += '<thead><tr><th>Date</th><th>Spots</th><th>Ratings</th></tr></thead><tbody>'

for _, row in res_fin.iterrows():
    html_table += f"<tr><td>{row['date_time']}</td><td>{row['spot']}</td><td>{row['rating']}</td></tr>"

html_table += '</tbody></table></body></html>'


template_str = """
<!DOCTYPE html>
<html>
<link rel="stylesheet" type="text/css" href="styles.css">
<head>
    <title>{{ title }}</title>
</head>
<body>
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Surfing_pictogram.svg/langfr-120px-Surfing_pictogram.svg.png" alt="Go To Surf">
    <h1>{{ heading }}</h1>
    """
template_str += html_table


template = Template(template_str)
html_output = template.render(title="Go To Surf Vendée",
                               heading="Best Spot par période")
                               

with open("_site/index.html", "w", encoding="utf8") as f:
    f.write(html_output)

print("ok")