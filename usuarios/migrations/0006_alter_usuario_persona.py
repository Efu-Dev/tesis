# Generated by Django 4.2 on 2023-07-05 19:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0005_remove_usuario_numero_seguridad_persona_cargo_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='persona',
            field=models.OneToOneField(default=4, on_delete=django.db.models.deletion.CASCADE, related_name='usuario_persona', to='usuarios.persona'),
        ),
    ]