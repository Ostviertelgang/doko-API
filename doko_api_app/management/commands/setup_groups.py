from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from doko_api_app.models import Game, Player, Round

class Command(BaseCommand):
    help = 'Create default groups and assign permissions'

    def handle(self, *args, **options):
        # Define the groups and their permissions
        GROUPS = {
            'Admin': {
                'game': ['add', 'change', 'delete', 'view'],
                'player': ['add', 'change', 'delete', 'view'],
                'round': ['add', 'change', 'delete', 'view'],
            },
            'Player': {
                'game': ['view'],
                'player': ['view'],
                'round': ['view'],
            }
        }

        # Get content types
        game_ct = ContentType.objects.get_for_model(Game)
        player_ct = ContentType.objects.get_for_model(Player)
        round_ct = ContentType.objects.get_for_model(Round)

        # Create groups and assign permissions
        for group_name, models_permissions in GROUPS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'Created group "{group_name}"')
            
            # Assign permissions for each model
            for model_name, permissions in models_permissions.items():
                content_type = {
                    'game': game_ct,
                    'player': player_ct,
                    'round': round_ct,
                }[model_name]

                for permission_name in permissions:
                    codename = f'{permission_name}_{model_name}'
                    try:
                        permission = Permission.objects.get(
                            codename=codename,
                            content_type=content_type,
                        )
                        group.permissions.add(permission)
                        self.stdout.write(f'Added "{permission.codename}" to {group_name}')
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Permission "{codename}" does not exist'
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS('Successfully set up groups and permissions')
        )