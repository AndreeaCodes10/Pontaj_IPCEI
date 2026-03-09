import calendar
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.comments import Comment
from .models import Lab, LabMembership, User, WorkEntry
import zipfile
from io import BytesIO
from openpyxl.utils import get_column_letter
from collections import defaultdict

users = list(User.objects.all().order_by("last_name"))

def get_initials(user):
    first = user.first_name[:1].upper() if user.first_name else ""
    last = user.last_name[:1].upper() if user.last_name else ""
    return f"{first}{last}"

def AG_workbook(lab, month, year):

    wb = Workbook()
    ws = wb.active
    ws.title = "Pontaj"
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    header_fill = PatternFill(start_color="ab9896", end_color="ab9896", fill_type="solid")

    # ws.append([
    #     "User","Lab","Subactivitate","Livrabil","Individual","Members",
    #     "Data","Nr ore","Durata","Descriere activitate","Comentarii","Links"
    #     ])
    header = [
        "Data","Nr ore","Durata","User","Lab","Subactivitate","Descriere","Individual","Livrabil","Links"
        ]

    header += [get_initials(u) for u in users]

    header += [
    "Comentarii",
    "Validat L2",
    "Validat Aumovio",
    "Validat P. Demian"
    ]
    
    ws.append(header)

    # apply background fill to header row
    for col_idx in range(1, len(header) + 1):
        ws.cell(row=1, column=col_idx).fill = header_fill
    
    base_columns = 10 
    for idx, user in enumerate(users):
        col_idx = base_columns + 1 + idx
        full_name = f"{user.first_name} {user.last_name}"
        ws.cell(row=1, column=col_idx).comment = Comment(full_name, "")

    entries = WorkEntry.objects.select_related(
        "user", "lab", "subactivitate"
    ).filter(
        lab=lab,
        date__year=year,
        date__month=month
    )

    # for e in entries:
    #     ws.append([
    #         e.user.username if e.user else "Anonymous",
    #         e.lab.name,
    #         e.subactivitate.nume,
    #         e.livrabil,
    #         "Da" if e.individual else "Nu",
    #         ", ".join([u.username for u in e.members.all()]),
    #         e.date.strftime("%d-%m-%Y"),
    #         e.nr_ore,
    #         e.durata,
    #         e.activity_description,
    #         e.comentarii,
    #         e.links,
    #     ])

    for e in entries:
        member_ids = set(e.members.values_list("id", flat=True))
        nume_utilizator = e.user.first_name+" "+e.user.last_name
        if e.user:
            member_ids.add(e.user.id)
        member_columns = [
            "✓" if u.id in member_ids else ""
            for u in users
        ]
        row = [
            e.date.strftime("%d-%m-%Y"),
            e.nr_ore,
            e.durata,
            nume_utilizator if e.user else "Anonymous",
            e.lab.name,
            e.subactivitate.nume,
            e.activity_description,
            "Da" if e.individual else "Nu",
            e.livrabil,
            e.links,
        ]
        row += member_columns
        row += [
            e.comentarii,
        ]
        ws.append(row)

    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        ws.column_dimensions[column].width = max_length + 2

    # apply thin border to every cell in worksheet
    for row in ws.iter_rows():
        for cell in row:
            cell.border = thin_border

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
    merged_starts = {
        (r.min_row, r.min_col): r
        for r in ws.merged_cells.ranges
    }

    for col in range(1, ws.max_column + 1):
        max_len = 0
        for row in range(1, ws.max_row + 1):

            cell = ws.cell(row, col)
            if not cell.value:
                continue

            # Skip merged cells spanning multiple columns
            merged = merged_starts.get((row, col))
            if merged and merged.max_col > merged.min_col:
                continue

            max_len = max(max_len, len(str(cell.value)))

        ws.column_dimensions[get_column_letter(col)].width = max_len + 2

    ws.cell(row=row+2, column=1, value="Director/Responsabil Proiect Cercetare")
    ws.cell(row=row+3, column=1, value=f"Prof. dr. {director.last_name} {director.first_name}")

    ws.cell(row=row+2, column=last_col-2, value="Întocmit,")
    ws.cell(row=row+3, column=last_col-2, value=f"Prof. dr. {director.last_name} {director.first_name}")

    return wb


def build_sumary_sheet(wb, users, year, month):

    ws = wb.create_sheet("Sumary")
    month_name = calendar.month_name[month].lower()
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    bold = Font(bold=True)

    thin = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # ---------------- HEADER ----------------
    ws["A2"] = "Indirect partner name:"
    ws["A3"] = "Project name:"
    ws["A4"] = "Contract PI/C9/I4 nr:"

    for r in (2,3,4):
        ws.merge_cells(start_row=r,start_column=1,end_row=r,end_column=3)

    ws["A5"] = f"PONTAJ INDIVIDUAL PENTRU LUNA {month_name}"
    ws.merge_cells("A5:E5")
    ws["G5"] = f"ANUL {year}"

    ws["A7"] = f"PONTAJ CENTRALIZAT PENTRU LUNA: {month} ANUL {year}"
    ws.merge_cells("A7:E7")

    header_row = 9

    # ---------------- HEADER ----------------

    ws.merge_cells(start_row=header_row, start_column=1, end_row=header_row+1, end_column=1)
    ws.cell(header_row,1,"NR. CRT.").alignment = center
    ws.cell(header_row,1).font = bold

    ws.merge_cells(start_row=header_row, start_column=2, end_row=header_row+1, end_column=2)
    ws.cell(header_row,2,"PERSONAL ANGAJAT").alignment = center
    ws.cell(header_row,2).font = bold

    ws.merge_cells(start_row=header_row, start_column=3, end_row=header_row, end_column=6)
    ws.cell(header_row,3,"NUMAR ORE PE ACTIVITATI").alignment = center
    ws.cell(header_row,3).font = bold

    ws.cell(header_row+1,3,"A1")
    ws.cell(header_row+1,4,"A2")
    ws.cell(header_row+1,5,"A3")
    ws.cell(header_row+1,6,"A4")

    for c in range(3,7):
        ws.cell(header_row+1,c).alignment = center
        ws.cell(header_row+1,c).font = bold

    ws.merge_cells(start_row=header_row, start_column=7, end_row=header_row+1, end_column=7)
    ws.cell(header_row,7,"TOTAL zi").alignment = center
    ws.cell(header_row,7).font = bold

    # ---------------- FETCH ENTRIES ----------------

    entries = WorkEntry.objects.filter(
        user__in=users,
        date__year=year,
        date__month=month
    ).select_related("user","lab")

    # hours[(user_id, lab_id, day)] = hours
    hours = defaultdict(int)

    for e in entries:
        hours[(e.user_id, e.lab_id)] += e.nr_ore

    # determine labs automatically
    # labs = list({e.lab_id for e in entries})[:4]
    labs = list(dict.fromkeys(e.lab_id for e in entries))[:4]
    lab_index = {lab_id:i for i,lab_id in enumerate(labs)}

    # ---------------- TABLE BODY ----------------

    start_row = header_row + 2
    row = start_row

    total_lab = defaultdict(int)

    for i, user in enumerate(users, start=1):

        ws.cell(row,1,i).alignment = center
        ws.cell(row,2,f"{user.last_name} {user.first_name}")

        total_zi = 0

        for lab_id, i_lab in lab_index.items():
            col = 3 + i_lab

            h = hours.get((user.id, lab_id), 0)

            ws.cell(row,col,h)

            total_zi += h
            total_lab[lab_id] += h

        ws.cell(row,7,total_zi).alignment = center

        row += 1

    # ---------------- MONTH TOTALS ----------------

    ws.cell(row,1,"TOTAL LAB").font = bold
    grand_total = 0

    for lab_id,i in lab_index.items():

        col = 3 + i
        val = total_lab[lab_id]

        ws.cell(row,col,val).font = bold
        ws.cell(row,col).alignment = center

        grand_total += val

    ws.cell(row,7,grand_total).font = bold
    ws.cell(row,7).alignment = center

    # ---------------- BORDERS ----------------

    for r in range(header_row, row+1):
        for c in range(1,8):
            ws.cell(r,c).border = thin

    ws.cell(row+4,2,"Aprobat,")
    ws.cell(row+5,2,"Director de proiect,")
    ws.merge_cells(start_row=row+4,start_column=2,end_row=row+4,end_column=3)
    ws.cell(row+4,4,"Avizat,")
    ws.cell(row+5,4,"Coordonator achizitii si resursa umana,")
    ws.merge_cells(start_row=row+5,start_column=4,end_row=row+5,end_column=7)

    # auto width
    merged_starts = {
        (r.min_row, r.min_col): r
        for r in ws.merged_cells.ranges
    }

    for col in range(1, ws.max_column + 1):
        max_len = 0
        for row in range(1, ws.max_row + 1):

            cell = ws.cell(row, col)
            if not cell.value:
                continue

            # Skip merged cells spanning multiple columns
            merged = merged_starts.get((row, col))
            if merged and merged.max_col > merged.min_col:
                continue

            max_len = max(max_len, len(str(cell.value)))

        ws.column_dimensions[get_column_letter(col)].width = max_len + 2


def conti_workbook(lab, users, month, year, director):

    days = calendar.monthrange(year, month)[1]
    month_name = calendar.month_name[month].lower()

    wb = Workbook()
    wb.remove(wb.active)

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    center_wrapped = Alignment(horizontal="center", vertical="center", wrap_text=True)
    bold = Font(bold=True)

    weekend_fill = PatternFill(start_color="E82F32", end_color="E82F32", fill_type="solid")

    thin = Border(*(Side(style="thin"),)*4)
    thick = Border(*(Side(style="thick"),)*4)

    for user in users:

        ws = wb.create_sheet(f"{user.last_name}_{user.first_name}")

        # ---------------- HEADER ----------------
        ws["A2"] = "Indirect partner name:"
        ws["A3"] = "Project name:"
        ws["A4"] = "Contract PI/C9/I4 nr:"

        for r in (2,3,4):
            ws.merge_cells(start_row=r,start_column=1,end_row=r,end_column=3)

        ws["A6"] = f"PONTAJ INDIVIDUAL PENTRU LUNA {month_name}"
        ws.merge_cells("A6:E6")
        ws["G6"] = f"ANUL {year}"

        ws["A7"] = f"NUME SI PRENUME: {user.last_name} {user.first_name}"
        ws.merge_cells("A7:E7")

        # ------------- ACTIVITIES TABLE -------------
        start = 9

        ws.cell(start,1,"Activitate")
        ws.cell(start,2,"Denumire activitate sumar")
        ws.merge_cells(start_row=start,start_column=2,end_row=start,end_column=5)

        ws.cell(start,6,"Mapare activitate partener direct")
        ws.merge_cells(start_row=start,start_column=6,end_row=start,end_column=10)

        for i in range(1,9):
            r = start+i
            ws.cell(r,1,f"A{i}")
            ws.merge_cells(start_row=r,start_column=2,end_row=r,end_column=5)
            ws.merge_cells(start_row=r,start_column=6,end_row=r,end_column=10)

        for r in range(start,start+9):
            for c in range(1,11):
                ws.cell(r,c).border=thin
        # ------------- DAILY TABLE -------------
        r0 = 20

        ws.cell(r0,1,"DATA").font=bold
        ws.merge_cells(start_row=r0,start_column=1,end_row=r0+2,end_column=1)
        ws.cell(row=r0, column=1).alignment = center_wrapped

        ws.cell(r0,2,"ACTIVITATI").font=bold
        ws.merge_cells(start_row=r0,start_column=2,end_row=r0,end_column=9)
        ws.cell(row=r0, column=2).alignment = center_wrapped

        ws.cell(r0,10,"TOTAL").font=bold
        ws.merge_cells(start_row=r0,start_column=10,end_row=r0+2,end_column=10)
        ws.cell(row=r0, column=10).alignment = center_wrapped

        labs = list(
            WorkEntry.objects
            .filter(user=user,date__year=year,date__month=month)
            .values_list("lab",flat=True)
            .distinct()[:4]
        )

        lab_index = {lab_id:i for i,lab_id in enumerate(labs)}

        # headers A1-A4
        for i in range(4):
            col = 2+i*2
            ws.cell(r0+1,col,f"A{i+1}").font=bold
            ws.merge_cells(start_row=r0+1,start_column=col,end_row=r0+1,end_column=col+1)
            ws.cell(row=r0+1, column=col).alignment = center_wrapped

            ws.cell(r0+2,col,"nr ore")
            ws.cell(r0+2,col+1,"interval")

        # fetch entries
        entries = WorkEntry.objects.filter(
            user=user,
            date__year=year,
            date__month=month
        ).select_related("lab")

        hours = {}
        durata = {}

        for e in entries:
            key = (e.lab_id,e.date.day)
            hours[key] = e.nr_ore
            durata[key] = e.durata

        total_month = 0
        totals_lab = {lab_id:0 for lab_id in labs}

        # days loop
        for d in range(1,days+1):

            row = r0+2+d
            ws.cell(row,1,d).alignment=center

            total_day = 0

            for lab_id,i in lab_index.items():

                col = 2+i*2

                h = hours.get((lab_id,d),"")
                dur = durata.get((lab_id,d),"")

                ws.cell(row,col,h).alignment=center
                ws.cell(row,col+1,dur).alignment=center

                if isinstance(h,(int,float)):
                    total_day += h
                    totals_lab[lab_id]+=h

            ws.cell(row,10,total_day)

            total_month += total_day

            if calendar.weekday(year,month,d)>=5:
                for c in range(1,11):
                    ws.cell(row,c).fill=weekend_fill

        # totals per lab
        end = r0+2+days+1
        ws.cell(end,1,"TOTAL Lab").font=bold

        for lab_id,i in lab_index.items():
            col = 2+i*2
            ws.cell(end,col,totals_lab[lab_id])

        ws.cell(end,10,total_month).font=bold

        # borders
        for r in range(r0,end+1):
            for c in range(1,11):
                ws.cell(r,c).border=thin

        ws.cell(end+2,5,"Semnătura,")
        ws.cell(end+5,2,"Aprobat,")
        ws.cell(end+6,2,"Director de proiect,")
        ws.merge_cells(start_row=end+6,start_column=2,end_row=end+6,end_column=3)
        ws.cell(end+5,8,"Avizat,")
        ws.cell(end+6,8,"Coordonator achizitii si resursa umana,")
        ws.merge_cells(start_row=end+6,start_column=8,end_row=end+6,end_column=11)

        # auto width
        merged_starts = {
            (r.min_row, r.min_col): r
            for r in ws.merged_cells.ranges
        }

        for col in range(1, ws.max_column + 1):
            max_len = 0
            for row in range(1, ws.max_row + 1):

                cell = ws.cell(row, col)
                if not cell.value:
                    continue

                # Skip merged cells spanning multiple columns
                merged = merged_starts.get((row, col))
                if merged and merged.max_col > merged.min_col:
                    continue

                max_len = max(max_len, len(str(cell.value)))

            ws.column_dimensions[get_column_letter(col)].width = max_len + 2

    build_sumary_sheet(wb, users, year, month)
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

