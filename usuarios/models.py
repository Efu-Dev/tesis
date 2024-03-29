from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import CustomUserManager
from inmuebles.models import Cita

# Create your models here.

class Persona(models.Model):
    tipo = models.CharField(choices=(('V','V'),('E','E'),('J','J'),('G','G')), null=False, max_length=1)
    identificacion = models.CharField(max_length=9, null=False )
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    fecha_nacimiento = models.DateTimeField(null=False)
    numero_telefono = models.CharField(null=False, max_length=11)
    puede_ver = models.BooleanField(default=False)
    cargo = models.CharField(max_length=1,choices=(("A","Administrador"), ("G", "Agente Inmobiliario"), ("C", "Comprador")))

    def __str__(self):
        return self.nombre.title() + " " + self.apellido.title()
    
    def cedula(self):
        return self.tipo + "-" + self.identificacion
    
    def citas_agente(self):
        return Cita.objects.filter(inmueble__agente = self, estado = "E")
    
    def citas_cliente(self):
        return Cita.objects.filter(persona = self, estado = "E")
    
    def email(self):
        return self.usuario_persona.email

class Usuario(AbstractUser):
    username = None
    email = models.EmailField("Correo Electrónico", unique=True)
    persona = models.OneToOneField(to='usuarios.Persona', on_delete=models.CASCADE, related_name="usuario_persona", default=4)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    def tipo_usuario(self):
        return "Agente" if self.usuario_persona.cargo == 'A' else "Cliente"   
    