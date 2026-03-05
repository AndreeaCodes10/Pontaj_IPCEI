from django.urls import path

from . import users_views
from . import views
from . import export_views

urlpatterns = [
    path("app/", views.index, name="index"),
    path("labs/", views.list_labs, name="list-labs"),
    path("subactivitati/<int:lab_id>/", views.list_subactivitati, name="list-subactivitati"),
    path("work-entry/", views.create_work_entry, name="create-work-entry"),
    # path("send-to-excel/", views.export_work_entries_excel, name="export-work-entries-excel"),
    path("pontaj-dates/", views.get_pontaj_dates, name="get-pontaj-dates"),
    path("monthly-hours/", views.get_monthly_hours, name="get-monthly-hours"),
    path('login/', views.login_page, name="login"),
    path("current-user/", views.current_user, name="current-user"),
    path("logout/", views.logout_view, name="logout"),
    path("export-monthly-sheet/", export_views.export_monthly_sheet, name="export-monthly-sheet"),
    path("monthly-user-entries/", views.monthly_user_entries, name="monthly-user-entries"),
    path("work-entry/<int:entry_id>/", views.delete_work_entry, name="delete-work-entry"),

    path("labs/<int:lab_id>/members/", users_views.lab_members),
    path("labs/<int:lab_id>/add/<int:user_id>/", users_views.add_user_to_lab),
    path("labs/<int:lab_id>/remove/<int:user_id>/", users_views.remove_user_from_lab),
    path("all-users/", users_views.all_users, name="all-users"),
]
