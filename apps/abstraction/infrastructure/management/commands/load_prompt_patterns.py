"""Django management command to load prompt pattern seed data."""
from django.core.management.base import BaseCommand

from apps.abstraction.infrastructure.orm.models import PromptPatternModel
from apps.abstraction.infrastructure.seed_data import PROMPT_PATTERN_SEEDS


class Command(BaseCommand):
    help = "Load prompt pattern seed data"

    def handle(self, *args, **options):
        """Execute the seed data loading."""
        self.stdout.write(self.style.SUCCESS("Loading prompt pattern seed data..."))

        # Load patterns
        self._load_patterns()

        self.stdout.write(self.style.SUCCESS("Seed data loaded successfully!"))

    def _load_patterns(self):
        """Load prompt pattern seeds."""
        self.stdout.write("Loading prompt patterns...")

        for pattern in PROMPT_PATTERN_SEEDS:
            # Check if pattern already exists
            existing = PromptPatternModel.objects.filter(name=pattern.name).first()

            if existing:
                # Update existing pattern
                orm_model = PromptPatternModel.from_domain(pattern)
                orm_model.id = existing.id
                orm_model.created_at = existing.created_at
                orm_model.updated_at = pattern.updated_at
                orm_model.save()
                self.stdout.write(f"  ✓ Updated pattern: {pattern.name}")
            else:
                # Create new pattern
                orm_model = PromptPatternModel.from_domain(pattern)
                orm_model.created_at = None
                orm_model.updated_at = None
                orm_model.save()
                self.stdout.write(f"  ✓ Created pattern: {pattern.name}")
