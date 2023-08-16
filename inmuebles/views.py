from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .models import Parroquia, Sector, Inmueble, Cita, Compra, Edicion, tipos_construccion
from usuarios.models import Persona
from datetime import datetime, timedelta
from reportes.mp3 import reporte_cita_mp3, reporte_compra_mp3, reporte_compras_mp3, reporte_pagos_compra_mp3
from reportes.mp3 import reporte_publicacion_mp3
from reportes.pdfs import generar_pdf
import os
from django.core.files.storage import FileSystemStorage
from django.db.models import Q

# Vistas:

def formulario_inmueble(request):
    # Vista del formulario de creación de inmueble
    if(not request.user.is_authenticated):
        return redirect('/usuarios/login/')

    if(request.method == 'GET'):
        # Construcción del formulario a partir de la plantilla
        context = {}
        context['construcciones'] = ["Casa Individual", "Casa Dúplex", "Casa Tríplex",
            "Casa de Villa", "Apartamento Regular", "Apartamento PentHouse", "Terreno", "Oficina",
            "Edificio"]
        context['parroquias'] = Parroquia.objects.all()
        context['sectores'] = Sector.objects.filter(parroquia__pk = 1)
        return render(request, "formulario_inmueble.html", context=context)
    elif(request.method == 'POST'):
        # Validación de completitud de datos
        nombre = request.POST.get('nombre')
        ano_construccion = request.POST.get('ano')
        tipo_construccion = request.POST.get('tipo_construccion')
        estacionamiento = request.POST.get('estacionamiento')
        tamano = request.POST.get('tamano')
        habitaciones = request.POST.get('habitaciones')
        banos = request.POST.get('banos')
        amueblado = request.POST.get('amueblado')
        descripcion = request.POST.get('descripcion')
        ubicacion_detallada = request.POST.get('ubicacion_detallada') 
        precio = request.POST.get('precio')    
        sector = request.POST.get('sector')
        electricidad = request.POST.get('electricidad')
        agua = request.POST.get('agua')
        internet = request.POST.get('internet')
        aseo = request.POST.get('aseo')
        gas = request.POST.get('gas')
        pisos = request.POST.get('pisos')

        errores = []

        if(not nombre):
            errores.append("Debe especificar un nombre.")
        
        if(not ano_construccion):
            errores.append("Debe especificar un año.")

        if(not tipo_construccion):
            errores.append("Debe especificar un tipo seleccionado.")

        if(not tamano):
            errores.append("Debe especificar tamaño.")

        if(not habitaciones):
            errores.append("Debe especificar habitaciones.")

        if(not banos):
            errores.append("Debe especificar baños.")

        if(not descripcion):
            errores.append("Debe especificar descripción.")

        if(not banos):
            errores.append("Debe especificar baños.")

        if(not ubicacion_detallada):
            errores.append("Debe especificar una ubicación detallada.")

        if(not precio):
            errores.append("Debe especificar un precio.")

        if(not sector):
            errores.append("Debe especificar un sector.")

        # Validación de correcta estructura de datos
        
        if(float(precio) <= 0):
            errores.append("El precio debe ser mayor a cero.")
        
        if(float(tamano) <= 0):
            errores.append("El tamaño debe ser mayor a 0.")
        
        if(float(pisos) <= 0):
            errores.append("Debe de tener al menos un piso.")
        
        if(float(banos) < 0):
            errores.append("El número de baños debe ser positivo o cero.")
        
        if(float(estacionamiento) < 0):
            errores.append("El número de estacionamientos debe ser positivo o cero.")
        
        if(float(habitaciones) < 0):
            errores.append("El número de habitaciones debe ser positivo o cero.")

        # Creación

        if(len(errores) != 0):
            return render(request, 'formulario_inmueble.html', {'errores': errores, 'previo': request.POST})

        Inmueble.objects.create(
            nombre = nombre,
            ano_construccion = ano_construccion,
            tipo_construccion = tipos_construccion[int(tipo_construccion)-1][0],
            estacionamientos = estacionamiento,
            tamano = tamano,
            banos = banos,
            habitaciones = habitaciones,
            amueblado = bool(amueblado),
            descripcion = descripcion,
            ubicacion_detallada = ubicacion_detallada,
            precio = precio,
            agua = bool(agua),
            gas = bool(gas),
            electricidad = bool(electricidad),
            internet = bool(internet),
            aseo = bool(aseo),
            pisos = pisos,
            sector = Sector.objects.filter(parroquia__pk = request.POST['parroquia']).order_by("nombre")[int(sector)-1],
            dueno = request.user.persona if request.user.is_authenticated else Persona.objects.first(),
            agente = Persona.objects.first() #! CAMBIAR PARA UN AGENTE ALEATORIO
        )

        return redirect("/")

def get_sectores(request, id):
    return JsonResponse({'res': list(Sector.objects.filter(parroquia__id = id).order_by('nombre').values())})

def resultados(request):
    if request.method == 'GET':
        resultados = buscar_coincidencias(request.session['busqueda'])
        return render(request, 'resultados.html', context={'resultados': resultados, 'busqueda': request.session['busqueda']})
    elif request.method == 'POST':
        busqueda = request.POST.get('busqueda').strip().lower()
        request.session['busqueda'] = busqueda

        return redirect('/inmuebles/resultados/')

def detallar_inmueble(request, pk):
    inmueble = Inmueble.objects.get(pk=pk)
    if(request.method == 'GET'):
        if(request.user.is_authenticated):
            context={'inmueble': inmueble, 'busqueda': request.session['busqueda'], 'puede_cita': not Cita.objects.filter(persona = request.user.persona, inmueble =inmueble, estado = "E").exists(), 'puede_comprar': Cita.objects.filter(persona = request.user.persona, inmueble =inmueble, estado = "F").exists()}
        else:
            context={'inmueble': inmueble, 'busqueda': request.session['busqueda'], 'puede_cita': False, 'puede_comprar': False}
        
        return render(request, "detalle_inmueble.html", context=context)
    elif(request.method == 'POST'):
        if(request.POST.get('busqueda')):
            busqueda = request.POST.get('busqueda').strip().lower()
            request.session['busqueda'] = busqueda

            return redirect('/inmuebles/resultados/')
        elif(request.POST.get('tipo') == 'pdf'):
            response = generar_pdf(request, 'reporte_publicacion', inmueble, "REPORTE DE INMUEBLE")
            response['Content-Disposition'] = f'attachment; filename=REPORTE_PUBLICACION_{inmueble.pk}.pdf'
            return response
        elif(request.POST.get('tipo') == 'mp3'):
            file_path = reporte_publicacion_mp3(inmueble)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/mp3")
                    response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
                    return response

def aprobar_inmueble(request, pk):
    if request.method == "GET":
        return render(request, 'aprobacion_inmueble.html', context={'inmueble': Inmueble.objects.get(pk = pk),
            'construcciones': tipos_construccion, 'titulo': 'Aprobación del Inmueble'})
    
    elif request.method == "POST":
        print(request.POST)
        nombre = request.POST.get('nombre')
        ano_construccion = request.POST.get('ano')
        tipo_construccion = request.POST.get('tipo_construccion')
        estacionamientos = bool(request.POST.get('estacionamiento'))
        tamano = request.POST.get('tamano')
        habitaciones = request.POST.get('habitaciones')
        banos = request.POST.get('banos')
        amueblado = bool(request.POST.get('amueblado'))
        descripcion = request.POST.get('descripcion')
        ubicacion_detallada = request.POST.get('ubicacion_detallada') 
        precio = request.POST.get('precio')
        comentarios_internos = request.POST.get('comentarios_internos')
        electricidad = bool(request.POST.get('electricidad'))
        agua = bool(request.POST.get('agua'))
        internet = bool(request.POST.get('internet'))
        aseo = bool(request.POST.get('aseo'))
        gas = bool(request.POST.get('gas'))
        pisos = request.POST.get('pisos')

        errores = []

        if(not nombre):
            errores.append("Debe especificar un nombre.")
        
        if(not ano_construccion):
            errores.append("Debe especificar un año.")

        if(not tipo_construccion):
            errores.append("Debe especificar un tipo seleccionado.")

        if(not tamano):
            errores.append("Debe especificar tamaño.")

        if(not habitaciones):
            errores.append("Debe especificar habitaciones.")

        if(not banos):
            errores.append("Debe especificar baños.")

        if(not descripcion):
            errores.append("Debe especificar descripción.")

        if(not banos):
            errores.append("Debe especificar baños.")

        if(not ubicacion_detallada):
            errores.append("Debe especificar una ubicación detallada.")

        if(not precio):
            errores.append("Debe especificar un precio.")

        # Validación de correcta estructura de datos
        
        if(float(precio) <= 0):
            errores.append("El precio debe ser mayor a cero.")
        
        if(float(tamano) <= 0):
            errores.append("El tamaño debe ser mayor a 0.")
        
        if(float(pisos) <= 0):
            errores.append("Debe de tener al menos un piso.")
        
        if(float(banos) < 0):
            errores.append("El número de baños debe ser positivo o cero.")
        
        if(float(estacionamientos) < 0):
            errores.append("El número de estacionamientos debe ser positivo o cero.")
        
        if(float(habitaciones) < 0):
            errores.append("El número de habitaciones debe ser positivo o cero.")

        # Creación

        if(len(errores) != 0):
            return render(request, 'aprobacion_inmuebles.html', 
                {'errores': errores, 'inmueble': Inmueble.objects.get(pk=pk), 'titulo': "Aprobación del Inmueble"})

        inmueble = Inmueble.objects.get(pk=pk)
        inmueble.nombre = nombre
        inmueble.ano_construccion = ano_construccion
        inmueble.tipo_construccion = tipo_construccion
        inmueble.estacionamientos = estacionamientos
        inmueble.tamano = tamano
        inmueble.habitaciones = habitaciones
        inmueble.banos = banos
        inmueble.amueblado = amueblado
        inmueble.descripcion = descripcion
        inmueble.comentarios_internos = comentarios_internos
        inmueble.ubicacion_detallada = ubicacion_detallada
        inmueble.precio = precio
        inmueble.agua = agua
        inmueble.electricidad = electricidad
        inmueble.gas = gas
        inmueble.aseo = aseo
        inmueble.internet = internet
        inmueble.pisos = pisos

        if('aprobado' in request.POST.keys()):
            inmueble.estado = 'A'
        else:
            inmueble.estado = 'D'

        inmueble.save()

        # Guardado de Imágenes
        img = 0
        for file in request.FILES.values():
            ext = "." + file.name.split(".")[1]
            myfile = f"{inmueble.pk}_{img}_" + ext
            
            from django.core.files.storage import default_storage
            if(default_storage.exists(myfile)):
                default_storage.delete(myfile)

            fs = FileSystemStorage()
            fs.save(myfile, file)
            img += 1

        return redirect('/')

def seleccionar_dia_cita(request, pk):
    if(request.method == 'GET'):
        inmueble = Inmueble.objects.get(pk=pk)
        dias_disponibles = []
        fecha = datetime.today() + timedelta(days=1)

        while len(dias_disponibles) < 7:
            if(fecha.weekday() < 5):
                print(fecha.weekday())
                dia_a_comparar = datetime(fecha.year,fecha.month,fecha.day)
                if(inmueble.agente.citas_agente().filter(fecha_asignada = dia_a_comparar).count() < 3):
                    if(request.user.persona.citas_cliente().filter(fecha_asignada = dia_a_comparar).count() < 3):
                        dias_disponibles.append({'fecha': fecha, 
                                                'dia_semana': 'Lunes' if fecha.weekday() == 0 else
                                                'Martes' if fecha.weekday() == 1 else 
                                                'Miércoles' if fecha.weekday() == 2 else
                                                'Jueves' if fecha.weekday() == 3 else 'Viernes'})

            fecha += timedelta(days=1)

        return render(request, 'seleccion_dia_cita.html', context={'dias': dias_disponibles, 'inmueble': inmueble})

    elif(request.method == 'POST'):
        request.session['fecha_cita_escogida'] = request.POST['dia_escogido']
        return redirect(f'/inmuebles/cita/hora/{pk}')

def seleccionar_hora_cita(request, pk):
    if(request.method == "GET"):
        inmueble = Inmueble.objects.get(pk=pk)
        horas_disponibles = []
        fecha = datetime.strptime(request.session['fecha_cita_escogida'], '%d-%m-%Y')

        if(not inmueble.agente.citas_agente().filter(fecha_asignada__day = fecha.day, fecha_asignada__month = fecha.month, fecha_asignada__year = fecha.year, fecha_asignada__hour = 8).exists()):
            if(not request.user.persona.citas_cliente().filter(fecha_asignada__day = fecha.day, fecha_asignada__month = fecha.month, fecha_asignada__year = fecha.year, fecha_asignada__hour = 8).exists()):
                horas_disponibles.append(fecha + timedelta(hours=8))
        
        if(not inmueble.agente.citas_agente().filter(fecha_asignada__day = fecha.day, fecha_asignada__month = fecha.month, fecha_asignada__year = fecha.year, fecha_asignada__hour = 10).exists()):
            if(not request.user.persona.citas_cliente().filter(fecha_asignada__day = fecha.day, fecha_asignada__month = fecha.month, fecha_asignada__year = fecha.year, fecha_asignada__hour = 10).exists()):
                horas_disponibles.append(fecha + timedelta(hours=10))

        if(not inmueble.agente.citas_agente().filter(fecha_asignada__day = fecha.day, fecha_asignada__month = fecha.month, fecha_asignada__year = fecha.year, fecha_asignada__hour = 13).exists()):
            if(not request.user.persona.citas_cliente().filter(fecha_asignada__day = fecha.day, fecha_asignada__month = fecha.month, fecha_asignada__year = fecha.year, fecha_asignada__hour = 13).exists()):
                horas_disponibles.append(fecha + timedelta(hours=13))

        if(not inmueble.agente.citas_agente().filter(fecha_asignada__day = fecha.day, fecha_asignada__month = fecha.month, fecha_asignada__year = fecha.year, fecha_asignada__hour = 16).exists()):
            if(not request.user.persona.citas_cliente().filter(fecha_asignada__day = fecha.day, fecha_asignada__month = fecha.month, fecha_asignada__year = fecha.year, fecha_asignada__hour = 16).exists()):
                horas_disponibles.append(fecha + timedelta(hours=16))

        return render(request, 'seleccion_horas_cita.html', context={'fecha': fecha, 'inmueble': inmueble, 'horas': horas_disponibles})
    elif(request.method == "POST"):
        hora_escogida = datetime.strptime(request.session['fecha_cita_escogida'], '%d-%m-%Y') + timedelta(hours=int(request.POST['hora_escogida']))
        cita = Cita.objects.create(
            compra = None,
            inmueble = Inmueble.objects.get(pk=pk),
            persona = request.user.persona,
            fecha_asignada = hora_escogida
        )

        return redirect(f'/inmuebles/cita/creada/{cita.pk}')

def cita_creada(request, pk):
    cita = Cita.objects.get(pk=pk)
    if(request.method == "GET"):
        return render(request, 'cita_creada.html', context={'cita': cita})
    elif(request.method == "POST"): # REPORTES
        if(request.POST['tipo'] == 'pdf'):
            response = generar_pdf(request, 'comprobante_cita', cita, "Comprobante de Cita")
            response['Content-Disposition'] = f'attachment; filename=COMPROBANTE_CITA_{cita.pk}.pdf'
            return response
        elif(request.POST['tipo'] == 'mp3'):
            file_path = reporte_cita_mp3(cita)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/mp3")
                    response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
                    return response

def comprar_inmueble(request, pk):
    inmueble = Inmueble.objects.get(pk=pk)
    if(request.method == "GET"):
        return render(request, "contrato.html", context={'inmueble': inmueble})
    elif(request.method == "POST"):
        compra = Compra.objects.create(comprador = request.user.persona, inmueble = inmueble)
        inmueble.estado = 'T'
        inmueble.save()

        return redirect(f'/inmuebles/compra_realizada/{compra.pk}/')

def compra_realizada(request, pk):
    compra = Compra.objects.get(pk=pk)
    if(request.method == 'GET'):
        return render(request, "compra_realizada.html", context={'compra': compra})
    elif(request.method == 'POST'):
        if(request.POST['tipo'] == 'mp3'):
            file_path = reporte_compra_mp3(compra)

            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/mp3")
                response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
                return response
        elif(request.POST['tipo'] == 'pdf'):
            response = generar_pdf(request, 'comprobante_compra', compra, "Comprobante de Compra")
            response['Content-Disposition'] = f'attachment; filename=COMPROBANTE_COMPRA_{compra.pk}.pdf'
            return response

def resultados_cita(request, pk):
    cita = Cita.objects.get(pk=pk)

    if(request.method == "GET"):
        return render(request, 'resultados_cita.html', context={'cita': cita})    
    elif(request.method == "POST"):
        resultados = request.POST.get('resultados')
        errores = []

        if(resultados):
            errores.append("Debe de registrarse un resultado de la cita.")

        if(len(errores)):
            return render(request, 'resultados_cita.html', context={'cita': cita, 'errores': errores})

        cita.estado = 'F' if request.POST.get('bien') else 'X'
        cita.resultados = request.POST['resultados']
        cita.save()

        return redirect("/")

def consultar_compras(request):
    compras = Compra.objects.filter(comprador=request.user.persona)

    if(request.method == 'GET'):
        return render(request, 'consultas/consultar_compras.html', context={'compras': compras.order_by('-fecha')})
    elif(request.method == 'POST'):
        if(request.POST.get('compra')): # Comprobante compras en espera
            if(request.POST['tipo'] == 'mp3'):
                file_path = reporte_compra_mp3(compras.get(pk=request.POST['compra']))

                with open(file_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/mp3")
                    response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
                    return response
            elif(request.POST['tipo'] == 'pdf'):
                compra = compras.get(pk=request.POST.get('compra'))
                response = generar_pdf(request, 'comprobante_compra', compra, "Comprobante de Compra")
                response['Content-Disposition'] = f'attachment; filename=COMPROBANTE_COMPRA_{compra.pk}.pdf'
                return response
            
        if(request.POST['tipo'] == 'mp3'):
            file_path = reporte_compras_mp3(request, compras)

            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/mp3")
                response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
                return response
        elif(request.POST['tipo'] == 'pdf'):
            response = generar_pdf(request, 'reporte_compras', compras, "REPORTE DE COMPRAS")
            response['Content-Disposition'] = f'attachment; filename=REPORTE_COMPRAS.pdf'
            return response
    
def consultar_publicaciones(request):
    return render(request, 'consultas/consultar_publicaciones.html', context={'publicaciones': Inmueble.objects.filter(dueno=request.user.persona)})

def consultar_citas(request): # Citas de VISITA
    citas = Cita.objects.filter(persona=request.user.persona)
    if(request.method == 'GET'):
        return render(request, 'consultas/consultar_citas_visita.html', context={'citas': citas})
    elif(request.method == 'POST'):
        cita = Cita.objects.get(pk = request.POST['pk'])
        if(request.POST['tipo'] == 'mp3'):
            file_path = reporte_cita_mp3(cita)

            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/mp3")
                response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
                return response
        elif(request.POST['tipo'] == 'pdf'):
            response = generar_pdf(request, 'comprobante_cita', cita, "COMPROBANTE DE CITA")
            response['Content-Disposition'] = f'attachment; filename=COMPROBANTE_CITA_{cita.pk}.pdf'
            return response

def consultar_ventas(request): # Para USUARIOS NORMALES
    return render(request, 'consultas/consultar_ventas_persona.html', context={'ventas': Compra.objects.filter(inmueble__dueno=request.user.persona)})

def consultar_pagos_ventas(request,pk): # Para USUARIOS NORMALES
    compra = Compra.objects.get(pk=pk)
    return render(request, 'consultas/consultar_pagos_ventas_persona.html', context={'pagos': compra.pagos.order_by('-fecha'), 'compra': compra})

def consultar_pagos_compras(request,pk): # Para USUARIOS NORMALES
    compra = Compra.objects.get(pk=pk)
    pagos = compra.pagos.order_by('-fecha')

    if(request.method == 'GET'):
        return render(request, 'consultas/consultar_pagos_compras_persona.html', context={'pagos': pagos.order_by('-fecha'), 'compra': compra})
    elif(request.method == 'POST'):
        if(request.POST['tipo'] == 'mp3'):
            file_path = reporte_pagos_compra_mp3(pagos, compra)

            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/mp3")
                response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
                return response
        elif(request.POST['tipo'] == 'pdf'):
            response = generar_pdf(request, 'reporte_pagos', pagos, "REPORTE DE PAGOS")
            response['Content-Disposition'] = f'attachment; filename=REPORTE_PAGOS_{compra.pk}.pdf'
            return response

def cancelar_compra(request,pk):
    compra = Compra.objects.get(pk=pk)
    if(request.method == 'GET'):
        return render(request, 'cancelacion/cancelacion_compra.html', context={'compra': compra})
    elif(request.method == 'POST'):
        if(compra.estado == 'E'):
            compra.estado = 'C'
            compra.save()
            return render(request, 'cancelacion/espera_cancelacion_compra.html', context={'compra': compra})

def cancelar_publicacion(request,pk):
    publicacion = Inmueble.objects.get(pk=pk)
    if(request.method == 'GET'):
        return render(request, 'cancelacion/cancelacion_publicacion.html', context={'publicacion': publicacion})
    elif(request.method == 'POST'):
        if(publicacion.estado == 'A' or publicacion.estado == 'R'):
            publicacion.estado = 'C'
            publicacion.save()
            return render(request, 'cancelacion/espera_cancelacion_publicacion.html', context={'publicacion': publicacion})

def cancelar_venta(request,pk):
    venta = Compra.objects.get(pk=pk)
    if(request.method == 'GET'):
        return render(request, 'cancelacion/cancelacion_venta.html', context={'venta': venta})
    elif(request.method == 'POST'):
        if(venta.estado == 'E'):
            venta.estado = 'C'
            venta.save()
            return render(request, 'cancelacion/espera_cancelacion_venta.html', context={'venta': venta})

def editar_inmueble(request, pk):
    inmueble = Inmueble.objects.get(pk=pk)
    if(request.method == 'GET'):
        context = {}
        context['construcciones'] = ["Casa Individual", "Casa Dúplex", "Casa Tríplex",
            "Casa de Villa", "Apartamento Regular", "Apartamento PentHouse", "Terreno", "Oficina",
            "Edificio"]
        context['parroquias'] = Parroquia.objects.all()
        context['sectores'] = Sector.objects.filter(parroquia__pk = 1)
        context['inmueble'] = inmueble

        return render(request,'edicion_inmueble.html',context=context)
    elif(request.method == 'POST'):
        # Validación de completitud de datos
        nombre = request.POST.get('nombre')
        ano_construccion = request.POST.get('ano')
        tipo_construccion = request.POST.get('tipo_construccion')
        estacionamiento = request.POST.get('estacionamiento')
        tamano = request.POST.get('tamano')
        habitaciones = request.POST.get('habitaciones')
        banos = request.POST.get('banos')
        amueblado = request.POST.get('amueblado')
        descripcion = request.POST.get('descripcion')
        ubicacion_detallada = request.POST.get('ubicacion_detallada') 
        precio = request.POST.get('precio')    
        electricidad = request.POST.get('electricidad')
        agua = request.POST.get('agua')
        internet = request.POST.get('internet')
        aseo = request.POST.get('aseo')
        gas = request.POST.get('gas')
        pisos = request.POST.get('pisos')

        errores = []

        if(not nombre):
            errores.append("Debe especificar un nombre.")
        
        if(not ano_construccion):
            errores.append("Debe especificar un año.")

        if(not tipo_construccion):
            errores.append("Debe especificar un tipo seleccionado.")

        if(not tamano):
            errores.append("Debe especificar tamaño.")

        if(not habitaciones):
            errores.append("Debe especificar habitaciones.")

        if(not banos):
            errores.append("Debe especificar baños.")

        if(not descripcion):
            errores.append("Debe especificar descripción.")

        if(not banos):
            errores.append("Debe especificar baños.")

        if(not ubicacion_detallada):
            errores.append("Debe especificar una ubicación detallada.")

        if(not precio):
            errores.append("Debe especificar un precio.")

        # Validación de correcta estructura de datos
        
        if(float(precio) <= 0):
            errores.append("El precio debe ser mayor a cero.")
        
        if(float(tamano) <= 0):
            errores.append("El tamaño debe ser mayor a 0.")
        
        if(float(pisos) <= 0):
            errores.append("Debe de tener al menos un piso.")
        
        if(float(banos) < 0):
            errores.append("El número de baños debe ser positivo o cero.")
        
        if(float(estacionamiento) < 0):
            errores.append("El número de estacionamientos debe ser positivo o cero.")
        
        if(float(habitaciones) < 0):
            errores.append("El número de habitaciones debe ser positivo o cero.")

        # Creación
        if(len(errores) != 0):
            return render(request, 'edicion_inmueble.html', {'errores': errores, 'previo': request.POST})

        inmueble.estado = "E"
        inmueble.save()

        Edicion.objects.create(
            nombre = nombre,
            ano_construccion = ano_construccion,
            tipo_construccion = tipos_construccion[int(tipo_construccion)-1][0],
            estacionamientos = estacionamiento,
            tamano = tamano,
            banos = banos,
            habitaciones = habitaciones,
            amueblado = bool(amueblado),
            descripcion = descripcion,
            ubicacion_detallada = ubicacion_detallada,
            precio = precio,
            agua = bool(agua),
            gas = bool(gas),
            electricidad = bool(electricidad),
            internet = bool(internet),
            aseo = bool(aseo),
            pisos = pisos,
            inmueble = Inmueble.objects.get(pk=pk)
        )

        return redirect("/")

def consultar_asignadas(request):
    if(not request.user.is_authenticated or request.user.persona.cargo != 'A'):
        print("Acceso No autorizado")
        return redirect('/')
    
    return render(request, 'agentes/consultar_asignadas.html', context={'publicaciones': Inmueble.objects.filter(agente = request.user.persona, estado__in = ["A","T","S"])})

def consultar_revision(request):
    if(not request.user.is_authenticated or request.user.persona.cargo != 'A'):
        print("Acceso No autorizado")
        return redirect('/')

    if(request.method == 'GET'):    
        return render(request, 'agentes/consultar_revision.html', context={'publicaciones': Inmueble.objects.filter(agente = request.user.persona, estado__in = ['R','E','C'])})
    elif(request.method == 'POST'):
        inmueble = Inmueble.objects.get(pk=request.POST['pk'])
        inmueble.estado = 'X'
        return redirect('/usuarios/agente')

def consultar_finalizadas(request):
    if(not request.user.is_authenticated or request.user.persona.cargo != 'A'):
        print("Acceso No autorizado")
        return redirect('/')
    
    return render(request, 'agentes/consultar_finalizadas.html', context={'publicaciones': Inmueble.objects.filter(agente = request.user.persona, estado__in = ["X","V","D"])})

def consultar_citas_pendientes(request):
    if(not request.user.is_authenticated or request.user.persona.cargo != 'A'):
        print("Acceso No autorizado")
        return redirect('/')
    
    return render(request, 'agentes/consultar_citas_pendientes.html', 
        context={'citas': Cita.objects.filter((Q(inmueble__agente = request.user.persona) | Q(compra__inmueble__agente = request.user.persona))
            & Q(estado__in = ["E","P"])).order_by('fecha_asignada')})

def consultar_citas_finalizadas(request):
    if(not request.user.is_authenticated or request.user.persona.cargo != 'A'):
        print("Acceso No autorizado")
        return redirect('/')
    
    return render(request, 'agentes/consultar_citas_finalizadas.html', 
        context={'citas': Cita.objects.filter(Q(inmueble__agente = request.user.persona) | Q(compra__inmueble__agente = request.user.persona)
            & Q(estado__in = ["F","X","C"])).order_by('-fecha_asignada')})

def consultar_ventas_cerradas(request):
    if(not request.user.is_authenticated or request.user.persona.cargo != 'A'):
        print("Acceso No autorizado")
        return redirect('/')
    
    return render(request, 'agentes/consultar_ventas_cerradas.html', 
        context={'ventas': Compra.objects.filter(inmueble__agente = request.user.persona, estado__in = ["F","X"]).order_by('fecha')})

def consultar_ventas_revision(request):
    if(not request.user.is_authenticated or request.user.persona.cargo != 'A'):
        print("Acceso No autorizado")
        return redirect('/')
    
    return render(request, 'agentes/consultar_ventas_revision.html', 
        context={'ventas': Compra.objects.filter(inmueble__agente = request.user.persona, estado__in = ["C"]).order_by('fecha')})

def edicion_inmueble_agente(request, pk):
    if(request.method == 'GET'):
        return render(request, 'aprobacion_inmueble.html', context={'inmueble': Inmueble.objects.get(pk = pk),
            'construcciones': tipos_construccion, 'titulo': "Edición del Inmueble"})
    elif(request.method == 'POST'):
        nombre = request.POST.get('nombre')
        ano_construccion = request.POST.get('ano')
        tipo_construccion = request.POST.get('tipo_construccion')
        estacionamientos = bool(request.POST.get('estacionamiento'))
        tamano = request.POST.get('tamano')
        habitaciones = request.POST.get('habitaciones')
        banos = request.POST.get('banos')
        amueblado = bool(request.POST.get('amueblado'))
        descripcion = request.POST.get('descripcion')
        ubicacion_detallada = request.POST.get('ubicacion_detallada') 
        precio = request.POST.get('precio')
        comentarios_internos = request.POST.get('comentarios_internos')
        electricidad = bool(request.POST.get('electricidad'))
        agua = bool(request.POST.get('agua'))
        internet = bool(request.POST.get('internet'))
        aseo = bool(request.POST.get('aseo'))
        gas = bool(request.POST.get('gas'))
        pisos = request.POST.get('pisos')

        print(request.POST)

        errores = []

        if(not nombre):
            errores.append("Debe especificar un nombre.")
        
        if(not ano_construccion):
            errores.append("Debe especificar un año.")

        if(not tipo_construccion):
            errores.append("Debe especificar un tipo seleccionado.")

        if(not tamano):
            errores.append("Debe especificar tamaño.")

        if(not habitaciones):
            errores.append("Debe especificar habitaciones.")

        if(not banos):
            errores.append("Debe especificar baños.")

        if(not descripcion):
            errores.append("Debe especificar descripción.")

        if(not banos):
            errores.append("Debe especificar baños.")

        if(not ubicacion_detallada):
            errores.append("Debe especificar una ubicación detallada.")

        if(not precio):
            errores.append("Debe especificar un precio.")

        # Validación de correcta estructura de datos
        
        if(float(precio) <= 0):
            errores.append("El precio debe ser mayor a cero.")
        
        if(float(tamano) <= 0):
            errores.append("El tamaño debe ser mayor a 0.")
        
        if(float(pisos) <= 0):
            errores.append("Debe de tener al menos un piso.")
        
        if(float(banos) < 0):
            errores.append("El número de baños debe ser positivo o cero.")
        
        if(float(estacionamientos) < 0):
            errores.append("El número de estacionamientos debe ser positivo o cero.")
        
        if(float(habitaciones) < 0):
            errores.append("El número de habitaciones debe ser positivo o cero.")

        # Creación

        if(len(errores) != 0):
            return render(request, 'aprobacion_inmuebles.html', 
                {'errores': errores, 'inmueble': Inmueble.objects.get(pk=pk), 'titulo': "Aprobación del Inmueble"})

        inmueble = Inmueble.objects.get(pk=pk)
        inmueble.nombre = nombre
        inmueble.ano_construccion = ano_construccion
        inmueble.tipo_construccion = tipo_construccion
        inmueble.estacionamientos = estacionamientos
        inmueble.tamano = tamano
        inmueble.habitaciones = habitaciones
        inmueble.banos = banos
        inmueble.amueblado = amueblado
        inmueble.descripcion = descripcion
        inmueble.comentarios_internos = comentarios_internos
        inmueble.ubicacion_detallada = ubicacion_detallada
        inmueble.precio = precio
        inmueble.agua = agua
        inmueble.electricidad = electricidad
        inmueble.gas = gas
        inmueble.aseo = aseo
        inmueble.internet = internet
        inmueble.pisos = pisos
        inmueble.save()

        return redirect('/usuarios/agente/')

def cancelacion_inmueble_agente(request, pk):
    inmueble = Inmueble.objects.get(pk=pk)
    if(request.method == 'GET'):
        return render(request, 'agentes/cancelacion/cancelacion_inmueble.html', context={'inmueble': inmueble})
    elif(request.method == 'POST'):
        inmueble.estado = 'X'
        inmueble.save()
        return redirect('/usuarios/agente/')

def consultar_pagos_venta_activa(request,pk):
    compra = Compra.objects.get(pk=pk)
    pagos = compra.pagos.order_by('-fecha')

    if(request.method == 'GET'):
        return render(request, 'agentes/consultar_pagos_venta_activa.html', context={'pagos': pagos.order_by('-fecha'), 'compra': compra})
    elif(request.method == 'POST'):
        if(request.POST['tipo'] == 'pdf'):
            response = generar_pdf(request, 'reporte_pagos', pagos, "REPORTE DE PAGOS")
            response['Content-Disposition'] = f'attachment; filename=REPORTE_PAGOS_{compra.pk}.pdf'
            return response

def revision_edicion_inmueble(request, pk):
    inmueble = Inmueble.objects.get(pk=pk)
    edicion = inmueble.edicion()

    if(request.method == 'GET'):
        context = {'inmueble': inmueble, 'edicion': edicion}
        return render(request, 'agentes/revision/revision_edicion_inmueble.html', context=context)
    elif(request.method == 'POST'):
        if(request.POST['cambios'] == 'aprobar'):
            inmueble.nombre = edicion.nombre
            inmueble.ano_construccion = edicion.ano_construccion
            inmueble.tipo_construccion = edicion.tipo_construccion
            inmueble.estacionamientos = edicion.estacionamientos
            inmueble.tamano = edicion.tamano
            inmueble.habitaciones = edicion.habitaciones
            inmueble.banos = edicion.banos
            inmueble.amueblado = edicion.amueblado
            inmueble.descripcion = edicion.descripcion
            inmueble.precio = edicion.precio
            inmueble.pisos = edicion.pisos
            inmueble.agua = edicion.agua
            inmueble.electricidad = edicion.electricidad
            inmueble.internet = edicion.internet
            inmueble.gas = edicion.gas
            inmueble.aseo = edicion.aseo
            edicion.estado = 'A'
        else:
            edicion.estado = 'R'

        inmueble.estado = 'A'
        inmueble.save()
        edicion.save()

        return redirect('/usuarios/agente/')

# Funciones Auxiliares:

def buscar_coincidencias(busqueda):
    posibles_inmuebles = None
    busqueda = busqueda.lower().replace("metros cuadrados", "m2").replace("á","a").replace("é","e")
    busqueda = busqueda.replace("í","i").replace("ó", "o").replace("ú","u")

    # Por Ubicación

    for sector in Sector.objects.all():
        if sector.nombre.lower() in busqueda:
            posibles_inmuebles = Inmueble.objects.filter(estado = "A", sector__nombre__icontains = sector.nombre) # Se colocan posibles inmuebles en ese sector
            if posibles_inmuebles.count() != 0:
                break
        
    if not posibles_inmuebles:
        for parroquia in Parroquia.objects.all():
            if parroquia.nombre.lower() in busqueda:
                posibles_inmuebles = Inmueble.objects.filter(estado = "A", sector__parroquia__pk = parroquia.pk)
                if posibles_inmuebles.count() != 0:
                    break

    if(not posibles_inmuebles):
        posibles_inmuebles = Inmueble.objects.filter(estado = "A")

    # Por metros cuadrados
    previo = posibles_inmuebles
    if "m2" in busqueda:
        separado = busqueda.split(" ")
        indice = encuentra_coincidencia(separado, "m2")
        
        if indice != -1:
            if separado[indice - 1].isnumeric():
                posibles_inmuebles = posibles_inmuebles.filter(tamano__gte = separado[indice-1]) if posibles_inmuebles else Inmueble.objects.filter(tamano__gte = separado[indice-1])

    if(not posibles_inmuebles):
        posibles_inmuebles = previo

    # Por baños
    previo = posibles_inmuebles
    if "baños" in busqueda:
        separado = busqueda.split(" ")
        indice = encuentra_coincidencia(separado, "baños")
            
        if indice != -1:
            if separado[indice - 1].isnumeric():
                posibles_inmuebles = posibles_inmuebles.filter(banos__gte = separado[indice-1]) if posibles_inmuebles else Inmueble.objects.filter(banos__gte = separado[indice-1])
    elif "baño" in busqueda:
        separado = busqueda.split(" ")
        indice = encuentra_coincidencia(separado, "baño")
            
        if indice != -1:
            if separado[indice - 1].isnumeric():
                posibles_inmuebles = posibles_inmuebles.filter(banos__gte = separado[indice-1]) if posibles_inmuebles else Inmueble.objects.filter(banos__gte = separado[indice-1])
    
    if(not posibles_inmuebles):
        posibles_inmuebles = previo

    # Por habitaciones
    previo = posibles_inmuebles
    if "habitaciones" in busqueda:
        separado = busqueda.split(" ")
        indice = encuentra_coincidencia(separado, "habitaciones")
            
        if indice != -1:
            if separado[indice - 1].isnumeric():
                posibles_inmuebles = posibles_inmuebles.filter(habitaciones__gte = separado[indice-1]) if posibles_inmuebles else Inmueble.objects.filter(habitaciones__gte = separado[indice-1])
    elif "habitacion" in busqueda:
        separado = busqueda.split(" ")
        indice = encuentra_coincidencia(separado, "habitacion")
            
        if indice != -1:
            if separado[indice - 1].isnumeric():
                posibles_inmuebles = posibles_inmuebles.filter(habitaciones__gte = separado[indice-1]) if posibles_inmuebles else Inmueble.objects.filter(habitaciones__gte = separado[indice-1])
    
    if(not posibles_inmuebles):
        posibles_inmuebles = previo

    # Amueblado
    previo = posibles_inmuebles
    if ("amueblado" in busqueda or "amoblado" in busqueda) and not ("no amueblado" in busqueda or "no amoblado" in busqueda):
        posibles_inmuebles = posibles_inmuebles.filter(amueblado = True)
    elif "no amueblado" in busqueda or "no amoblado" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(amueblado = False)

    if(not posibles_inmuebles):
        posibles_inmuebles = previo

    # Tipo de vivienda:
    previo = posibles_inmuebles
    print("K")
    if "casa" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(tipo_construccion__icontains = "casa")
    elif "apartamento" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(tipo_construccion__icontains = "apartamento")
    elif "individual" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(tipo_construccion__icontains = "individual")
    elif "dúplex" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(tipo_construccion__icontains = "dúplex")
    elif "tríplex" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(tipo_construccion__icontains = "tríplex")
    elif "villa" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(tipo_construccion__icontains = "villa")
    elif "penthouse" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(tipo_construccion__icontains = "penthouse")
    elif "terreno" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(tipo_construccion__icontains = "terreno")
    elif "edificio" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(tipo_construccion__icontains = "edificio")
    elif "mansion" in busqueda:
        print("AJA???")
        posibles_inmuebles = posibles_inmuebles.filter(Q(nombre__icontains = 'mansión') | Q(descripcion__icontains = 'mansión'))

    if(not posibles_inmuebles):
        posibles_inmuebles = previo

    # Precio
    previo = posibles_inmuebles
    if "dólares" in busqueda:
        separado = busqueda.split(" ")
        indice = encuentra_coincidencia(separado, "dólares")
            
        if indice != -1:
            if separado[indice-1].isnumeric():
                posibles_inmuebles = posibles_inmuebles.filter(precio__lte = separado[indice-1])

    if(not posibles_inmuebles):
        posibles_inmuebles = previo

    # Ubicación detallada
    previo = posibles_inmuebles
    if "calle" in busqueda or "avenida" in busqueda:
        separado = busqueda.split(" ")
        indice = encuentra_coincidencia(separado, "calle")
            
        if indice != -1:
            posibles_inmuebles = posibles_inmuebles.filter(ubicacion_detallada__icontains = separado[indice])

    if(not posibles_inmuebles):
        posibles_inmuebles = previo

    # Pisos
    previo = posibles_inmuebles
    if "pisos" in busqueda:
        separado = busqueda.split(" ")
        indice = encuentra_coincidencia(separado, "pisos")
        
        if indice != -1:
            if separado[indice - 1].isnumeric():
                posibles_inmuebles = posibles_inmuebles.filter(tamano__gte = separado[indice-1])

    if(not posibles_inmuebles):
        posibles_inmuebles = previo

    # Servicios
    previo = posibles_inmuebles
    if "agua" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(agua = True)

    if "electricidad" in busqueda or "luz" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(electricidad = True)

    if "aseo" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(aseo = True)

    if "internet" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(internet = True)

    if "gas" in busqueda:
        posibles_inmuebles = posibles_inmuebles.filter(gas = True)

    if(not posibles_inmuebles):
        posibles_inmuebles = previo

    return posibles_inmuebles

def encuentra_coincidencia(array, a_buscar):
    for i,x in enumerate(array):
        if x == a_buscar:
            return i
    
    return -1