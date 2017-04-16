# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-16 09:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Build',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('docker_image', models.CharField(blank=True, max_length=256, null=True)),
                ('ref', models.CharField(max_length=256)),
                ('commit', models.CharField(max_length=256)),
                ('message', models.CharField(max_length=256)),
                ('author_username', models.CharField(max_length=256)),
                ('author_display_name', models.CharField(max_length=256)),
                ('status', models.CharField(max_length=256)),
                ('output', models.TextField()),
                ('datetime_start', models.DateTimeField(blank=True, null=True)),
                ('datetime_end', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Repo',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('path', models.CharField(db_index=True, max_length=256)),
                ('enabled', models.BooleanField()),
                ('public', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('username', models.CharField(db_index=True, max_length=256)),
                ('display_name', models.CharField(max_length=256)),
                ('service_id', models.CharField(max_length=256)),
                ('service_username', models.CharField(max_length=256)),
                ('service_atoken', models.CharField(max_length=256)),
                ('service_rtoken', models.CharField(blank=True, max_length=256, null=True)),
                ('service_etoken', models.DateTimeField(blank=True, null=True)),
                ('last_login', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='repo',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.User'),
        ),
        migrations.AddField(
            model_name='build',
            name='repo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Repo'),
        ),
    ]