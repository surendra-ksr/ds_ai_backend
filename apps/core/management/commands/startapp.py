
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
    help = 'Creates a Django app with a custom structure.'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='The name of the application.')

    def handle(self, *args, **options):
        app_name = options['app_name']
        app_dir = os.path.join(settings.BASE_DIR, 'apps', app_name)

        if os.path.exists(app_dir):
            raise CommandError(f"App '{app_name}' already exists.")

        # Create app directory
        os.makedirs(app_dir)

        # Create standard files
        files_to_create = {
            '__init__.py': '',
            'admin.py': f'from django.contrib import admin\n\n# Register your models here.\n',
            'apps.py': f'from django.apps import AppConfig\n\nclass {app_name.capitalize()}Config(AppConfig):\n    default_auto_field = \'django.db.models.BigAutoField\'\n    name = \'apps.{app_name}\'\n',
            'models.py': f'from django.db import models\n\n# Create your models here.\n',
            'tests.py': f'from django.test import TestCase\n\n# Create your tests here.\n',
            'views.py': f'from django.shortcuts import render\n\n# Create your views here.\n',
            'serializers.py': 'from rest_framework import serializers\n',
            'urls.py': 'from django.urls import path\nfrom . import views\n\nurlpatterns = []\n',
        }

        for filename, content in files_to_create.items():
            with open(os.path.join(app_dir, filename), 'w') as f:
                f.write(content)

        self.stdout.write(self.style.SUCCESS(f"Successfully created app '{app_name}'"))
