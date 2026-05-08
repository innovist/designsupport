"""Account Django ORM models.

Implements User model with custom Django authentication backend.
"""
from uuid import uuid4

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from shared.infrastructure.orm.base_model import TimestampedModel


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, display_name=None, **extra_fields):
        """Create and save a regular user.

        Args:
            email: User email
            password: User password (will be hashed)
            display_name: User display name
            **extra_fields: Additional fields

        Returns:
            User instance

        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(email=email, display_name=display_name or email.split("@")[0], **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, display_name=None, **extra_fields):
        """Create and save a superuser.

        Args:
            email: User email
            password: User password (will be hashed)
            display_name: User display name
            **extra_fields: Additional fields

        Returns:
            Superuser instance
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, display_name, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    """Custom User model for email-based authentication.

    Uses email as the unique identifier instead of username.
    Inherits timestamp fields from TimestampedModel.
    """

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    # Authentication fields
    email = models.EmailField(unique=True, max_length=255, db_index=True)
    password_hash = models.CharField(max_length=255)  # Argon2id hash

    # Profile fields
    display_name = models.CharField(max_length=100)

    # Workspace reference
    default_workspace_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Account status
    is_active = models.BooleanField(default=True, db_index=True)
    is_tenant_admin = models.BooleanField(default=False)  # Tenant-level admin flag

    # Django admin integration
    is_staff = models.BooleanField(default=False)  # Admin access
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    # Objects manager
    objects = UserManager()

    class Meta:
        db_table = "accounts_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["default_workspace_id"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return self.email

    def set_password(self, raw_password: str) -> None:
        """Hash and set the user's password.

        Args:
            raw_password: Plain text password
        """
        # Import here to avoid domain layer dependency
        from apps.accounts.domain.services import PasswordHasher

        self.password_hash = PasswordHasher.hash(raw_password)
        self.password = self.password_hash

    def check_password(self, raw_password: str) -> bool:
        """Verify the user's password.

        Args:
            raw_password: Plain text password to verify

        Returns:
            True if password matches
        """
        # Import here to avoid domain layer dependency
        from apps.accounts.domain.services import PasswordHasher

        return PasswordHasher.verify(raw_password, self.password_hash)


UserModel = User
