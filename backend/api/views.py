from django.http import JsonResponse
from .models import Lab, LabMembership, Subactivitate, UserProfile, WorkEntry
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from .serializers import WorkEntrySerializer
import openpyxl
from datetime import datetime
import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseForbidden
import calendar
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Alignment, Font
from openpyxl.styles.borders import Border, Side


@csrf_exempt
def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("index")   # redirect to your main page
        else:
            return render(request, "api/login.html", {"error": "Invalid credentials"})

    return render(request, "api/login.html")
    
@api_view(['POST'])
def logout_view(request):
    logout(request)
    return JsonResponse({"message": "Logged out"})

@login_required
def get_pontaj_dates(request):
    '''Endpoint to get all dates where the user has work entries, for a given lab.'''
    lab_id = request.GET.get("lab")

    entries = WorkEntry.objects.filter(
        user=request.user,
        lab_id=lab_id
    )

    dates = list(entries.values_list("date", flat=True))

    formatted_dates = [d.strftime("%Y-%m-%d") for d in dates]

    return JsonResponse(formatted_dates, safe=False)

@login_required
def get_monthly_hours(request):
    '''Endpoint to get total hours worked by the user in a given month/year and lab, along with the monthly limit.'''
    user = request.user
    # read month/year from query params, default to current
    month = int(request.GET.get("month", datetime.now().month))
    year = int(request.GET.get("year", datetime.now().year))

    lab_id = request.GET.get("lab")
    if not lab_id:
        return JsonResponse({"error": "lab_id required"}, status=400)

    membership = LabMembership.objects.filter(
        profile=request.user.userprofile,
        lab_id=lab_id
    ).first()

    if not membership:
        return JsonResponse({
            "used_hours": 0,
            "limit": 0, 
            "remaining": 0
        })

    total = WorkEntry.objects.filter(
        user=request.user,
        lab_id=lab_id,
        date__month=month,
        date__year=year
    ).aggregate(total=Sum("nr_ore"))["total"] or 0

    limit = membership.monthly_hour_limit

    return JsonResponse({
        "used_hours": total,
        "limit": limit,
        "remaining": limit - total
    })

# @login_required
# def current_user(request):
#     if request.user.is_authenticated:
#         return JsonResponse({
#             "username": request.user.username,
#             "role": request.user.userprofile.role
#         })
#     return JsonResponse({"username": None})

@login_required
def current_user(request):
    '''Endpoint to get current user info, including global role and lab-specific role if lab_id is provided.'''
    user = request.user
    profile = user.userprofile

    lab_id = request.GET.get("lab_id")

    lab_role = None
    is_director = False

    if lab_id:
        membership = LabMembership.objects.filter(
            profile=profile,
            lab_id=lab_id
        ).first()

        if membership:
            lab_role = membership.role
            is_director = membership.role == "director"

    data = {
        "username": user.username,
        "global_role": profile.role,  # admin or not
        "lab_role": lab_role,
        "is_director": is_director,
    }

    return JsonResponse(data)

@login_required
def index(request):
    return render(request, "api/index.html")

def get_visible_labs(user):
    '''Helper function to get labs visible to the user based on their role. Admin sees all, director sees their labs, member sees their labs.'''
    profile = user.userprofile

    if profile.role == "admin":
        return Lab.objects.all()

    if profile.role == "director":
        return profile.labs.all()

    return profile.labs.all()

@login_required
def list_labs(request):
    labs = get_visible_labs(request.user)
    data = [{"id": l.id, "name": l.name} for l in labs]
    return JsonResponse(data, safe=False)

# def list_labs(request):
#     labs = Lab.objects.all()
#     data = [{"id": l.id, "name": l.name} for l in labs]
#     return JsonResponse(data, safe=False)


def list_subactivitati(request, lab_id):
    subs = Subactivitate.objects.filter(lab_id=lab_id)
    data = [{
        "id": s.id,
        "nume": s.nume,
        "descriere": s.descriere,
        "livrabil": s.livrabil,
    } for s in subs]
    return JsonResponse(data, safe=False)


@require_http_methods(["POST"])
def create_work_entry(request):
    '''Endpoint to create a work entry. Validates that the user is enrolled in the lab and does not exceed monthly hour limit.'''
    if request.method == "POST":
        data = json.loads(request.body)
        print("RECEIVED:", data)

        user = request.user
        profile = user.userprofile
        lab_id = data.get("lab")

        nr_ore = data.get("nr_ore")
        durata = data.get("durata")
        if not lab_id:
            return JsonResponse({"error": "Missing lab"}, status=400)

        if not data.get("nr_ore") or not data.get("durata"):
            return JsonResponse({"error": "Missing nr_ore or durata"}, status=400)
        
        if not data.get("nr_ore") or not data.get("durata"):
            return JsonResponse({"error": "Missing nr_ore or durata"}, status=400)
        
        membership = LabMembership.objects.filter(
            profile=profile,
            lab_id=lab_id
        ).first()

        if not membership:
            return JsonResponse(
            {"error": "User not enrolled in this lab"},
            status=403
        )

        date_obj = datetime.strptime(data["date"], "%Y-%m-%d")
        month = date_obj.month
        year = date_obj.year

        existing_hours = WorkEntry.objects.filter(
            user=user,
            lab_id=lab_id,
            date__month=month,
            date__year=year
        ).aggregate(total=Sum("nr_ore"))["total"] or 0

        new_hours = int(data["nr_ore"])

        profile = user.userprofile

        if existing_hours + new_hours > membership.monthly_hour_limit:
            return JsonResponse(
                {"error": "Monthly hour limit exceeded"},
                status=400
            )

        serializer = WorkEntrySerializer(data=data)

        if serializer.is_valid():
            serializer.save(user=user)
            return JsonResponse(serializer.data, status=201)

        print("SERIALIZER ERRORS:", serializer.errors)
        return JsonResponse(serializer.errors, status=400)

    return JsonResponse({"error": "POST only"}, status=400)

@login_required
def monthly_user_entries(request):
    '''Endpoint to get all work entries for the current user in a given month/year and lab.'''
    month = int(request.GET.get("month"))
    year = int(request.GET.get("year"))
    lab_id = request.GET.get("lab")

    entries = WorkEntry.objects.filter(
        user=request.user,
        lab_id=lab_id,
        date__month=month,
        date__year=year
    ).order_by("-date")

    data = [
        {
            "id": e.id,
            "date": e.date.strftime("%d-%m-%Y"),
            "lab": e.lab.name if e.lab else "",
            "subactivitate": e.subactivitate.nume if e.subactivitate else "",
            "livrabil": e.subactivitate.livrabil if e.subactivitate else "",
            "durata": e.durata,
            "activity_description": e.activity_description,
            "comentarii": e.comentarii,
        }
        for e in entries
    ]

    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["DELETE"])
def delete_work_entry(request, entry_id):
    '''Endpoint to delete a work entry. Only the user who created the entry can delete it.'''
    entry = get_object_or_404(WorkEntry, id=entry_id, user=request.user)
    entry.delete()
    return JsonResponse({"status": "ok"})

# -----------------------
# EXPORT TO EXCEL - OLD ENDPOINT (REPLACED BY MONTHLY SHEET EXPORT)
# -----------------------
# @require_http_methods(["GET"])
# def export_work_entries_excel(request):

#     if not request.user.is_authenticated:
#         return HttpResponseForbidden()

#     try:
#         role = request.user.userprofile.role
#     except UserProfile.DoesNotExist:
#         return HttpResponseForbidden()

#     if role not in ["prof", "admin"]:
#         return HttpResponseForbidden()
    
#     wb = openpyxl.Workbook()
#     ws = wb.active
#     ws.title = "Pontaj"

#     ws.append([
#         "User",
#         "Lab",
#         "Subactivitate",
#         "Livrabil",
#         "Individual",
#         "Data",
#         "Nr ore",
#         "Durata",
#         "Descriere activitate",
#         "Comentarii",
#         "Links",
#     ])

#     for e in WorkEntry.objects.select_related(
#         "user", "lab", "subactivitate"
#     ):
        
#         ws.append([
#             e.user.username if e.user else "Anonymous",
#             e.lab.name,
#             e.subactivitate.nume,
#             e.subactivitate.livrabil,
#             "Da" if e.individual else "Nu",
#             e.date.strftime("%d-%m-%Y"),
#             e.nr_ore,
#             e.durata,
#             e.activity_description,
#             e.comentarii,
#             e.links,
#         ])

#     # Make columns auto width
#     for col in ws.columns:
#         max_length = 0
#         column = col[0].column_letter
#         for cell in col:
#             try:
#                 max_length = max(max_length, len(str(cell.value)))
#             except:
#                 pass
#         ws.column_dimensions[column].width = max_length + 2
        
#     response = HttpResponse(
#         content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )
#     response["Content-Disposition"] = 'attachment; filename="pontaj.xlsx"'
#     wb.save(response)
#     return response

# @require_http_methods(["GET"])
# def export_monthly_sheet(request):

#     if not request.user.is_authenticated:
#         return HttpResponseForbidden()

#     role = request.user.userprofile.role
#     if role not in ["director", "admin"]:
#         return HttpResponseForbidden()

#     month = int(request.GET.get("month"))
#     year = int(request.GET.get("year"))

#     month_name = calendar.month_name[month].lower()
#     days_in_month = calendar.monthrange(year, month)[1]

#     wb = Workbook()
#     ws = wb.active

#     # --- HEADER ---
#     ws["A1"] = "Universitatea Politehnica Timișoara"
#     ws["A2"] = "Departamentul Electronică Aplicată"
#     ws["A4"] = "FOAIE COLECTIVĂ DE PREZENȚĂ - EVIDENȚA NUMĂRULUI DE ORE LUCRATE (PONTAJ)"
#     ws["A5"] = f"{month_name} {year}"

#     row = 7

#     users = User.objects.filter(userprofile__role__in=["student","director","admin"]).order_by("last_name")

#     for user in users:

#         ws.cell(row=row, column=1, value=f"{user.last_name} {user.first_name}")
#         row += 1

#         # --- days header ---
#         for d in range(1, days_in_month + 1):
#             ws.cell(row=row, column=d + 1, value=f"{d}")

#         ws.cell(row=row, column=days_in_month + 2, value="Semnătura")
#         row += 1

#         # --- fetch entries ---
#         entries = WorkEntry.objects.filter(
#             user=user,
#             date__year=year,
#             date__month=month
#         )

#         durata_by_day = defaultdict(list)
#         hours_by_day = defaultdict(int)

#         for e in entries:
#             day = e.date.day
#             durata_by_day[day].append(e.durata)
#             hours_by_day[day] += e.nr_ore

#         # --- durata row ---
#         for d in range(1, days_in_month + 1):
#             ws.cell(
#                 row=row,
#                 column=d + 1,
#                 value="\n".join(durata_by_day[d])
#             )
#         row += 1

#         # --- hours row ---
#         total_month = 0
#         for d in range(1, days_in_month + 1):
#             h = hours_by_day[d]
#             ws.cell(row=row, column=d + 1, value=h)
#             total_month += h

#         ws.cell(row=row, column=days_in_month + 2, value=total_month)

#         row += 3  # space between users

#     response = HttpResponse(
#         content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )
#     filename = f"pontaj_{month}_{year}.xlsx"
#     response["Content-Disposition"] = f'attachment; filename="{filename}"'

#     wb.save(response)
#     return response



# @require_http_methods(["GET"])
# def export_monthly_sheet(request):

#     if not request.user.is_authenticated:
#         return HttpResponseForbidden()

#     profile = request.user.userprofile
#     role = profile.role

#     if role not in ["director", "admin"]:
#         return HttpResponseForbidden()

#     month = int(request.GET.get("month"))
#     year = int(request.GET.get("year"))

#     month_name = calendar.month_name[month].lower()
#     days_in_month = calendar.monthrange(year, month)[1]

#     wb = Workbook()
#     ws = wb.active

#     # --- HEADER ---
#     ws["A1"] = "Universitatea Politehnica Timișoara"
#     ws["A2"] = "Departamentul Electronică Aplicată"
#     ws["A4"] = "FOAIE COLECTIVĂ DE PREZENȚĂ - EVIDENȚA NUMĂRULUI DE ORE LUCRATE (PONTAJ)"
#     ws["A5"] = f"{month_name} {year}"

#     # --- TEMPLATE STATIC ROWS ---
#     ws["A8"] = "Nume și prenume"
#     ws["A9"] = "cadru didactic"

#     # days header at row 9 starting B
#     for d in range(1, days_in_month + 1):
#         ws.cell(row=9, column=d + 1, value=d)

#     ws.cell(row=9, column=days_in_month + 2, value="Semnătura")

#     # --- USERS FILTERED BY LAB ---
#     users_qs = User.objects.filter(userprofile__role="member")

#     if role == "director":
#         users_qs = users_qs.filter(userprofile__lab=profile.lab)

#     users = users_qs.order_by("last_name")

#     row = 10  # first user row (A10)

#     for user in users:

#         ws.cell(row=row, column=1, value=f"{user.last_name} {user.first_name}")

#         # --- fetch entries ---
#         entries = WorkEntry.objects.filter(
#             user=user,
#             date__year=year,
#             date__month=month
#         )

#         durata_by_day = {}
#         hours_by_day = {}

#         for e in entries:
#             day = e.date.day
#             durata_by_day[day] = e.durata
#             hours_by_day[day] = e.nr_ore

#         # --- durata row (user row) ---
#         for d in range(1, days_in_month + 1):
#             ws.cell(row=row, column=d + 1, value=durata_by_day.get(d, ""))

#         # --- nr_ore row (below) ---
#         total_month = 0
#         for d in range(1, days_in_month + 1):
#             h = hours_by_day.get(d, "")
#             ws.cell(row=row + 1, column=d + 1, value=h)
#             if isinstance(h, (int, float)):
#                 total_month += h

#         ws.cell(row=row + 1, column=days_in_month + 2, value=total_month)

#         row += 2  # next user block

#     response = HttpResponse(
#         content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )
#     filename = f"pontaj_{month}_{year}.xlsx"
#     response["Content-Disposition"] = f'attachment; filename="{filename}"'

#     wb.save(response)
#     return response

