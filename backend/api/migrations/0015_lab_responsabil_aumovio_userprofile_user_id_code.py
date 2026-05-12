from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0014_remove_workentry_jurnal_individual"),
    ]

    operations = [
        migrations.AddField(
            model_name="lab",
            name="responsabil_aumovio",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="user_id_code",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
