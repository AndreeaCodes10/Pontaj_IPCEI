from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0015_lab_responsabil_aumovio_userprofile_user_id_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="labmembership",
            name="signature_png",
            field=models.BinaryField(blank=True, null=True),
        ),
    ]
