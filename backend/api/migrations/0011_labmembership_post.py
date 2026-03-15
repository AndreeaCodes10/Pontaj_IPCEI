from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0010_workentry_scurta_descriere_jurnal"),
    ]

    operations = [
        migrations.AddField(
            model_name="labmembership",
            name="post",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]

