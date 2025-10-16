from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import ssl
import threading
import json
from dotenv import load_dotenv
import os

app = Flask(__name__)
socketio = SocketIO(app)

BROKER = ""
PORT = 8883

load_dotenv()

username = os.getenv("MQTT_USERNAME_S")
password = os.getenv("MQTT_PASSWORD_S")

# Inscreve em todas as salas possíveis (sala1, sala2, etc.)
TOPICOS = [
    "biblioteca/+/temperatura",
    "biblioteca/+/umidade",
    "biblioteca/+/presenca",
    "biblioteca/+/comando/ar-cond",
    "biblioteca/+/luz",
    "biblioteca/+/porta/entrada"
]

# Guarda os estados individuais por sala
salas = {}

def escolher_imagem(sala):
    """Escolhe a imagem baseada nos estados da sala específica"""
    estado_ar = salas[sala].get("ar", "desligar")
    estado_luz = salas[sala].get("luz", "apagar")

    if estado_ar == "desligar" and estado_luz == "apagar":
        return f"{sala}_imagem1.png"
    elif estado_ar == "ligar" and estado_luz == "apagar":
        return f"{sala}_imagem2.png"
    elif estado_ar == "desligar" and estado_luz == "acender":
        return f"{sala}_imagem3.png"
    elif estado_ar == "ligar" and estado_luz == "acender":
        return f"{sala}_imagem4.png"
    else:
        return f"{sala}_default.png"

# Ao conectar ao broker
def on_connect(client, userdata, flags, rc):
    print("✅ Conectado ao broker:", rc)
    for topico in TOPICOS:
        client.subscribe(topico, qos=1)
        print(f"📡 Inscrito no topico: {topico}")

# Ao receber mensagem MQTT
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
    except:
        print("❌ Erro no payload")
        return

    print(f"📨 Topico: {msg.topic} | Payload: {payload}")

    # Pega o nome da sala do topico (ex: sala1)
    partes = msg.topic.split("/")
    if len(partes) < 3:
        return

    sala = partes[1]
    subtopico = "/".join(partes[2:])  # ex: comando/ar-cond, luz, temperatura, etc.

    # Cria estado inicial se não existir
    if sala not in salas:
        salas[sala] = {
            "ar": "desligar",
            "luz": "apagar"
        }

    # Atualiza estados especificos
    if subtopico == "comando/ar-cond":
        salas[sala]["ar"] = data.get("comando", salas[sala]["ar"])
    elif subtopico == "luz":
        salas[sala]["luz"] = data.get("comando", salas[sala]["luz"])

    # Escolhe imagem para essa sala
    imagem = escolher_imagem(sala)

    # Envia para o frontend via WebSocket
    socketio.emit('mqtt_message', {
        'sala': sala,
        'topic': msg.topic,
        'payload': payload,
        'imagem': imagem,
        'estado_ar': salas[sala]["ar"],
        'estado_luz': salas[sala]["luz"]
    })

# Thread separada para o cliente MQTT
def mqtt_thread():
    client = mqtt.Client(client_id="subscriber-biblioteca")
    client.username_pw_set(username, password)
    client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.loop_forever()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    threading.Thread(target=mqtt_thread).start()
    socketio.run(app, host='0.0.0.0', port=5000, ssl_context=('ssl/cert.pem', 'ssl/key.pem'))
