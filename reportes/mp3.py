import pyttsx3
from datetime import datetime

class TextToSpeech:
    engine: pyttsx3.Engine

    def __init__(self, voice, rate, volume):
        self.engine = pyttsx3.init()
        if voice:
            self.engine.setProperty("voice", voice)
        
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
    
    def list_available_voices(self):
        voices: list = [self.engine.getProperty('voices')]

        for i,voice in enumerate(voices[0]):
            print(f'{i+1} {voice.name}: {voice.languages} ({voice.id})')

    def text_to_speech(self, text, filename="reporte.mp3"):
        self.engine.save_to_file(text, filename)
        self.engine.runAndWait()

def reporte_cita_mp3(cita):
    filename = f"reportes/mp3/REPORTE_MP3_CITA_{cita.pk}.mp3"
    text =  f"INMUEBLES INCAIBO. {fecha_a_texto(str(datetime.now().date()))}. COMPROBANTE EN FORMATO MP3 DE CITA DE VISITA. " 
    text += f"DEBE LLEVAR ESTE COMPROBANTE EL DÍA DE LA CITA PARA SER ADMITIDO EN LA VISITA AL INMUEBLE. "
    text += f"INMUEBLE A VISITAR: {cita.inmueble.nombre}. "
    text += f"SECTOR DEL INMUEBLE: {cita.inmueble.sector.nombre}. "
    text += f"DIRECCIÓN DEL INMUEBLE: {cita.inmueble.ubicacion_detallada}. "
    text += f"FECHA Y HORA: {fecha_a_texto(str(cita.fecha_asignada.date()))} a las {cita.fecha_asignada.hour} horas. "
    text += f"NOMBRE DEL VISITANTE: {cita.persona}. "
    text += f"CÉDULA DEL VISITANTE: {cita.persona.cedula()}. "
    text += f"NOMBRE DEL AGENTE: {cita.inmueble.agente}. "
    text += f"TELÉFONO DEL AGENTE: {cita.inmueble.agente.numero_telefono}. "
    text += f"CORREO DEL AGENTE: {cita.inmueble.agente.usuario_persona.email}. "

    text += f"NÚMERO DE CITA: {cita.pk}. "

    text += f"FIN DEL REPORTE. LA MODIFICACIÓN DE ESTE DOCUMENTO DIGITAL ESTÁ PROHIBIDA."

    TextToSpeech(None, 200, 100).text_to_speech(text, filename)
    return filename

def reporte_compra_mp3(compra):
    filename = f"reportes/mp3/REPORTE_MP3_COMPRA_{compra.pk}.mp3"
    text =  f"INMUEBLES INCAIBO. {fecha_a_texto(str(datetime.now().date()))}. COMPROBANTE EN FORMATO MP3 DE COMPRA DE INMUEBLE. " 
    text += f"NÚMERO DE COMPRA: {compra.pk}. "

    text += f"EL DÍA {fecha_a_texto(str(compra.fecha.date()))} LA PERSONA {compra.comprador.nombre} {compra.comprador.apellido}. "
    text += f"TITULAR DE LA CÉDULA DE IDENTIDAD {compra.comprador.cedula()}. "
    text += f"HA FIRMADO VIRTUALMENTE EL CONTRATO DONDE SE HA COMPROMETIDO A LA COMPRA DEL INMUEBLE. {compra.inmueble.nombre}. "
    text += f"UBICADO EN EL SECTOR {compra.inmueble.sector.nombre}. PARROQUIA {compra.inmueble.sector.parroquia.nombre}. DIRECCIÓN {compra.inmueble.ubicacion_detallada}. "
    text += f"DUEÑO {compra.inmueble.dueno}. TITULAR DE LA CÉDULA DE IDENTIDAD {compra.inmueble.dueno.cedula()}. TELÉFONO {compra.inmueble.dueno.numero_telefono}. "
    text += f"CORREO ELECTRÓNICO {compra.inmueble.dueno.usuario_persona.email}. "
    text += f"AGENTE {compra.inmueble.agente}. TITULAR DE LA CÉDULA DE IDENTIDAD {compra.inmueble.agente.cedula()}. TELÉFONO {compra.inmueble.agente.numero_telefono}. "
    text += f"CORREO ELECTRÓNICO {compra.inmueble.agente.usuario_persona.email}. "

    text += f"EL COMPRADOR HA DECIDIDO COMPRAR EL INMUEBLE EN {compra.inmueble.precio} DÓLARES AMERICANOS SUJETOS A MODIFICACIÓN DE ACUERDO A LO ESTABLECIDO EN CITAS Y ACUERDOS PREVIOS."
    text += f"FIN DEL REPORTE. LA MODIFICACIÓN DE ESTE DOCUMENTO DIGITAL ESTÁ PROHIBIDA."

    TextToSpeech(None, 200, 100).text_to_speech(text, filename)
    return filename

def reporte_compras_mp3(request, compras):
    filename = f"reportes/mp3/REPORTE_MP3_COMPRAS.mp3"
    text =  f"INMUEBLES INCAIBO. {fecha_a_texto(str(datetime.now().date()))}. REPORTE DE COMPRAS DEL USUARIO {request.user.persona}. " 

    for compra in compras:
        text += f"COMPRA NÚMERO {compra.pk}, INMUEBLE {compra.inmueble.nombre}, FECHA {fecha_a_texto(str(compra.fecha.date()))}, "
        text += f"ESTADO {compra.estado_largo()}, PRECIO {compra.inmueble.precio} DÓLARES. "

    text += f"FIN DEL REPORTE. LA MODIFICACIÓN DE ESTE DOCUMENTO DIGITAL ESTÁ PROHIBIDA."

    TextToSpeech(None, 200, 100).text_to_speech(text, filename)
    return filename

def reporte_pagos_compra_mp3(pagos, compra):
    filename = f"reportes/mp3/REPORTE_MP3_PAGOS.mp3"
    text =  f"INMUEBLES INCAIBO. {fecha_a_texto(str(datetime.now().date()))}. REPORTE DE PAGOS DE LA COMPRA {compra.pk}. " 

    text += f"COMPRA NÚMERO {compra.pk}, INMUEBLE {compra.inmueble.nombre}, FECHA {fecha_a_texto(str(compra.fecha.date()))}, "
    text += f"ESTADO {compra.estado_largo()}, PRECIO {compra.inmueble.precio} DÓLARES. "

    text += "LISTA DE PAGOS"

    total_bs = 0
    total_dolar = 0

    for i,pago in enumerate(pagos):
        text += f"PAGO {i+1}, REFERENCIA {pago.referencia}, FECHA {fecha_a_texto(str(pago.fecha.date()))}, "
        text += f"CUENTA {pago.cuenta.banco} {pago.cuenta.numero}, MONTO BOLÍVARES {pago.monto}, "
        text += f"MONTO DÓLARES {round(pago.valor_dolar(), 2)}, ESTADO {pago.estado_largo()}. "

        if(pago.estado == 'A'):
            total_bs += pago.monto
            total_dolar += pago.valor_dolar()

    text += f"MONTO APROBADO EN BOLÍVARES: {total_bs} BOLÍVARES. MONTO APROBADO EN DÓLARES: {total_dolar} DÓLARES."

    text += f"FIN DEL REPORTE. LA MODIFICACIÓN DE ESTE DOCUMENTO DIGITAL ESTÁ PROHIBIDA."

    TextToSpeech(None, 200, 100).text_to_speech(text, filename)
    return filename


def fecha_a_texto(fecha):
    print(fecha)
    texto = f"{fecha.split('-')[2]} de "
    
    mes = int(fecha.split('-')[1])
    if(mes == 1):
        texto += "enero"
    elif(mes == 2):
        texto += "febrero"
    elif(mes == 3):
        texto += "marzo"
    elif(mes == 4):
        texto += "abril"
    elif(mes == 5):
        texto += "mayo"
    elif(mes == 6):
        texto += "junio"
    elif(mes == 7):
        texto += "julio"
    elif(mes == 8):
        texto += "agosto"
    elif(mes == 9):
        texto += "septiembre"
    elif(mes == 10):
        texto += "octubre"
    elif(mes == 11):
        texto += "noviembre"
    elif(mes == 12):
        texto += "diciembre"
    
    texto += f" del {fecha.split('-')[0]}"

    return texto