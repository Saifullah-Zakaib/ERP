from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    help = 'Create initial users for all roles'

    def handle(self, *args, **kwargs):
        users_data = [
            {
                'username': 'admin',
                'password': 'admin123',
                'email': 'admin@beamysports.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'inventory',
                'password': 'inventory123',
                'email': 'inventory@beamysports.com',
                'first_name': 'Inventory',
                'last_name': 'Manager',
                'role': 'inventory',
                'department': 'Inventory',
            },
            {
                'username': 'production',
                'password': 'production123',
                'email': 'production@beamysports.com',
                'first_name': 'Production',
                'last_name': 'Manager',
                'role': 'production',
                'department': 'Production',
            },
            {
                'username': 'hr',
                'password': 'hr123',
                'email': 'hr@beamysports.com',
                'first_name': 'HR',
                'last_name': 'Manager',
                'role': 'hr',
                'department': 'HR',
            },
            {
                'username': 'finance',
                'password': 'finance123',
                'email': 'finance@beamysports.com',
                'first_name': 'Finance',
                'last_name': 'Manager',
                'role': 'finance',
                'department': 'Finance',
            },
            {
                'username': 'supplier',
                'password': 'supplier123',
                'email': 'supplier@beamysports.com',
                'first_name': 'Purchase',
                'last_name': 'Manager',
                'role': 'supplier',
                'department': 'Supplier',
            },
        ]

        for user_data in users_data:
            username = user_data.pop('username')
            password = user_data.pop('password')
            
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, password=password, **user_data)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created user: {username}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'User already exists: {username}')
                )
