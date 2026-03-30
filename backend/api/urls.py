from django.urls import path
from django.contrib.auth import views as auth_views

from . import users_views
from . import views
from . import export_views
# http://127.0.0.1:8000/api/login/
# http://127.0.0.1:8000/api/app/
# http://127.0.0.1:8000/api/entries/?lab=&month=3&year=2026

urlpatterns = [
    path("app/", views.index, name="index"),
    path("entries/", views.entries_page, name="entries_page"),
    path("members-hours/", views.members_hours_page, name="members-hours-page"),
    path("annual-stats/", views.annual_stats_page, name="annual-stats-page"),
    path("labs/", views.list_labs, name="list-labs"),
    path("director-labs/", views.list_director_labs, name="list-director-labs"),
    path("activitati/<int:lab_id>/", views.list_activitati, name="list-activitati"),
    path("work-entry/", views.create_work_entry, name="create-work-entry"),
    # path("send-to-excel/", views.export_work_entries_excel, name="export-work-entries-excel"),
    path("pontaj-dates/", views.get_pontaj_dates, name="get-pontaj-dates"),
    path("monthly-hours/", views.get_monthly_hours, name="get-monthly-hours"),
    path("members-monthly-hours/", views.get_members_monthly_hours, name="get-members-monthly-hours"),
    path("members-yearly-hours/", views.get_members_yearly_hours, name="get-members-yearly-hours"),
    path('login/', views.login_page, name="login"),
    path("current-user/", views.current_user, name="current-user"),
    path("logout/", views.logout_view, name="logout"),

    # Password Management
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="api/password_reset.html"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="api/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="api/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="api/password_reset_complete.html"), name="password_reset_complete"),
    path("password-change/", auth_views.PasswordChangeView.as_view(template_name="api/password_change.html"), name="password_change"),
    path("password-change/done/", auth_views.PasswordChangeDoneView.as_view(template_name="api/password_change_done.html"), name="password_change_done"),

    # path("export-monthly-sheet/", export_views.export_monthly_sheet, name="export-monthly-sheet"),
    path("export-monthly-sheet/", export_views.export_excel, name="export-excel"),
    # path("export-monthly-sheet/", export_views.export_work_entries_excel, name="export-work-entries-excel"),
    path("monthly-user-entries/", views.monthly_user_entries, name="monthly-user-entries"),
    path("generate-jurnal-docx/", views.generate_jurnal_docx, name="generate-jurnal-docx"),
    path("work-entry/<int:entry_id>/", views.work_entry_detail, name="work-entry-detail"),
    path("monthly-meta/", views.monthly_meta, name="monthly-meta"),

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
