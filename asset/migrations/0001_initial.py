# Generated by Django 5.2 on 2025-05-01 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(blank=True, max_length=20, null=True)),
                ('enable', models.BooleanField(default=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
