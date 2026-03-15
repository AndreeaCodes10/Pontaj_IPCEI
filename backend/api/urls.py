from django.urls import path

from . import users_views
from . import views
from . import export_views
# http://127.0.0.1:8000/api/login/
# http://127.0.0.1:8000/api/app/
# http://127.0.0.1:8000/api/entries/?lab=&month=3&year=2026

urlpatterns = [
    path("app/", views.index, name="index"),
    path("entries/", views.entries_page, name="entries_page"),
    path("labs/", views.list_labs, name="list-labs"),
    path("activitati/<int:lab_id>/", views.list_activitati, name="list-activitati"),
    path("work-entry/", views.create_work_entry, name="create-work-entry"),
    # path("send-to-excel/", views.export_work_entries_excel, name="export-work-entries-excel"),
    path("pontaj-dates/", views.get_pontaj_dates, name="get-pontaj-dates"),
    path("monthly-hours/", views.get_monthly_hours, name="get-monthly-hours"),
    path('login/', views.login_page, name="login"),
    path("current-user/", views.current_user, name="current-user"),
    path("logout/", views.logout_view, name="logout"),
    # path("export-monthly-sheet/", export_views.export_monthly_sheet, name="export-monthly-sheet"),
    path("export-monthly-sheet/", export_views.export_excel, name="export-excel"),
    # path("export-monthly-sheet/", export_views.export_work_entries_excel, name="export-work-entries-excel"),
    path("monthly-user-entries/", views.monthly_user_entries, name="monthly-user-entries"),
    path("generate-jurnal-docx/", views.generate_jurnal_docx, name="generate-jurnal-docx"),
    path("work-entry/<int:entry_id>/", views.delete_work_entry, name="delete-work-entry"),

    path("labs/<int:lab_id>/members/", users_views.lab_members),
    path(
        "labs/<int:lab_id>/members/<int:user_id>/monthly-hour-limit/",
        users_views.update_monthly_hour_limit,
        name="update-monthly-hour-limit",
    ),
    path(
        "labs/<int:lab_id>/members/<int:user_id>/monthly-hour-limit/anexa1-docx/",
        users_views.generate_anexa1_referat_modificare_docx,
        name="generate-anexa1-referat-modificare-docx",
    ),

]
