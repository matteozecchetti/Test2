from google.cloud import firestore
import pandas as pd
import numpy as np
from random import randint

db = firestore.Client.from_service_account_json('credentials.json')

# legge il csv contatori con lat long
contatori = pd.read_csv("contatori.csv", sep=",")

markers = ""

# recupero la collection last e mi salvo gli stati attuali per ogni codice contatore, assegnando i colori
stati = {}
for doc in db.collection('last').stream():
    #print(f'{doc.id} --> {doc.to_dict()}')
    if doc.to_dict()["portata"] > 0:
        stati[doc.id] = "green"
    elif doc.to_dict()["portata"] == 0:
        stati[doc.id] = "black"
    else:
        stati[doc.id] = "red"

# crea la string per ottenere i marker, mettendo anche un colore casuale tra i 3
for item, row in contatori.iterrows():
    markers += "L.marker(["+str(row.lat)+", "+str(row.long) + \
        "], {icon: "+stati[str(int(row.n_serie))] + \
        "Icon}).bindPopup('test').addTo(map)\n"

with open('map.template') as f:
    temp = f.read()
    # modifica il template
    temp = temp.replace("{{markers}}", markers)
    with open("map_test.html", "w") as f:
        # scrive il template in html
        f.write(temp)
    with open("result.txt", "w") as f:
        f.write(temp)

datat = []
for doc in db.collection("71652827").stream():
    x = doc.to_dict()
    if ":" in doc.id:
        datat.append([x["data&ora"], x["temperatura1"]])

print(datat)
