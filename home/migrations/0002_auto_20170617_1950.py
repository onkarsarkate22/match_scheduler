# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-17 19:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logincredential',
            name='user_name',
            field=models.CharField(max_length=20),
        ),
    ]