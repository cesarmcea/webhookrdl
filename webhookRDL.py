import json
from flask import Flask, request
import requests
from translate import Translator

app = Flask(__name__)
event_start_data = None
event_end_data = None
registroIncidencia = None
fechaHoraInicioIndisponibilidad = None
codigoEstadoIndisponibilidad = None
estadoRespuestaIndisponibilidad = None
idEvento = 0
usuario = "usr_webredes"
clave = "20230710xuldaT%&.@"
tokenAutenticacionSAO = None

def obtener_token(usuario, clave):
    url_login = "https://apim-rutaloa-sicns-dev.azure-api.net/Autenticacion/LoginUsuario"
    headers = {"Content-Type": "application/json"}
    data = {
        "usuario": usuario,
        "clave": clave
    }
    response = requests.post(url_login, json=data, headers=headers)
    response_json = response.json()
    token = response_json.get("tokenAutenticacionSAO")
    return token

def traducir_texto(texto, idioma_origen, idioma_destino):
    translator = Translator(from_lang=idioma_origen, to_lang=idioma_destino)
    traduccion = translator.translate(texto)
    return traduccion

def enviar_datos(token, registro):
    url_envio_datos = "https://apim-rutaloa-sicns-dev.azure-api.net/integracion/EventoConcesion/IngresoEventoDPW"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "usuario": "usr_webredes"
    }
    payload = {
        "ListaEventos": [registro]
    }
    response = requests.post(url_envio_datos, json=payload, headers=headers)
    if response.status_code == 200:
        print("Registro enviado correctamente")
    else:
        print("Error al enviar el registro:", response.text)


@app.route('/webhook', methods=['POST'])
def webhook():
    global event_start_data, event_end_data, fechaHoraInicioIndisponibilidad, codigoEstadoIndisponibilidad, estadoRespuestaIndisponibilidad, idEvento, descripcionIndisponibilidad, tokenAutenticacionSAO

    if not event_start_data:
        event_start_data = request.json
        fechaHoraInicioIndisponibilidad = event_start_data['request_datetime']
        codigoEstadoIndisponibilidad = event_start_data['response_status_code']
        estadoRespuestaIndisponibilidad = event_start_data['response_state']
        descripcionIndisponibilidad = event_start_data.get('response_summary', '')
        
        print("Fecha y hora Inicio Indisponibilidad:", fechaHoraInicioIndisponibilidad)
        print("Codigo de respuesta:", codigoEstadoIndisponibilidad)
        print("Estado de respuesta:", estadoRespuestaIndisponibilidad)
        print("Observación:", descripcionIndisponibilidad)
        return 'Datos de inicio de evento recibidos'
    
    elif not event_end_data:
        event_end_data = request.json
        fechahoraFinIndisponibilidad = event_end_data['request_datetime']
        fechaHoraInicioIndisponibilidad = event_start_data['request_datetime']
        codigoEstadoIndisponibilidad = event_start_data['response_status_code']
        estadoRespuestaIndisponibilidad = event_start_data['response_state']
        descripcionIndisponibilidad = event_start_data.get('response_summary', '')

        global idEvento
        idEvento += 1

        
        idioma_origen = 'en'  
        idioma_destino = 'es'  
        estadoRespuestaIndisponibilidad = traducir_texto(estadoRespuestaIndisponibilidad, idioma_origen, idioma_destino)
        descripcionIndisponibilidad = traducir_texto(descripcionIndisponibilidad, idioma_origen, idioma_destino)

        registroIncidencia = {
            'idEvento': idEvento,
            'fechaHoraInicioIndisponibilidad': fechaHoraInicioIndisponibilidad,
            'fechaHoraFinIndisponibilidad': fechahoraFinIndisponibilidad,
            'tipoIndisponibilidad': 2,
            'observacion': "Código de estado: " + codigoEstadoIndisponibilidad + ", Estado de respuesta: " + estadoRespuestaIndisponibilidad + ', Observación: ' + descripcionIndisponibilidad
        }
        print(registroIncidencia)

        event_start_data = None
        event_end_data = None

        
        tokenAutenticacionSAO = obtener_token(usuario, clave)
        print("Token de autenticación SAO:", tokenAutenticacionSAO)

        
        enviar_datos(tokenAutenticacionSAO, registroIncidencia)
       
    return 'Informe generado correctamente'

if __name__ == '__main__':
    app.run()
