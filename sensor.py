from time import sleep
import pandas as pd
from google.cloud import pubsub_v1
from secret import project_id, topic_name
from google.auth import jwt
import json

print(project_id)

print(topic_name)

# legge il csv
df = pd.read_csv("TEA2.csv", sep=";")

# legge il csv contatori con lat long
contatori = pd.read_csv("contatori.csv", sep=",")
contatori["n_serie"] = contatori["n_serie"].astype(
    int)

# preparazione del dataset
df["Tempo di lettura"] = pd.to_datetime(
    df["Tempo di lettura"], format="%d/%m/%Y %H:%M")
df["Numero di serie del contatore"] = df["Numero di serie del contatore"].astype(
    int)
df = df.sort_values(by="Tempo di lettura", ascending=True)
df_sensor = df.copy()
df_sensor = df_sensor.reset_index()

# passiamo le credenziali per stabilire che l'applicazione è abilitata a interagire con PubSub
service_account_info = json.load(open("credentials.json"))
audience = "https://pubsub.googleapis.com/google.pubsub.v1.Publisher"
credentials = jwt.Credentials.from_service_account_info(
    service_account_info, audience=audience
)
# il sensore crea il publisher client
publisher = pubsub_v1.PublisherClient(credentials=credentials)
# definisco il topic specificando il progetto e l'argomento
topic_path = publisher.topic_path(project_id, topic_name)

try:
    topic = publisher.create_topic(request={"name": topic_path})
    print(f"Created topic: {topic.name}")
except Exception as e:
    print(e)

c = 0

data = ""
# Codice cliente;Numero di serie del contatore;Tempo di lettura;Energia 1 Energia termica;Unità;Portata 1;Unità ;
# Potenza 1;Unità ;Temperatura 1;Unità;Temperatura 2;Unità;Volume 1;Unità

# ogni 5 secondi vengono lette 115 righe del dataset (oridnato per data ed ora)
while (c < 100000):
    data = ""
    for row in df_sensor.truncate(before=c, after=c+114).iterrows():
        data = data + str(row[1]["Numero di serie del contatore"])+"$" + \
            str(row[1]["Tempo di lettura"])+"$" + \
            str(row[1]["Portata 1"]) + "$" + str(row[1]["Temperatura 1"])+"$"+str(row[1]["Temperatura 2"]) + "$" + \
            str(row[1]["Energia 1 Energia termica"])+"$"+str(row[1]
                                                             ["Potenza 1"])+"$"+str(row[1]["Volume 1"]) + "next"

    c = c+115

    data_encoded = data.encode("utf-8")

    # print("ENCODED")
    # print(data_encoded)
    # print("STRING")
    # print(data)

    r = publisher.publish(topic_path, data_encoded)

    sleep(10)
    print("LETTURA FATTA")
