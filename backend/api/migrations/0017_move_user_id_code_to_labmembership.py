from django.db import migrations, models


def copy_user_id_code_to_membership(apps, schema_editor):
    UserProfile = apps.get_model('api', 'UserProfile')
    LabMembership = apps.get_model('api', 'LabMembership')

    for membership in LabMembership.objects.select_related('profile').all():
        code = getattr(membership.profile, 'user_id_code', None)
        if code and not membership.user_id_code:
            membership.user_id_code = code
            membership.save(update_fields=['user_id_code'])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_labmembership_signature_png'),
    ]

    operations = [
        migrations.AddField(
            model_name='labmembership',
            name='user_id_code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.RunPython(copy_user_id_code_to_membership, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='userprofile',
            name='user_id_code',
        ),
    ]
