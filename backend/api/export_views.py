import calendar
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from .models import Lab, LabMembership, User, WorkEntry
import zipfile
from io import BytesIO

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
    
#     wb = Workbook()
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
def generate_entries_workbook(lab, month, year):

    wb = Workbook()
    ws = wb.active
    ws.title = "Pontaj"

    ws.append([
        "User","Lab","Subactivitate","Livrabil","Individual",
        "Data","Nr ore","Durata","Descriere activitate","Comentarii","Links"
    ])

    entries = WorkEntry.objects.select_related(
        "user", "lab", "subactivitate"
    ).filter(
        lab=lab,
        date__year=year,
        date__month=month
    )

    for e in entries:
        ws.append([
            e.user.username if e.user else "Anonymous",
            e.lab.name,
            e.subactivitate.nume,
            e.subactivitate.livrabil,
            "Da" if e.individual else "Nu",
            e.date.strftime("%d-%m-%Y"),
            e.nr_ore,
            e.durata,
            e.activity_description,
            e.comentarii,
            e.links,
        ])
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        ws.column_dimensions[column].width = max_length + 2

    return wb


# @require_http_methods(["GET"])
# def export_monthly_sheet():
#     '''Endpoint to export an Excel sheet with the monthly work entries for all users in a lab. Only accessible by admin or lab director.'''

#     if not request.user.is_authenticated:
#         return HttpResponseForbidden()

#     profile = request.user.userprofile

#     lab_id = request.GET.get("lab_id")
#     lab = get_object_or_404(Lab, id=lab_id)

#     is_admin = profile.role == "admin"

#     is_director = LabMembership.objects.filter(
#         lab=lab,
#         profile=profile,
#         role="director"
#     ).exists()

#     if not (is_admin or is_director):
#         return HttpResponseForbidden()

#     month = int(request.GET.get("month"))
#     year = int(request.GET.get("year"))

#     days_in_month = calendar.monthrange(year, month)[1]
#     month_name = calendar.month_name[month].lower()

#     # ---------- USERS BY LAB ----------
#     memberships = LabMembership.objects.filter(lab=lab).select_related("profile__user")

#     users = [m.profile.user for m in memberships]
#     users = sorted(users, key=lambda u: u.last_name)

#     # ---------- WORKBOOK ----------
#     wb = Workbook()
#     ws = wb.active

#     # styles
#     center = Alignment(horizontal="center", vertical="center", wrap_text=True)
#     bold = Font(bold=True)
#     center_wrapped = Alignment(horizontal="center", vertical="center", wrap_text=True)

#     weekend_fill = PatternFill(start_color="E82F32", end_color="E82F32", fill_type="solid")

#     # --- HEADER ---
#     last_col = days_in_month + 2
#     ws["A1"] = "Universitatea Politehnica Timișoara"
#     ws["A2"] = "Departamentul Electronică Aplicată"
#     ws["A4"] = "FOAIE COLECTIVĂ DE PREZENȚĂ - EVIDENȚA NUMĂRULUI DE ORE LUCRATE (PONTAJ)"
#     ws.merge_cells(start_row=4, start_column=1, end_row=4, end_column=last_col)
#     ws.cell(row=4, column=1).alignment = center

#     ws["A5"] = f"Laborator: {lab.name}"
#     ws.merge_cells(start_row=5, start_column=1, end_row=5, end_column=last_col)
#     ws.cell(row=5, column=1).alignment = center

#     ws["A6"] = f"{month_name} {year}"
#     ws.merge_cells(start_row=6, start_column=1, end_row=6, end_column=last_col)
#     ws.cell(row=6, column=1).alignment = center
    
#     # ---------- START POSITION ----------
#     row = 8

#     # border style for the first template block
#     thin_border = Border(
#         left=Side(style="thin"),
#         right=Side(style="thin"),
#         top=Side(style="thin"),
#         bottom=Side(style="thin"),
#     )
#     # apply borders from start_row to start_row+7 across all columns

#     for user in users:
        
#         director = request.user
#         # --- NUME ---
#         ws.cell(row=row, column=1, value="Nume și prenume cadru didactic")
#         ws.merge_cells(start_row=row, start_column=1, end_row=row + 1, end_column=1)
#         ws.cell(row=row, column=1).alignment = center_wrapped
#         # ws.cell(row=row, column=1).alignment = center

#         ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=last_col-1)

#         ws.cell(row=row + 2, column=1, value=f"{user.last_name} {user.first_name}")
#         ws.merge_cells(start_row=row + 2, start_column=1, end_row=row + 5, end_column=1)
#         ws.cell(row=row + 2, column=1).alignment = center_wrapped

#         ws.cell(row=row + 6, column=1, value="Total ore")
#         ws.cell(row=row + 6, column=1).alignment = center_wrapped

#         # --- DAYS HEADER ---
#         for d in range(1, days_in_month + 1):
#             weekday = calendar.weekday(year, month, d)
#             col = d + 1
#             cell = ws.cell(row=row + 1, column=col, value=f"{d}\n{month_name}")  
#             cell.alignment = center
#             cell.font = bold

#             # weekend coloring
#             if weekday >= 5:
#                 # cell.fill = weekend_fill
#                 for r in range(row + 1, row + 7):
#                     ws.cell(row=r, column=col).fill = weekend_fill

#         ws.cell(row=row , column=days_in_month + 2, value="Semnătura")
#         ws.merge_cells(start_row=row , start_column=days_in_month + 2, end_row=row + 1, end_column=days_in_month + 2)
#         ws.cell(row=row, column=days_in_month + 2).alignment = center

#         ws.merge_cells(start_row=row + 2, start_column=days_in_month + 2, end_row=row + 5, end_column=days_in_month + 2)

#         # --- FETCH ENTRIES ---
#         entries = WorkEntry.objects.filter(
#             user=user,
#             lab=lab,
#             date__year=year,
#             date__month=month
#         )

#         durata_by_day = {}
#         hours_by_day = {}

#         for e in entries:
#             durata_by_day[e.date.day] = e.durata
#             hours_by_day[e.date.day] = e.nr_ore

#         # --- DURATA ROW ---
#         for d in range(1, days_in_month + 1):
#             col = d + 1
#             ws.cell(row=row + 2, column=col, value=durata_by_day.get(d, ""))

#         # --- NR ORE ROW ---
#         total = 0
#         for d in range(1, days_in_month + 1):
#             col = d + 1
#             h = hours_by_day.get(d, "")
#             ws.cell(row=row + 6, column=col, value=h)
#             if isinstance(h, (int, float)):
#                 total += h

#         ws.cell(row=row + 6, column=days_in_month + 2, value=total)
#         for r in range(row, row + 7):
#             for c in range(1, last_col + 1):
#                 ws.cell(row=r, column=c).border = thin_border

#         # ---------- NEXT USER BLOCK ----------
#         row += 8  # exact spacing like template

#     # Make columns auto width
#     for col in ws.columns:
#         max_length = 0
#         column = col[0].column_letter
#         for cell in col:
#             try:
#                 max_length = max(max_length, len(str(cell.value)))
#             except:
#                 pass
#         if column == "A":
#             print("max len",max_length)
#             ws.column_dimensions[column].width = max_length - 5
#         else:
#             ws.column_dimensions[column].width = max_length

    
#     ws.cell(row=row, column=1, value="Director/Responsabil Proiect Cercetare")
#     ws.cell(row=row + 1, column=1, value=f"Prof. dr. {director.last_name} {director.first_name}")
#     ws.cell(row=row, column= last_col-2, value="Întocmit,")
#     ws.cell(row=row + 1, column=last_col-2, value=f"Prof. dr. {director.last_name} {director.first_name}")


#     # ---------- RESPONSE ----------
#     response = HttpResponse(
#         content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )

#     filename = f"pontaj_{lab.name}_luna_{month}_{year}.xlsx"
#     response["Content-Disposition"] = f'attachment; filename="{filename}"'

#     wb.save(response)
#     return response

def generate_monthly_workbook(lab, users, month, year, director):
    days_in_month = calendar.monthrange(year, month)[1]
    month_name = calendar.month_name[month].lower()

    wb = Workbook()
    ws = wb.active

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    bold = Font(bold=True)
    center_wrapped = Alignment(horizontal="center", vertical="center", wrap_text=True)

    weekend_fill = PatternFill(start_color="E82F32", end_color="E82F32", fill_type="solid")

    last_col = days_in_month + 2

    # HEADER
    ws["A1"] = "Universitatea Politehnica Timișoara"
    ws["A2"] = "Departamentul Electronică Aplicată"

    ws["A4"] = "FOAIE COLECTIVĂ DE PREZENȚĂ - EVIDENȚA NUMĂRULUI DE ORE LUCRATE (PONTAJ)"
    ws.merge_cells(start_row=4, start_column=1, end_row=4, end_column=last_col)
    ws.cell(row=4, column=1).alignment = center

    ws["A5"] = f"Laborator: {lab.name}"
    ws.merge_cells(start_row=5, start_column=1, end_row=5, end_column=last_col)
    ws.cell(row=5, column=1).alignment = center

    ws["A6"] = f"{month_name} {year}"
    ws.merge_cells(start_row=6, start_column=1, end_row=6, end_column=last_col)
    ws.cell(row=6, column=1).alignment = center

    row = 8

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for user in users:

        ws.cell(row=row, column=1, value="Nume și prenume cadru didactic")
        ws.merge_cells(start_row=row, start_column=1, end_row=row+1, end_column=1)
        ws.cell(row=row, column=1).alignment = center_wrapped

        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=last_col-1)

        ws.cell(row=row+2, column=1, value=f"{user.last_name} {user.first_name}")
        ws.merge_cells(start_row=row+2, start_column=1, end_row=row+5, end_column=1)
        ws.cell(row=row+2, column=1).alignment = center_wrapped

        ws.cell(row=row+6, column=1, value="Total ore")
        ws.cell(row=row+6, column=1).alignment = center_wrapped

        # DAYS HEADER
        for d in range(1, days_in_month + 1):
            weekday = calendar.weekday(year, month, d)
            col = d + 1

            cell = ws.cell(row=row+1, column=col, value=f"{d}\n{month_name}")
            cell.alignment = center
            cell.font = bold

            if weekday >= 5:
                for r in range(row+1, row+7):
                    ws.cell(row=r, column=col).fill = weekend_fill

        ws.cell(row=row, column=days_in_month+2, value="Semnătura")
        ws.merge_cells(start_row=row, start_column=days_in_month+2, end_row=row+1, end_column=days_in_month+2)
        ws.cell(row=row, column=days_in_month+2).alignment = center

        ws.merge_cells(start_row=row+2, start_column=days_in_month+2, end_row=row+5, end_column=days_in_month+2)

        # FETCH ENTRIES
        entries = WorkEntry.objects.filter(
            user=user,
            lab=lab,
            date__year=year,
            date__month=month
        )

        durata_by_day = {}
        hours_by_day = {}

        for e in entries:
            durata_by_day[e.date.day] = e.durata
            hours_by_day[e.date.day] = e.nr_ore

        for d in range(1, days_in_month+1):
            ws.cell(row=row+2, column=d+1, value=durata_by_day.get(d, ""))

        total = 0
        for d in range(1, days_in_month+1):
            h = hours_by_day.get(d, "")
            ws.cell(row=row+6, column=d+1, value=h)

            if isinstance(h, (int, float)):
                total += h

        ws.cell(row=row+6, column=days_in_month+2, value=total)

        for r in range(row, row+7):
            for c in range(1, last_col+1):
                ws.cell(row=r, column=c).border = thin_border

        row += 8

    # Make columns auto width
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        if column == "A":
            print("max len",max_length)
            ws.column_dimensions[column].width = max_length - 5
        else:
            ws.column_dimensions[column].width = max_length

    ws.cell(row=row, column=1, value="Director/Responsabil Proiect Cercetare")
    ws.cell(row=row+1, column=1, value=f"Prof. dr. {director.last_name} {director.first_name}")

    ws.cell(row=row, column=last_col-2, value="Întocmit,")
    ws.cell(row=row+1, column=last_col-2, value=f"Prof. dr. {director.last_name} {director.first_name}")

    return wb

@require_http_methods(["GET"])
def export_excel(request):

    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    profile = request.user.userprofile

    lab_id = request.GET.get("lab_id")
    month = int(request.GET.get("month"))
    year = int(request.GET.get("year"))

    lab = get_object_or_404(Lab,id=lab_id)

    is_admin = profile.role == "admin"

    is_director = LabMembership.objects.filter(
        lab=lab,
        profile=profile,
        role="director"
    ).exists()

    if not (is_admin or is_director):
        return HttpResponseForbidden()

    memberships = LabMembership.objects.filter(lab=lab).select_related("profile__user")
    users = sorted([m.profile.user for m in memberships], key=lambda u: u.last_name)

    wb_entries = generate_entries_workbook(lab,month,year)
    wb_monthly = generate_monthly_workbook(lab,users,month,year,request.user)

    entries_buffer = BytesIO()
    monthly_buffer = BytesIO()

    wb_entries.save(entries_buffer)
    wb_monthly.save(monthly_buffer)

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer,"w") as z:
        z.writestr("pontaj_tabel_AG.xlsx",entries_buffer.getvalue())
        z.writestr(f"pontaj_poli_{lab.name}_{month}_{year}.xlsx",monthly_buffer.getvalue())

    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer,content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="pontaj_{lab.name}_{month}_{year}.zip"'

    return response