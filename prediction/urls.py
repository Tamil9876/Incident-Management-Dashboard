from django.urls import path, include
from django.contrib import admin
from . import views
from django.shortcuts import redirect



urlpatterns = [

    path("Admin/", admin.site.urls),
    path("", views.home, name="home"),        # Home page
    path("upload/", views.upload_csv, name="upload_csv"),
    path("incidents/", views.incident_list, name="incident_list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("incident/<int:id>/", views.incident_detail, name="incident_detail"),
    path("incident/<int:id>/edit/", views.edit_incident, name="edit_incident"),
    path("delete/<int:id>/", views.delete_incident, name="delete_incident"),
    path("download/pdf/", views.download_pdf_report, name="download_pdf"),
    path("download csv/", views.download_csv, name="download_csv"),
    path("dashboard/pdf/", views.dashboard_pdf, name="dashboard_pdf"),
    path("notifications/", views.notifications_list, name="notifications"),

]
