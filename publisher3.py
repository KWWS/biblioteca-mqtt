import paho.mqtt.client as mqtt
import random
import time
import json
import ssl
from dotenv import load_dotenv
import os

# Endereco do broker MQTT da HiveMQ (com TLS)
BROKER = ""
PORT = 8883

# Carrega variaveis do .env
load_dotenv()

# Autenticacao MQTT
username = os.getenv("MQTT_USERNAME_P")
password = os.getenv("MQTT_PASSWORD_P")

# Cria cliente MQTT
client = mqtt.Client(client_id="publisher-biblioteca")
client.username_pw_set(username, password)
client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2)
client.connect(BROKER, PORT)
client.loop_start()

# Gera os topicos dinamicamente para sala1 e sala2
TOPICOS = {}

for sala in range(1, 3):  # salas 1 e 2
    prefixo = f"biblioteca/sala{sala}"
    TOPICOS[sala] = {
        "temperatura": f"{prefixo}/temperatura",
        "umidade": f"{prefixo}/umidade",
        "presenca": f"{prefixo}/presenca",
        "ar_cond": f"{prefixo}/comando/ar-cond",
        "luz": f"{prefixo}/luz",
        "porta": f"{prefixo}/porta/entrada"
    }

try:
    while True:
        for sala in range(1, 3):  # salas 1 e 2
            # Gera valores aleatorios simulados
            temperatura = round(random.uniform(0.0, 40.0), 2)
            umidade = round(random.uniform(20.0, 80.0), 2)
            presenca = random.choice([0, 1])
            comando_porta = random.choice(["abrir", "fechar"])

            # Logica para o ar-condicionado
            if temperatura > 20 or umidade > 50:
                comando_ar = "ligar"
            else:
                comando_ar = "desligar"

            # Logica para a luz
            if presenca == 1:
                estado_luz = "acender"
            else:
                estado_luz = "apagar"

            # Publica nos topicos da sala atual
            client.publish(TOPICOS[sala]["temperatura"], json.dumps({"temperatura": temperatura}), qos=1)
            client.publish(TOPICOS[sala]["umidade"], json.dumps({"umidade": umidade}), qos=1)
            client.publish(TOPICOS[sala]["presenca"], json.dumps({"presenca": presenca}), qos=1)
            client.publish(TOPICOS[sala]["ar_cond"], json.dumps({"comando": comando_ar}), qos=1)
            client.publish(TOPICOS[sala]["luz"], json.dumps({"comando": estado_luz}), qos=1)
            client.publish(TOPICOS[sala]["porta"], json.dumps({"comando": comando_porta}), qos=1)

            print(f"📤 Sala {sala} | Temp: {temperatura}C | Umidade: {umidade}% | Presenca: {presenca} | Ar: {comando_ar} | Luz: {estado_luz}")

        print("📡 Dados enviados para sala1 e sala2.\n")
        time.sleep(5)

except KeyboardInterrupt:
    print("🛑 Encerrado pelo usuario.")
    client.loop_stop()
    client.disconnect()
