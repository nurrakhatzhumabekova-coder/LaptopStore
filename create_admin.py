import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

try:
    User.objects.get(username='admin')
    print('✅ Пользователь admin уже существует')
except User.DoesNotExist:
    User.objects.create_superuser('admin', 'admin@store.com', 'admin123')
    print('✅ Суперпользователь admin создан!')