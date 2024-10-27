# `doko_api_app/management/commands/create_user.py`

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create a new user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user')
        parser.add_argument('password', type=str, help='Password of the user')
        parser.add_argument('--superuser', action='store_true', help='Create a superuser')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        password = kwargs['password']
        is_superuser = kwargs['superuser']

        if is_superuser:
            User.objects.create_superuser(username=username, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser {username}'))
        else:
            User.objects.create_user(username=username, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created user {username}'))