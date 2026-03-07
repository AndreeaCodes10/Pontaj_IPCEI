from datetime import datetime, date, time

from rest_framework import serializers
from .models import Lab, Subactivitate, WorkEntry


class LabSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Lab
        fields = ["id", "name", "display_name"]

    def get_display_name(self, obj):
        return obj.get_name_display()


class SubactivitateSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    display_livrabil = serializers.SerializerMethodField()
    class Meta:
        model = Subactivitate
        fields = [
            "id",
            "lab",
            "nume",
            "descriere",
            "display_name",
            "display_livrabil"
        ]

    def get_display_name(self, obj):
        return obj.nume()
    
class WorkEntrySerializer(serializers.ModelSerializer):
    nr_ore = serializers.FloatField()

    class Meta:
        model = WorkEntry
        fields = [
            "id",
            "user",
            "lab",
            "subactivitate",
            "livrabil",
            "individual",
            "date",
            "nr_ore",
            "durata",
            "activity_description",
            "comentarii",
            "links",
        ]
        read_only_fields = ["user"]

    def validate(self, data):
        # ensure durata format HH:MM-HH:MM
        if "-" not in data["durata"]:
            raise serializers.ValidationError(
                "Durata format invalid."
            )

        if data["subactivitate"].lab != data["lab"]:
            raise serializers.ValidationError(
                "Subactivitate does not belong to selected Lab."
            )

        return data