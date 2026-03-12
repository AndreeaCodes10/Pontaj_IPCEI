from django.contrib import admin
from .models import Lab, WorkEntry, UserProfile , LabMembership, Activitate


class ActivitateInline(admin.TabularInline):
    model = Activitate
    extra = 1
class LabMembershipInline(admin.TabularInline):
    model = LabMembership
    extra = 1

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "monthly_hour_limit")
    list_filter = ("role",)
    search_fields = ("user__username",)
    inlines = [LabMembershipInline]

@admin.register(LabMembership)
class LabMembershipAdmin(admin.ModelAdmin):
    list_display = ("profile", "lab", "role", "monthly_hour_limit")  # Add monthly_hour_limit to the list display
    list_filter = ("lab", "role")
    search_fields = ("profile__user__username", "lab__name")
    
@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = [ActivitateInline]


@admin.register(Activitate)
class ActivitateAdmin(admin.ModelAdmin):
    list_display = ("nume", "lab")
    search_fields = ("nume",)


@admin.register(WorkEntry)
class WorkEntryAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "lab",
        "activitate",
        "individual",
        "date",
        "nr_ore",
        "durata",
        "activity_description",
        "comentarii",
        "links"
    )
    list_filter = (
        "lab",
        "individual",
        "date",
    )
