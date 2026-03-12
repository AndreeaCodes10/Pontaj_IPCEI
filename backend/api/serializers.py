from datetime import datetime, date, time

from rest_framework import serializers
from .models import Lab, WorkEntry


class LabSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Lab
        fields = ["id", "name", "display_name"]

    def get_display_name(self, obj):
        return obj.get_name_display()

class WorkEntrySerializer(serializers.ModelSerializer):
    nr_ore = serializers.IntegerField()

    class Meta:
        model = WorkEntry
        fields = [
            "id",
            "user",
            "lab",
            "activitate",
            "livrabil",
            "individual",
            "date",
            "nr_ore",
            "durata",
            "activity_description",
            "comentarii",
            "links",
        ]
        # activity_description is derived from Activitate.descriere (admin-managed),
        # not submitted by the user.
        read_only_fields = ["user", "activity_description"]

    def validate(self, data):
        # ensure durata format HH:MM-HH:MM
        if "-" not in data["durata"]:
            raise serializers.ValidationError(
                "Durata format invalid."
            )

        if data["activitate"].lab != data["lab"]:
            raise serializers.ValidationError(
                "Activitate does not belong to selected Lab."
            )

        return data

    def create(self, validated_data):
        activitate = validated_data.get("activitate")
        if activitate is not None:
            validated_data["activity_description"] = activitate.descriere or ""
        return super().create(validated_data)
