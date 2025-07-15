import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker
from users.models import UserProfile

class Command(BaseCommand):
    help = 'Creates 100 fake users with realistic data.'

    def handle(self, *args, **kwargs):
        fake = Faker('fr_FR')  # Utiliser la localisation française pour des noms plus pertinents
        self.stdout.write(self.style.SUCCESS('Starting to create 1000 fake users...'))

        for i in range(100):
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            # S'assurer que le nom d'utilisateur est unique
            username = fake.unique.user_name()

            # S'assurer que l'email est unique
            email = fake.unique.email()

            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                password='password123',  # Mot de passe simple pour les tests
                email=email,
                first_name=first_name,
                last_name=last_name
            )

            # Mettre à jour le profil utilisateur avec les données bancaires (créé par signal)
            user_profile = user.userprofile
            user_profile.card_number = fake.credit_card_number()
            user_profile.card_expiry = fake.credit_card_expire()
            user_profile.card_cvv = fake.credit_card_security_code()
            user_profile.save()

            if (i + 1) % 10 == 0:
                self.stdout.write(self.style.SUCCESS(f'Successfully created {i + 1}/1000 users.'))

        self.stdout.write(self.style.SUCCESS('Finished creating 1000 fake users.')) 