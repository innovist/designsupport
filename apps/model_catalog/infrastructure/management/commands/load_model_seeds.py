"""Django management command to load model catalog seed data."""
from django.core.management.base import BaseCommand

from apps.model_catalog.infrastructure.orm.models import (
    FeatureModelPolicyModel,
    ModelCatalogModel,
    ModelProviderModel,
)
from apps.model_catalog.infrastructure.seed_data import (
    FEATURE_POLICY_SEEDS,
    MODEL_SEEDS,
    PROVIDER_SEEDS,
)


class Command(BaseCommand):
    help = "Load model catalog seed data (providers, models, policies)"

    def handle(self, *args, **options):
        """Execute the seed data loading."""
        self.stdout.write(self.style.SUCCESS("Loading model catalog seed data..."))

        # Load providers
        self._load_providers()

        # Load models
        self._load_models()

        # Load feature policies
        self._load_policies()

        self.stdout.write(self.style.SUCCESS("Seed data loaded successfully!"))

    def _load_providers(self):
        """Load provider seeds."""
        self.stdout.write("Loading providers...")

        for provider in PROVIDER_SEEDS:
            orm_model = ModelProviderModel.from_domain(provider)
            orm_model.created_at = None
            orm_model.updated_at = None
            orm_model.save()

            self.stdout.write(f"  ✓ Created provider: {provider.name}")

    def _load_models(self):
        """Load model catalog seeds."""
        self.stdout.write("Loading models...")

        for model in MODEL_SEEDS:
            orm_model = ModelCatalogModel.from_domain(model)
            orm_model.created_at = None
            orm_model.updated_at = None
            orm_model.save()

            self.stdout.write(
                f"  ✓ Created model: {model.provider_id}/{model.model_name}"
            )

    def _load_policies(self):
        """Load feature policy seeds."""
        self.stdout.write("Loading feature policies...")

        for policy in FEATURE_POLICY_SEEDS:
            orm_model = FeatureModelPolicyModel.from_domain(policy)
            orm_model.created_at = None
            orm_model.updated_at = None
            orm_model.save()

            # Add fallback models
            if policy.fallback_model_ids:
                fallback_models = list(ModelCatalogModel.objects.filter(
                    id__in=policy.fallback_model_ids
                ).all())
                orm_model.fallback_models.set(fallback_models)

            self.stdout.write(
                f"  ✓ Created policy: {policy.feature_key} → "
                f"{policy.primary_model_id} (v{policy.version})"
            )
