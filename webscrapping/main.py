import load_data_f as ld
import pandas as pd
import csv

list_spots=['La-Sauzaie','Les-Dunes','Saint-Gilles-Croixde-Vie']#'Tanchet','La-Baie-Des-Sables','Plage-Des-Granges','Sion']
res=pd.DataFrame()
for spot in list_spots:
    tmp=ld.load_data(spot)
    res=pd.concat([res,tmp])

res=res.replace('!',-1)
res['rating']=pd.to_numeric(res['rating'])
res['key']=str(res.index)+res['day']+'_'+res['time']
res.sort_values('key')
res_max = res.groupby('key')['rating'].idxmax()
res_fin=res.loc[res_max,['key','spot','rating']]
res_fin['lien']=f'https://fr.surf-forecast.com/breaks/{res_fin['spot']}/forecasts/latest/six_day'
print(res_fin)


res.to_csv('res.csv')
res_fin.to_csv('res_.csv')