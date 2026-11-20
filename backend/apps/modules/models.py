from django.db import models

from apps.spaces.models import Space

from .catalog import MODULE_CHOICES, MODULE_KEYS


class SpaceModule(models.Model):
    space = models.ForeignKey(
        Space,
        on_delete=models.CASCADE,
        related_name="module_configurations",
    )
    module_key = models.CharField(max_length=32, choices=MODULE_CHOICES)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("space_id", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("space", "module_key"),
                name="unique_module_configuration_per_space",
            ),
            models.CheckConstraint(
                condition=models.Q(module_key__in=MODULE_KEYS),
                name="valid_space_module_key",
            ),
        ]

    def __str__(self):
        return f"{self.space}: {self.get_module_key_display()}"
