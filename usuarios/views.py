from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import logout
from .models import Persona, Usuario
from django.contrib.auth.hashers import make_password
from inmuebles.views import enviar_correo
import re
import random
import datetime
# Create your views here.

def bienvenida(request):
    if request.method == 'POST' and request.POST.get('busqueda'):
        busqueda = request.POST.get('busqueda').strip().lower()
        request.session['busqueda'] = busqueda

        return redirect('/inmuebles/resultados/')
    
    mensaje = ""
    
    if(request.session.get('mensaje')):
        mensaje = request.session.get('mensaje')
        del(request.session['mensaje'])

    return render(request, 'registration/bienvenida.html', {'mensaje': mensaje})

def comprobacion_cedula(request):
    print(request.GET)
    return JsonResponse({'existe': Persona.objects.filter(tipo=request.GET['tipo'], identificacion = request.GET['cedula']).exists()})

def comprobacion_correo(request):
    if(not request.user.is_authenticated):
        return JsonResponse({'existe': Usuario.objects.filter(email = request.GET['email']).exists()})
    return JsonResponse({'existe': Usuario.objects.filter(email = request.GET['email']).exclude(pk = request.user.pk).exists()})

def comprobacion_telefono(request):
    print(request.GET)
    if(not request.user.is_authenticated):
        return JsonResponse({'existe': Persona.objects.filter(numero_telefono = request.GET['numero_telefono']).exists()})
    return JsonResponse({'existe': Persona.objects.filter(numero_telefono = request.GET['numero_telefono']).exclude(pk=request.user.persona.pk).exists()})

def register_user(request):
    if request.method == 'POST':
        print(request.POST)
        persona = request.POST.get('tipo')
        identificacion = request.POST.get('identificacion')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        ciego = request.POST.get('ciego')
        email = request.POST.get('email')
        password = request.POST.get('password')
        telefono = request.POST.get('telefono')

        # Validar
        errores = []

        # Campos Vacíos
        if(identificacion == ""):
            errores.append("El campo de identificación no puede estar vacío.")
        if(nombre == ""):
            errores.append("El campo de nombres no puede estar vacío.")
        if(apellido == ""):
            errores.append("El campo de apellidos no puede estar vacío.")
        if(fecha_nacimiento == ""):
            errores.append("El campo de fecha de nacimiento no puede estar vacío.")
        if(email == ""):
            errores.append("El campo de correo electrónico no puede estar vacío.")
        if(password == ""):
            errores.append("El campo de contraseña no puede estar vacío.")
        
        # Campos duplicados
        if(Usuario.objects.filter(email=email).exists()):
            errores.append("El email ingresado ya fue utilizado.")
        if(Persona.objects.filter(tipo=persona,identificacion=identificacion).exists()):
            errores.append("Ya hay una persona con esa identificación registrada.")
        if(Persona.objects.filter(numero_telefono = telefono).exists()):
            errores.append("Ya ese número de teléfono está siendo utilizado.")
        
        # Caracteres inválidos
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        fecha = datetime.datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
        if(not re.fullmatch(regex,email.strip())):
            errores.append("El correo electrónico ingresado no es válido.")
        regex = r"[A-Za-záéíóúÁÉÍÓÚñÑüÜ\s]+"
        if(not re.fullmatch(regex,nombre.strip())):
            errores.append("El nombre ingresado no es válido.")
        if(not re.fullmatch(regex,apellido.strip())):
            errores.append("El apellido ingresado no es válido.")
        if(datetime.datetime.today() < fecha):
            errores.append("La fecha de nacimiento debe de ser menor o igual al día actual.")
        elif(calculateAge(fecha) < 21):
            errores.append("Su edad debe de ser mayor o igual a 21.")
        elif(fecha.year < 1900):
            errores.append("El año de nacimiento debe ser mayor o igual a 1900.")
        
        regex = r"[0-9]+"
        if(re.fullmatch(telefono,regex)):
            errores.append("El número de teléfono ingresado no es enteramente numérico.")
        
        if(len(telefono) < 10):
            errores.append("El número de teléfono debe ser de al menos 10 caracteres.")
        
        if(len(password) < 8):
            errores.append("La contraseña debe contener al menos 8 caracteres.")

        if(len(errores) != 0):
            return render(request, 'registration/register.html', {'errores': errores, 'previo': request.POST})

        # Crear
        persona = Persona.objects.create(tipo=persona, identificacion=identificacion.strip(),
            nombre=nombre.strip(), apellido=apellido.strip(), fecha_nacimiento=fecha_nacimiento,
            numero_telefono= telefono, puede_ver = not ciego, cargo = "C")
        Usuario.objects.create(persona=persona, email=email.strip(), password = make_password(password))

        request.session['mensaje'] = "¡Su usuario se ha creado exitosamente! Ahora inicie sesión."

        return redirect('/')
    else:
        return render(request, 'registration/register.html', {})
    
def bienvenida_agente(request):
    if(not request.user.is_authenticated or request.user.persona.cargo != 'A'):
        print("Acceso No autorizado")
        return redirect('/')
    
    mensaje = ""
    
    if(request.session.get('mensaje')):
        mensaje = request.session.get('mensaje')
        del(request.session['mensaje'])
    
    return render(request, "bienvenida_agente.html", {'mensaje': mensaje})

def perfil(request):
    return render(request, 'perfil.html')

def edicion_perfil(request):
    if(request.method == 'GET'):
        return render(request, 'edicion_perfil.html')
    elif(request.method == 'POST'):
        errores = []
        if(Persona.objects.filter(numero_telefono = request.POST['numero_telefono']).exists() and request.POST['numero_telefono'] != request.user.persona.numero_telefono):
            errores.append('El número de teléfono ya está registrado.')
        
        if(Usuario.objects.filter(email = request.POST['email']).exists() and request.POST['email'] != request.user.email):
            errores.append('El correo electrónico ingresado ya está registrado')

        if(len(errores)):
            return render(request, 'edicion_perfil.html', {'previo': request.POST, 'errores': errores})
        else:
            request.user.email = request.POST['email']
            request.user.save()

            persona = request.user.persona
            persona.numero_telefono = request.POST['numero_telefono']
            request.user.persona.save()

            request.session['mensaje'] = "Se han cambiado sus datos exitosamente."

            return redirect('/')

def cambio_contrasena(request):
    if(request.method == 'GET'):
        return render(request, 'cambio_contrasena.html')
    elif(request.method == 'POST'):
        if(request.POST['contrasena'] != request.POST['repetir']):
            return render(request, 'cambio_contrasena.html', {'error': 'Las contraseñas no coinciden.'})

        request.user.password = make_password(request.POST['contrasena'])
        request.user.save()

        request.session['mensaje'] = "Se ha cambiado su contraseña exitosamente. Inicie sesión de nuevo."

        return redirect('/')

def cerrar_sesion(request):
    logout(request)
    request.session['mensaje'] = "Sesión cerrada."
    return redirect('/')

def recuperar_contrasena(request):
    request.session['busqueda'] = ''
    if(request.method == 'GET'):
        return render(request, 'recuperar_contrasena.html')
    elif(request.method == 'POST'):

        if(not Usuario.objects.filter(email__iexact = request.POST['email']).exists()):
            errores = [f"El correo electrónico {request.POST['email']} no se encuentra en nuestra base de datos."]
            return render(request, 'recuperar_contrasena.html', context={'errores': errores})

        usuario = Usuario.objects.get(email__iexact = request.POST['email'])
        contrasena = generar_contrasena()
        usuario.password = make_password(contrasena)
        usuario.save()

        enviar_correo(usuario.persona, 'Olvido de Contraseña', f"Estimado usuario {usuario.persona}, \nuested olvidó la contraseña y solicitó renovarla. Aquí tiene su contraseña nueva: <b>{contrasena}</b>\nSe le sugiere que al iniciar sesión la cambie inmediatamente.\n\nAtentamente, Inmuebles Incaibo.")

        request.session['mensaje'] = "Su contraseña nueva ha sido enviada a su correo electrónico."

        return redirect("/")

# Funciones Auxiliares

def generar_contrasena():
    caracteres = "abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZ1234567890!?.#$:;-_*"
    nueva_contrasena = ''.join(random.choice(caracteres) for i in range(int(random.randint(8,15))))

    return nueva_contrasena

def calculateAge(dob):
    today = datetime.date.today()
    age = today.year - dob.year -((today.month, today.day) <
         (dob.month, dob.day))
  
    return age