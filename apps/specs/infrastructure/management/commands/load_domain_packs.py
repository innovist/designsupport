"""Django management command to load domain pack seed data."""
from django.core.management.base import BaseCommand

from apps.specs.infrastructure.orm.models import DomainPackModel
from apps.specs.infrastructure.seed_data import get_domain_pack_seed_data


class Command(BaseCommand):
    """Load domain pack seed data into database."""

    help = "Loads domain pack seed data into the database"

    def handle(self, *args, **options):
        """Execute the command."""
        # Get seed data
        seed_data = get_domain_pack_seed_data()

        # Track statistics
        created_count = 0
        updated_count = 0

        for pack_data in seed_data:
            pack_id = pack_data["id"]

            # Check if pack already exists
            try:
                existing_pack = DomainPackModel.objects.get(id=pack_id)

                # Update existing pack
                for key, value in pack_data.items():
                    setattr(existing_pack, key, value)
                existing_pack.save()

                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Updated domain pack: {pack_id}")
                )

            except DomainPackModel.DoesNotExist:
                # Create new pack
                DomainPackModel.objects.create(**pack_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created domain pack: {pack_id}")
                )

        # Print summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f"Domain pack seed data loaded: {created_count} created, {updated_count} updated"
            )
        )
        self.stdout.write("=" * 50)
