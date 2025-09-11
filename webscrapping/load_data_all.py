#fonction pour charger les données d'une liste de spot et de ne sélectionner que les meilleurs spots par créneau horaire.
from webscrapping import load_data_f as ld
import pandas as pd
from datetime import date, timedelta


def load_data_all(list_spots):

    # list_spots=['La-Sauzaie','Les-Dunes','Saint-Gilles-Croixde-Vie']#'Tanchet','La-Baie-Des-Sables','Plage-Des-Granges','Sion']
    res=pd.DataFrame()
    for spot in list_spots:
        tmp=ld.load_data(spot)
        res=pd.concat([res,tmp])

    
    #traitement du dataframe
    ##ratings
    res=res.replace('!',-1)
    res['rating']=pd.to_numeric(res['rating'])

    ##gestion clé de tri via la date et l'heure
    ###correction de l'heure
    res['heure_f']=res['time'].case_when(
    [
        (res['time']=="matin",9),
        (res['time']=="après-midi",15),
        (res['time']=="soir",18)
    ]
    )

    ###correction de la date
    today=date.today()

    ####creation premiere clé pour avoir les jours dans le bon ordre
    res['rk_time']=res.groupby(['spot']).cumcount(+1)
    res['key1']=res['rk_time'].astype(str)+'_'+res['day']
    res=res.sort_values('rk_time')

    jours = [int(x.split('_')[1]) for x in res['day']]

    dates = [today]
    for day in jours[1:]:
        last_date = dates[-1]
        if day < last_date.day:
            mois_suivant = last_date.replace(day=1) + timedelta(days=32)
            new_date = mois_suivant.replace(day=day)
        else:
            new_date = last_date.replace(day=day)
        dates.append(new_date)

    ### ajout dates transformées
    res['date'] = pd.to_datetime(dates)

    ## on crée la clé avec la date corrigée et l'heure fictive
    res['key'] = pd.to_datetime(
        res['date'].dt.strftime('%d/%m/%Y') + ' ' + res['heure_f'].astype(str),
        format='%d/%m/%Y %H'
    )


    res.sort_values('key')
    # recupération des lignes avec le meilleur rating
    max_ratings = res.groupby('key')['rating'].transform('max')
    res = res[res['rating'] == max_ratings]

    res['date_time'] = pd.to_datetime(res['date']).dt.strftime('%Y-%m-%d') + '_' + res['time'].astype(str)
    res['lien']=f'https://fr.surf-forecast.com/breaks/{res['spot']}/forecasts/latest/six_day'

    return res


