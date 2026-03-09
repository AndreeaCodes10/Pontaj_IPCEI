from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Lab(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("member", "Member"),  # optional global default
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    monthly_hour_limit = models.IntegerField(default=40)
    labs = models.ManyToManyField("Lab", through="LabMembership", blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
    
class LabMembership(models.Model):
    ROLE_CHOICES = (
        ("director", "Director"),
        ("member", "Member"),
    )

    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")

    monthly_hour_limit = models.IntegerField(default=40)

    class Meta:
        unique_together = ("profile", "lab")

    def __str__(self):
        return f"{self.profile.user.username} - {self.lab.name} ({self.role})"
    
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

    
class Subactivitate(models.Model):

    lab = models.ForeignKey(
        Lab,
        on_delete=models.CASCADE,
        related_name="subactivitati"
    )

    nume = models.CharField(max_length=100)

    # This is template-level description (multiple allowed per subactivity)
    descriere = models.TextField(blank=True)

    class Meta:
        unique_together = ("lab", "nume")

    def __str__(self):
        # return f"{self.lab.get_name_display()} - {self.get_nume_display()}"
        return f"{self.lab.name} - {self.nume}"


class WorkEntry(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)

    subactivitate = models.ForeignKey(
        Subactivitate,
        on_delete=models.PROTECT
    )

    # Common fields
    livrabil = models.TextField()
    individual = models.BooleanField(default=False)
    members = models.ManyToManyField(User, blank=True, related_name="shared_entries")

    date = models.DateField(default=timezone.now)

    nr_ore = models.IntegerField()
    durata = models.CharField(max_length=20)

    activity_description = models.TextField()

    comentarii = models.TextField(blank=True)

    links = models.TextField(blank=True)

    def __str__(self):
        return (
            f"{self.user} | "
            f"{self.lab.name} | "
            f"{self.subactivitate.nume} | "
            f"{self.date}"
        )