from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import HRProfile

@receiver(post_save, sender=User)
def create_hr_profile(sender, instance, created, **kwargs):
    if created:
        HRProfile.objects.create(
            user=instance,
            company_name="Default Company"
        )
