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

# @login_required
# def current_user(request):
#     '''Endpoint to get current user info, including global role and lab-specific role if lab_id is provided.'''
#     user = request.user
#     profile = user.userprofile

#     lab_id = request.GET.get("lab_id")

#     lab_role = None
#     is_director = False

#     if lab_id:
#         membership = LabMembership.objects.filter(
#             profile=profile,
#             lab_id=lab_id
#         ).first()

#         if membership:
#             lab_role = membership.role
#             is_director = membership.role == "director"

#     data = {
#         "username": user.username,
#         "global_role": profile.role,  # admin or not
#         "lab_role": lab_role,
#         "is_director": is_director,
#     }

#     return JsonResponse(data)

@login_required
def current_user(request):
    profile = request.user.userprofile
    lab_id = request.GET.get("lab")

    lab_role = None

    if lab_id:
        try:
            membership = LabMembership.objects.get(
                lab_id=lab_id,
                profile=profile
            )
            lab_role = membership.role
        except LabMembership.DoesNotExist:
            pass

    return JsonResponse({
        "username": request.user.username,
        "global_role": profile.role,
        "lab_role": lab_role
    })


@login_required
def index(request):
    return render(request, "api/index.html")

@login_required
def entries_page(request):
    return render(request, "api/entries.html")

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
        members = data.get("members", [])
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

        if not membership and profile.role != "admin":
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
            entry = serializer.save(user=user)

            if members:
                users = User.objects.filter(id__in=members)
                entry.members.set(users)
            return JsonResponse(serializer.data, status=201)

        print("SERIALIZER ERRORS:", serializer.errors)
        return JsonResponse(serializer.errors, status=400)

    return JsonResponse({"error": "POST only"}, status=400)

@login_required
def monthly_user_entries(request):
    '''Endpoint to get all work entries for the current user in a given month/year and lab.'''
    month = request.GET.get("month")
    year = request.GET.get("year")

    try:
        month = int(month)
        year = int(year)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid month/year"}, status=400)
    
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
            "nr_ore": e.nr_ore,
            "lab": e.lab.name if e.lab else "",
            "subactivitate": e.subactivitate.nume if e.subactivitate else "",
            "livrabil": e.livrabil if e.livrabil else "N/A",
            "durata": e.durata,
            "activity_description": e.activity_description,
            "individual": e.individual,
            "members": [u.username for u in e.members.all()],
            "links": e.links,
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
