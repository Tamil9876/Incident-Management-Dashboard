import csv
import io
import json
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from .models import Incident
from django import forms

# -----------------------------------------
# ROLE CHECKS
# -----------------------------------------
def is_admin(user):
    return user.groups.filter(name="Admin").exists()

def is_engineer(user):
    return user.groups.filter(name="Engineer").exists()

def is_viewer(user):
    return user.groups.filter(name="Viewer").exists()


# -----------------------------------------
# HOME & AUTH
# -----------------------------------------
def home(request):
    return render(request, "home.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password ❌")
    return render(request, "login.html")

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


# -----------------------------------------
# UPLOAD CSV (Admin + Engineer)
# -----------------------------------------
@login_required
@user_passes_test(lambda u: is_admin(u) or is_engineer(u))
def upload_csv(request):
    if request.method == "POST":
        if "file" not in request.FILES:
            messages.error(request, "No file uploaded")
            return redirect("upload_csv")

        csv_file = request.FILES["file"]
        if not csv_file.name.endswith(".csv"):
            messages.error(request, "File must be CSV")
            return redirect("upload_csv")

        try:
            df = pd.read_csv(csv_file)
            required_columns = ["date", "last_maintenance_date", "pressure", "temperature", "failure", "risk", "actions"]

            for col in required_columns:
                if col not in df.columns:
                    messages.error(request, f"Missing column: {col}")
                    return redirect("upload_csv")

            for _, row in df.iterrows():
                Incident.objects.create(
                    date=row["date"],
                    last_maintenance_date=row["last_maintenance_date"],
                    pressure=row["pressure"],
                    temperature=row["temperature"],
                    failure=row["failure"],
                    risk=row["risk"],
                    actions=row["actions"],
                )
            messages.success(request, "CSV uploaded successfully ✅")
            return redirect("incident_list")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect("upload_csv")

    return render(request, "upload_csv.html")


# -----------------------------------------
# INCIDENT LIST (All Roles)
# -----------------------------------------
@login_required
def incident_list(request):
    query = request.GET.get("q", "")
    if query:
        incidents = Incident.objects.filter(
            failure__icontains=query
        ) | Incident.objects.filter(
            risk__icontains=query
        ) | Incident.objects.filter(
            date__icontains=query
        )
    else:
        incidents = Incident.objects.all().order_by("-date")

    return render(request, "incident_list.html", {"incidents": incidents, "query": query})


# -----------------------------------------
# DASHBOARD (All Roles)
# -----------------------------------------
@login_required
def dashboard(request):
    incidents = Incident.objects.all()

    # summary counts
    total_incidents = incidents.count()
    high_risk = incidents.filter(risk__iexact="High").count()
    medium_risk = incidents.filter(risk__iexact="Medium").count()
    low_risk = incidents.filter(risk__iexact="Low").count()

    # failure distribution
    failure_qs = incidents.values("failure").annotate(total=Count("id"))
    failure_labels = [f["failure"] for f in failure_qs]
    failure_counts = [f["total"] for f in failure_qs]

    # risk distribution
    risk_qs = incidents.values("risk").annotate(total=Count("id"))
    risk_labels = [r["risk"] for r in risk_qs]
    risk_counts = [r["total"] for r in risk_qs]

    # trend by month
    months_counter = Counter()
    for inc in incidents:
        if inc.date:
            months_counter[inc.date.strftime("%Y-%m")] += 1
            months_counter[inc.date.strftime("%x-%m")] += 1
    months_sorted = sorted(months_counter.items())
    months = [m for m, _ in months_sorted]
    counts = [c for _, c in months_sorted]

    # recent incidents
    recent_incidents = incidents.order_by("-date")[:5]

    context = {
        "total_incidents": total_incidents,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk,
        "failure_labels": json.dumps(failure_labels),
        "failure_counts": json.dumps(failure_counts),
        "risk_labels": json.dumps(risk_labels),
        "risk_counts": json.dumps(risk_counts),
        "months": json.dumps(months),
        "counts": json.dumps(counts),
        "recent_incidents": recent_incidents,
    }
    return render(request, "dashboard.html", context)


# -----------------------------------------
# DASHBOARD PDF (All Roles)
# -----------------------------------------
@login_required
def dashboard_pdf(request):
    incidents = Incident.objects.all()

    # summary counts
    total_incidents = incidents.count()
    high_risk = incidents.filter(risk__iexact="High").count()
    medium_risk = incidents.filter(risk__iexact="Medium").count()
    low_risk = incidents.filter(risk__iexact="Low").count()

    # failure distribution
    failure_qs = incidents.values("failure").annotate(total=Count("id"))
    failure_labels = [f["failure"] for f in failure_qs]
    failure_counts = [f["total"] for f in failure_qs]

    # risk distribution
    risk_qs = incidents.values("risk").annotate(total=Count("id"))
    risk_labels = [r["risk"] for r in risk_qs]
    risk_counts = [r["total"] for r in risk_qs]

    # trend by month
    months_counter = Counter()
    for inc in incidents:
        if inc.date:
            months_counter[inc.date.strftime("%Y-%m")] += 1
            months_counter[inc.date.strftime("%x-%m")] += 1
    months_sorted = sorted(months_counter.items())
    months = [m for m, _ in months_sorted]
    counts = [c for _, c in months_sorted]

    incidents = Incident.objects.all().order_by("-date")

    total_incidents = incidents.count()
    high_risk = incidents.filter(risk__iexact="High").count()
    medium_risk = incidents.filter(risk__iexact="Medium").count()
    low_risk = incidents.filter(risk__iexact="Low").count()

    failure_qs = incidents.values("failure").annotate(total=Count("id"))
    failure_labels = [f["failure"] for f in failure_qs]
    failure_counts = [f["total"] for f in failure_qs]

    risk_qs = incidents.values("risk").annotate(total=Count("id"))
    risk_labels = [r["risk"] for r in risk_qs]
    risk_counts = [r["total"] for r in risk_qs]

    months_counter = Counter()
    for inc in incidents:
        if inc.date:
            months_counter[inc.date.strftime("%Y-%m")] += 1
            months_counter[inc.date.strftime("%x-%m")] += 1
    months_sorted = sorted(months_counter.items())
    months = [m for m, _ in months_sorted]
    counts = [c for _, c in months_sorted]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("ONGC Maintenance - Dashboard Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    # summary table
    summary_table_data = [
        ["Total", "High Risk", "Medium Risk", "Low Risk"],
        [str(total_incidents), str(high_risk), str(medium_risk), str(low_risk)],
    ]
    table = Table(summary_table_data, colWidths=[110, 110, 110, 110])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 18))

    doc.build(elements)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="dashboard_report.pdf")




# -----------------------------------------
# INCIDENT DETAIL (All Roles)
# -----------------------------------------
@login_required
def incident_detail(request, id):
    incident = get_object_or_404(Incident, id=id)
    return render(request, "incident_detail.html", {"incident": incident})


# -----------------------------------------
# DELETE INCIDENT (Admin only)
# -----------------------------------------
@login_required
@user_passes_test(is_admin)
def delete_incident(request, id):
    incident = get_object_or_404(Incident, id=id)
    incident.delete()
    messages.success(request, "Incident deleted ❌")
    return redirect("incident_list")



# Simple form for editing
class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ["date", "last_maintenance_date", "pressure", "temperature", "failure", "risk", "actions"]

# -----------------------------------------
# EDIT INCIDENT (Admin + Engineer)
# -----------------------------------------
@login_required
@user_passes_test(lambda u: is_admin(u) or is_engineer(u))
def edit_incident(request, id):
    incident = get_object_or_404(Incident, id=id)
    if request.method == "POST":
        form = IncidentForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            messages.success(request, "Incident updated successfully ✏️")
            return redirect("incident_detail", id=incident.id)
    else:
        form = IncidentForm(instance=incident)

    return render(request, "edit_incident.html", {"form": form, "incident": incident})



# -----------------------------------------
# DOWNLOAD INCIDENTS (Filtered, All Roles)
# -----------------------------------------
@login_required
def download_csv(request):
    query = request.GET.get("q", "")
    if query:
        incidents = Incident.objects.filter(
            failure__icontains=query
        ) | Incident.objects.filter(
            risk__icontains=query
        ) | Incident.objects.filter(
            date__icontains=query
        )
    else:
        incidents = Incident.objects.all()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="incidents.csv"'
    writer = csv.writer(response)
    writer.writerow(["date", "last_maintenance_date", "pressure", "temperature", "failure", "risk", "actions"])
    for i in incidents:
        writer.writerow([i.date, i.last_maintenance_date, i.pressure, i.temperature, i.failure, i.risk, i.actions])
    return response

# -----------------------------------------
# FULL PDF REPORT (All Roles)
# -----------------------------------------
@login_required
def download_pdf_report(request):
    incidents = Incident.objects.all().order_by("-date")

    # Summary counts
    total_incidents = incidents.count()
    high_risk = incidents.filter(risk__iexact="High").count()
    medium_risk = incidents.filter(risk__iexact="Medium").count()
    low_risk = incidents.filter(risk__iexact="Low").count()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("ONGC Maintenance - Incident Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Summary Table
    summary_data = [
        ["Total Incidents", "High Risk", "Medium Risk", "Low Risk"],
        [str(total_incidents), str(high_risk), str(medium_risk), str(low_risk)],
    ]
    summary_table = Table(summary_data, colWidths=[120, 120, 120, 120])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 18))

    # Incident Table
    data = [["Date", "Last Maint.", "Pressure", "Temperature", "Failure", "Risk", "Actions"]]
    for i in incidents:
        data.append([
            str(i.date),
            str(i.last_maintenance_date),
            str(i.pressure),
            str(i.temperature),
            i.failure,
            i.risk,
            i.actions,
        ])

    table = Table(data, repeatRows=1, colWidths=[70, 70, 60, 70, 80, 50, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="ONGC_Incident_Report.pdf")


@login_required
def notifications_list(request):
    notifications =  Notification.objects.order_by("-created_at")[:20]  # latest 20
    return render(request, "notifications.html", {"notifications": notifications})
