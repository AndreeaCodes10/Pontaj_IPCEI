import calendar
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from .models import Lab, LabMembership, User, WorkEntry
import zipfile
from io import BytesIO

def AG_workbook(lab, month, year):

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
            e.livrabil,
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

def upt_workbook(lab, users, month, year, director):
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


def conti_workbook(lab, users, month, year, director):
    days_in_month = calendar.monthrange(year, month)[1]
    month_name = calendar.month_name[month].lower()

    wb = Workbook()
    wb.remove(wb.active)

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    bold = Font(bold=True)
    center_wrapped = Alignment(horizontal="center", vertical="center", wrap_text=True)

    weekend_fill = PatternFill(start_color="E82F32", end_color="E82F32", fill_type="solid")

    last_col = days_in_month + 2

    row = 9

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    bold_border = Border(
        left=Side(style="thick"),
        right=Side(style="thick"),
        top=Side(style="thick"),
        bottom=Side(style="thick"),
    )

    for user in users:

        ws = wb.create_sheet(title=f"{user.last_name}_{user.first_name}")
        # ------------------HEADER--------------------------
        ws["A2"] = "Indirect partner name:"
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=3)

        ws["A3"] = "Project name:"
        ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=3)

        ws["A4"] = "Contract PI/C9/I4 nr:"
        ws.merge_cells(start_row=4, start_column=1, end_row=4, end_column=3)

        ws["A6"] = f"PONTAJ INDIVIDUAL PENTRU LUNA {month_name}"
        ws.merge_cells(start_row=6, start_column=1, end_row=6, end_column=5)
        ws.cell(row=6, column=1).alignment = center
        ws["G6"] = f"ANUL {year}"

        ws["A7"] = f" NUME SI PRENUME: {user.last_name} {user.first_name}"
        ws.merge_cells(start_row=7, start_column=1, end_row=7, end_column=5)
        #-------------------------------------------------------------------------

        ws.cell(row=row, column=1, value="Activitate")
        ws.cell(row=row, column=2, value="Denumire activitate sumar")
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
        ws.cell(row=row, column=6, value="Mapare activitate partener direct")
        ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=10)
        for j in (1,10):
            ws.cell(row=row, column=j).border = bold_border
                    
        for i in range(1, 9):
            rr = row + i

            ws.cell(row=rr, column=1, value=f"A{i}")

            ws.merge_cells(start_row=rr, start_column=2, end_row=rr, end_column=5)
            ws.merge_cells(start_row=rr, start_column=6, end_row=rr, end_column=10)

            for c in range(1, 11):
                ws.cell(row=rr, column=c).border = thin_border

        r=20
        ws.cell(row=r, column=1, value=f"DATA")
        ws.merge_cells(start_row=r, start_column=1, end_row=r+2, end_column=1)
        ws.cell(row=r, column=1).alignment = center_wrapped
        ws.cell(row=r, column=1).font = bold

        ws.cell(row=r, column=2, value=f"ACTIVITATI")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=9)
        ws.cell(row=r, column=2).alignment = center_wrapped
        ws.cell(row=r, column=2).font = bold

        ws.cell(row=r, column=10, value=f"TOTAL")
        ws.merge_cells(start_row=r, start_column=10, end_row=r+2, end_column=10)
        ws.cell(row=r, column=10).alignment = center_wrapped
        ws.cell(row=r, column=10).font = bold

        activities = ["A1","A2","A3","A4"]

        col = 2

        for act in activities:
            ws.cell(row=r+1, column=col, value=act)
            ws.cell(row=r+1, column=col).font = bold
            ws.merge_cells(start_row=r+1, start_column=col, end_row=r+1, end_column=col+1)

            ws.cell(row=r+2, column=col, value="nr ore")
            ws.cell(row=r+2, column=col+1, value="interval")

            col += 2

        # DAYS HEADER
        for d in range(1, days_in_month + 1):
            weekday = calendar.weekday(year, month, d)
            day_row = d + 2 + r

            cell = ws.cell(row=day_row, column=1, value=f"{d}")
            cell.alignment = center
            cell.font = bold

            if weekday >= 5:
                for col in range(1, 10):
                    ws.cell(row=day_row, column=col).fill = weekend_fill

        
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


        total = 0

        for d in range(1, days_in_month + 1):

            day_row = r + 2 + d

            durata = durata_by_day.get(d, "")
            ore = hours_by_day.get(d, "")

            ws.cell(row=day_row, column=2, value=ore)
            ws.cell(row=day_row, column=2).alignment = center_wrapped
            ws.cell(row=day_row, column=3, value=durata)
            ws.cell(row=day_row, column=3).alignment = center_wrapped

            if isinstance(ore, (int, float)):
                total += ore

        for r in range(r, day_row+1):
            for c in range(1, 11):
                ws.cell(row=r, column=c).border = thin_border

        # Make columns auto width
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
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

    wb_AG = AG_workbook(lab,month,year)
    wb_upt = upt_workbook(lab,users,month,year,request.user)
    wb_conti = conti_workbook(lab,users,month,year,request.user)

    AG_buffer = BytesIO()
    upt_buffer = BytesIO()
    conti_buffer = BytesIO()

    wb_AG.save(AG_buffer)
    wb_upt.save(upt_buffer)
    wb_conti.save(conti_buffer)

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer,"w") as z:
        z.writestr("pontaj_tabel_AG.xlsx",AG_buffer.getvalue())
        z.writestr(f"pontaj_poli_{lab.name}_{month}_{year}.xlsx",upt_buffer.getvalue())
        z.writestr(f"pontaj_conti_{lab.name}_{month}_{year}.xlsx",conti_buffer.getvalue())

    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer,content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="pontaj_{lab.name}_{month}_{year}.zip"'

    return response

