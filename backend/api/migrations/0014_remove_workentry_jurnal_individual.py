from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0013_monthlymeta"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="workentry",
            name="individual",
        ),
        migrations.RemoveField(
            model_name="workentry",
            name="jurnal",
        ),
        migrations.RemoveField(
            model_name="workentry",
            name="scurta_descriere_jurnal",
        ),
    ]
