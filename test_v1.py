from random import randint
import pandas as pd

# legge il csv
df = pd.read_csv("TEA2.csv", sep=";")

# lat e long del centro della mappa
lat = 44.698205
long = 10.629942

# creazione dataframe 'contatori' con ogni contatore e lat e long casuali
# contatori = pd.DataFrame(
#    {'n_serie': df["Numero di serie del contatore"].unique()})
#contatori["lat"] = contatori.apply(lambda row: lat+(0.5-random())/100, axis=1)
# contatori["long"] = contatori.apply(
#    lambda row: long+(0.5-random())/100, axis=1)

# contatori.to_csv("contatori.csv")

# legge il csv contatori con lat long
contatori = pd.read_csv("contatori.csv", sep=",")

colori = ["green", "black", "red"]

markers = ""

# crea la string per ottenere i marker, mettendo anche un colore casuale tra i 3
for item, row in contatori.iterrows():
    index = randint(0, 2)
    markers += "L.marker(["+str(row.lat)+", "+str(row.long) + \
        "], {icon: "+colori[index]+"Icon}).addTo(map)\n"

with open('map.template') as f:
    temp = f.read()
    # modifica il template
    temp = temp.replace("{{markers}}", markers)
    with open("map.html", "w") as f:
        # scrive il template in html
        f.write(temp)
    with open("result.txt", "w") as f:
        f.write(temp)
