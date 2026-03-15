from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0011_labmembership_post"),
    ]

    operations = [
        migrations.AddField(
            model_name="lab",
            name="titlu",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]

