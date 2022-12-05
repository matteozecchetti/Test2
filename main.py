import json
from flask import Flask, request, render_template, redirect, url_for, flash
from json import loads
from base64 import b64decode
from google.cloud import firestore
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from secret import secret_key


class User(UserMixin):
    def __init__(self, username):
        super().__init__()
        self .id = username
        self.username = username


app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key

usersdb = {
    'marco': 'marcomamei',
    'matteo': 'matteozecchetti'
}


login = LoginManager(app)
# se c'è una pagina che richiede il login si viene reindirizzati alla pagina di login
login.login_view = '/static/login.html'


# se lo username è presente nel db degli utenti, crea l'istanza utente
@login.user_loader
def load_user(username):
    if username in usersdb:
        return User(username)
    return None


@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('/'))
    username = request.values['u']
    password = request.values['p']
    # controllo se username e password sono corretti
    if username in usersdb and password == usersdb[username]:
        # creo l'utente
        login_user(User(username))
        # viene registrato il parametro per la pagina a cui provo ad accedere prima di fare il login
        next_page = request.args.get('next')
        if not next_page:
            next_page = '/'
        return redirect(next_page)
    return redirect('/static/login_failed.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/', methods=['GET', 'POST'])
@login_required
def render_map():

    db = firestore.Client.from_service_account_json('credentials.json')
    # recupero la collection last e mi salvo gli stati attuali per ogni codice contatore, assegnando i colori
    stati = {}
    for doc in db.collection('last').stream():
        # print(f'{doc.id} --> {doc.to_dict()}')
        if doc.to_dict()["portata"] == 0:
            stati[doc.id] = "black"
        elif doc.to_dict()["temperatura1"] > doc.to_dict()["temperatura2"]:
            stati[doc.id] = "green"
        else:
            stati[doc.id] = "red"

    # recupero codici e coordinate dei contatori
    contatori = []
    for doc in db.collection("lista contatori").stream():
        coord = doc.to_dict()
        contatori.append([doc.id, coord["lat"], coord["long"]])

    # crea la string per ottenere i marker, mettendo anche un colore casuale tra i 3
    markers = ""
    for c in contatori:
        markers += "L.marker(["+str(c[1])+", "+str(c[2]) + \
            "], {icon: "+stati[str(int(c[0]))] + \
            "Icon}).bindPopup('<div class=\"container-fluid\" style=\"text-align:center;font-size:20px\"><p style=\"font-weight:1000\">"+str(int(c[0]))+"</p><p><a href=\"https://progetto-v3.ew.r.appspot.com/graph/temp/" + \
            str(int(c[0])) + \
            "\">clicca per vedere la scheda</a></p></div>').addTo(map)\n"

    return render_template('map.html', title='Home', markers=markers, username=current_user.username)


def upload_data(msg):
    print("caricamento dati..")
    db = firestore.Client.from_service_account_json('credentials.json')
    data = msg.split("next")
    for d in data:
        if d != "":
            values = d.split("$")
            db.collection(values[0]).document(values[1]).set({
                "data&ora": values[1], "portata": float(values[2]), "temperatura1": float(values[3]), "temperatura2": float(values[4]), "energia": float(values[5]), "potenza": float(values[6]), "volume": float(values[7])
            })
            db.collection("last").document(values[0]).set({
                "data&ora": values[1], "portata": float(values[2]), "temperatura1": float(values[3]), "temperatura2": float(values[4])
            })
    return "OK"


@app.route('/pubsub/push', methods=['POST'])
def pubsub_push():
    print('dati ricevuti', flush=True)
    # carico i dati ricevuti in un dizionario
    dict = loads(request.data.decode('utf-8'))
    msg = b64decode(dict['message']['data']).decode(
        'utf-8')  # leggo il messaggio e viene codificato
    # print(msg)  # dati che vengono inseriti in firestore
    upload_data(msg)
    return "OK", 200


def read_data_temp(metercode):
    db = firestore.Client.from_service_account_json('credentials.json')
    data = []
    temp1 = []
    temp2 = []
    for doc in db.collection(metercode).stream():
        x = doc.to_dict()
        if ":" in doc.id:
            data.append([x["data&ora"], x["temperatura1"],
                        x["temperatura2"]])
            temp1.append(x["temperatura1"])
            temp2.append(x["temperatura2"])

    avg_temp1 = round(sum(temp1)/len(temp1), 2)
    avg_temp2 = round(sum(temp2)/len(temp2), 2)

    lista_contatori = ""
    for doc in db.collection("lista contatori").stream():
        if metercode == str(doc.id):
            lista_contatori = lista_contatori + \
                "<p style=\"color:white;font-size:20px;font-weight:800;background-color:rgb(10, 12, 150);\">"+str(
                    doc.id)+"</p>"
        else:
            lista_contatori = lista_contatori + \
                "<a href=\"https://progetto-v3.ew.r.appspot.com/graph/temp/"+doc.id+"\"1 style=\"text-decoration:none\"><p style=\"color:rgb(10, 12, 150);font-size:20px;font-weight:800;background-color:white;\">"+str(
                    doc.id)+"</p></a>"
    return json.dumps(data), lista_contatori, avg_temp1, avg_temp2


def read_data_port(metercode):
    db = firestore.Client.from_service_account_json('credentials.json')
    data = []
    port = []
    for doc in db.collection(metercode).stream():
        x = doc.to_dict()
        if ":" in doc.id:
            data.append([x["data&ora"], x["portata"]])
            port.append(x['portata'])

    avg_port = round(sum(port)/len(port), 2)
    max_port = round(max(port), 2)
    min_port = round(min(port), 2)

    lista_contatori = ""
    for doc in db.collection("lista contatori").stream():
        if metercode == str(doc.id):
            lista_contatori = lista_contatori + \
                "<p style=\"color:white;font-size:20px;font-weight:800;background-color:rgb(10, 12, 150);\">"+str(
                    doc.id)+"</p>"
        else:
            lista_contatori = lista_contatori + \
                "<a href=\"https://progetto-v3.ew.r.appspot.com/graph/port/"+doc.id+"\"1 style=\"text-decoration:none\"><p style=\"color:rgb(10, 12, 150);font-size:20px;font-weight:800;background-color:white;\">"+str(
                    doc.id)+"</p></a>"
    return json.dumps(data), lista_contatori, avg_port, max_port, min_port


@app.route('/graph/<gtype>/<metercode>', methods=['GET'])
@login_required
def graph(metercode, gtype):
    if gtype == "temp":
        data, lista_contatori, avg_temp1, avg_temp2 = read_data_temp(metercode)
        data = json.loads(data)
        data.insert(0, ['Time', 'Temperatura 1', 'Temperatura 2'])
        return render_template('contatori_temp.html', data=data, lista_contatori=lista_contatori, metercode=metercode, avg_temp1=avg_temp1, avg_temp2=avg_temp2, username=current_user.username)
    else:
        data, lista_contatori, avg_port, max_port, min_port = read_data_port(
            metercode)
        data = json.loads(data)
        data.insert(0, ['Time', 'Portata'])
        return render_template('contatori_port.html', data=data, lista_contatori=lista_contatori, metercode=metercode, avg_port=avg_port, max_port=max_port, min_port=min_port, username=current_user.username)


@app.route('/contatori_temp', methods=['GET'])
@login_required
def contatori_temp():
    db = firestore.Client.from_service_account_json('credentials.json')
    for doc in db.collection("lista contatori").stream():
        url = "/graph/temp/"+str(doc.id)
        return redirect(url)
    return redirect("/")


# esegue il programma
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
