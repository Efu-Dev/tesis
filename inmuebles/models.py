from django.db import models
from num2words import num2words
from django.conf import settings
from os import listdir
from os.path import isfile, join

# Create your models here.

estados_inmueble = [
    ("R", "En Revisión"),
    ("A", "Activo"),
    ("T", "Compromiso de Compra"),
    ("D", "Denegado"),
    ("E", "Revisión por Edición"),
    ("C", "Revisión para Cancelación"),
    ("X", "Cancelado"),
    ("S", "Formalidades Pendientes"),
    ("V", "Vendida")
]

estados_compra = [
    ("E", "Espera de Pago"),
    ("C", "Por Cancelación"),
    ("X", "Cancelada"),
    ("S", "Cita de Formalidades"),
    ("F", "Finalizada"),
]

estados_cita = [
    ("E", "En Espera"),
    ("C", "Cancelada"),
    ("P", "Pendiente por Resultado"),
    ("F", "Finalizada - Visto Bueno Para Compra"),
    ("X", "Finalizada - No Habilitado para Compra"),
]

tipos_construccion = [
    ("Casa Individual",)*2,
    ("Casa Dúplex",)*2,
    ("Casa Tríplex",)*2,
    ("Casa de Villa",)*2,
    ("Apartamento Regular",)*2,
    ("Apartamento PentHouse",)*2,
    ("Terreno",)*2,
    ("Oficina",)*2,
    ("Edificio",)*2,
]

class Parroquia(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre.upper()

class Sector(models.Model):
    nombre = models.CharField(max_length=45)
    parroquia = models.ForeignKey(to=Parroquia, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre.upper()

class Inmueble(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.CharField(max_length=1, default="R", choices=estados_inmueble)
    ano_construccion = models.IntegerField()
    tipo_construccion = models.CharField(max_length=45, default="Casa Individual", choices=tipos_construccion)
    estacionamientos = models.IntegerField()
    tamano = models.DecimalField(decimal_places=2,max_digits=10)
    habitaciones = models.IntegerField()
    banos = models.IntegerField()
    amueblado = models.BooleanField()
    descripcion = models.TextField()
    comentarios_internos = models.TextField(default="")
    ubicacion_detallada = models.TextField()
    precio = models.DecimalField(decimal_places=2,max_digits=12)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    pisos = models.IntegerField()
    agua = models.BooleanField()
    electricidad = models.BooleanField()
    internet = models.BooleanField()
    gas = models.BooleanField()
    aseo = models.BooleanField()

    sector = models.ForeignKey(to=Sector, on_delete=models.CASCADE)
    dueno = models.ForeignKey(to='usuarios.Persona',on_delete=models.CASCADE, related_name="dueno")
    agente =  models.ForeignKey(to='usuarios.Persona', on_delete=models.CASCADE, related_name="agente")

    def precio_input(self):
        return str(self.precio).replace(",",".")
    
    def tamano_input(self):
        return str(self.tamano).replace(",",".")
    
    def precio_texto(self):
        return num2words(self.precio, lang="es")
    
    def tamano_texto(self):
        return num2words(self.tamano, lang="es")
    
    def estado_largo(self):
        for (x,y) in estados_inmueble:
            if(x == self.estado):
                return y
        
        return "DESCONOCIDO"
    
    def compra_activa(self):
        return Compra.objects.get(inmueble=self,estado__in= ["E", "S"])

    def formalidades(self):
        if(self.estado == 'S'):
            return self.compra_activa().citas.first()

    def servicios(self):
        servicios = ""
        if(self.agua):
            servicios += "Agua. "
        
        if(self.electricidad):
            servicios += "Electricidad. "
        
        if(self.aseo):
            servicios += "Aseo urbano. "
        
        if(self.gas):
            servicios += "Gas. "
        
        if(self.internet):
            servicios += "Internet. "
        
        if(len(servicios) == 0):
            servicios = "Ninguno."

        return servicios
    
    def imagenes(self):
        media_path = settings.MEDIA_ROOT
        imagenes = ['/media/' + f for f in listdir(media_path) if isfile(join(media_path, f)) and f.startswith(f'{self.pk}_')]
        return imagenes
    
    def edicion(self):
        return Edicion.objects.get(inmueble__pk=self.pk, estado = 'R')
    
    def tiene_pagos_pendientes(self):
        return self.compra_activa() or self.compra_activa().pagos.filter(estado = 'P').exists()
    
    def compra_final(self):
        compra = Compra.objects.filter(estado = 'F', inmueble__pk = self.pk)
        print(compra.first())
        if(compra.exists()):
            return compra.first()

    def __str__(self):
        return self.nombre.upper()

class Compra(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=1,choices=estados_compra,default='E')
    comprador = models.ForeignKey(to='usuarios.Persona', on_delete=models.CASCADE)
    inmueble = models.ForeignKey(to=Inmueble, on_delete=models.CASCADE)

    def monto_cancelado(self):
        return sum([round(x.valor_dolar(), 2) for x in self.pagos.filter(estado = "A")] if self.pagos.all().count() else [0])
    
    def monto_cancelado_texto(self):
        return num2words(sum([round(x.valor_dolar(), 2) for x in self.pagos.filter(estado = "A")] if self.pagos.all().count() else [0]), lang="es")

    def estado_largo(self):
        for (x,y) in estados_compra:
            if(x == self.estado):
                return y
        
        return "DESCONOCIDO"
    
    def comision_inmobiliaria(self):
        return round(float(self.inmueble.precio)*0.05, 2)
    
    def iva(self):
        return round(float(self.inmueble.precio)*0.16, 2)
    
    def comision_dueno(self):
        return round(float(self.inmueble.precio)*0.79, 2)
    
    def excedente(self):
        return round(float(self.monto_cancelado()) - float(self.inmueble.precio), 2)
    
    def comision_inmobiliaria_texto(self):
        return num2words(round(float(self.inmueble.precio)*0.05, 2), lang="es")
    
    def iva_texto(self):
        return num2words(round(float(self.inmueble.precio)*0.16, 2), lang="es")
    
    def comision_dueno_texto(self):
        return num2words(round(float(self.inmueble.precio)*0.79, 2), lang="es")
    
    def excedente_texto(self):
        return num2words(round(float(self.monto_cancelado()) - float(self.inmueble.precio), 2), lang="es")
    
    def cita_formalidades(self):
        return self.citas.last()
    
    def tiene_pagos_pendientes(self):
        return self.pagos.filter(estado = 'P').exists()
    
    def __str__(self):
        return f"COMPRA DEL INMUEBLE '{self.inmueble.nombre.upper()}' ({self.inmueble.pk})"

class Cita(models.Model):
    compra = models.ForeignKey(to=Compra, on_delete=models.CASCADE, null=True, related_name="citas")
    inmueble = models.ForeignKey(to=Inmueble, on_delete=models.CASCADE, null=True)
    persona = models.ForeignKey(to='usuarios.Persona', on_delete=models.CASCADE, null=True)
    fecha_asignada = models.DateTimeField()
    estado = models.CharField(max_length=1, choices=estados_cita, default='E')
    resultados = models.TextField(blank=True)

    def estado_largo(self):
        for (x,y) in estados_cita:
            if(x == self.estado):
                return y
        
        return "DESCONOCIDO"
    
    def __str__(self):
        return f"CITA DE VISITA AL INMUEBLE '{self.inmueble.nombre.upper()}' ({self.pk})" if self.persona else f"CITA DE FORMALIDADES AL INMUEBLE '{self.compra.inmueble.nombre.upper()}' ({self.pk})"
    
class Edicion(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.CharField(max_length=1, default="R", choices=estados_inmueble)
    ano_construccion = models.IntegerField()
    tipo_construccion = models.CharField(max_length=45, default="Casa Individual", choices=tipos_construccion)
    estacionamientos = models.IntegerField()
    tamano = models.DecimalField(decimal_places=2,max_digits=10)
    habitaciones = models.IntegerField()
    banos = models.IntegerField()
    amueblado = models.BooleanField()
    descripcion = models.TextField()
    comentarios_internos = models.TextField(default="")
    ubicacion_detallada = models.TextField()
    precio = models.DecimalField(decimal_places=2,max_digits=12)
    pisos = models.IntegerField()
    agua = models.BooleanField()
    electricidad = models.BooleanField()
    internet = models.BooleanField()
    gas = models.BooleanField()
    aseo = models.BooleanField()
    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE)

    def precio_input(self):
        return str(self.precio).replace(",",".")
    
    def tamano_input(self):
        return str(self.tamano).replace(",",".")
    
    def __str__(self):
        return f"EDICIÓN INMUEBLE '{self.inmueble.nombre.upper()}' ({self.pk})"