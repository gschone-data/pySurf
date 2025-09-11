import load_data_f as ld
import load_data_all as lda
# x=ld.load_data('La-Sauzaie')
# print(x)



list_spots=['La-Sauzaie','Les-Dunes','Saint-Gilles-Croixde-Vie','Tanchet','La-Baie-Des-Sables','Plage-Des-Granges','Sion']

df=lda.load_data_all(list_spots)
df.to_csv("resfin.csv")