from django.db import models
from django.contrib.auth.models import AbstractUser

# -----------------------------
# Custom User Model with Roles
# -----------------------------
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ("Admin", "Admin"),
        ("Engineer", "Engineer"),
        ("Viewer", "Viewer"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="Viewer"
    )

    # ✅ Prevent clashes with default Django related names
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_set",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_permissions_set",
        blank=True
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


# -----------------------------
# Incident Model
# -----------------------------
class Incident(models.Model):
    date = models.DateField()
    last_maintenance_date = models.DateField(null=True, blank=True)
    pressure = models.FloatField()
    temperature = models.FloatField()
    failure = models.CharField(max_length=200)
    risk = models.CharField(max_length=200)
    actions = models.TextField(blank=True, null=True)

    reported_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_incidents"
    )

    created_at = models.DateTimeField(auto_now_add=True)  # when record was added
    updated_at = models.DateTimeField(auto_now=True)      # last update

    def __str__(self):
        return f"Incident on {self.date} - Failure: {self.failure}"

# models.py
class Notification(models.Model):
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.message
