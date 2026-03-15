import calendar
from django.http import HttpResponse, HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side 
from .models import Lab, LabMembership, User, WorkEntry
from .excel_utils import apply_border
import zipfile
from io import BytesIO
from collections import defaultdict
from openpyxl.comments import Comment

def months_to_RO(month):
    lunile = ["ianuarie","februarie", "martie", "aprile",
              "mai", "iunie","iulie", "august",
              "septembrie", "octombrie", "noiembrie", "decembrie"]
    return lunile[month-1]

def get_initials(user):
    first = user.first_name[:1].upper() if user.first_name else ""
    last = user.last_name[:1].upper() if user.last_name else ""
    return f"{first}{last}"


def autofit_sheet(ws):
    """Adjust column widths and row heights based on cell content.
    Skips merged cells except for the top-left cell of each merge range.
    """
    merged_starts = {(r.min_row, r.min_col): r for r in ws.merged_cells.ranges}

    min_width = 8
    max_width = 55
    padding = 2

    wrap_columns = set()
    computed_widths = {}

    # columns (approximate "autofit" + clamp so long text doesn't explode layout)
    for col_cells in ws.columns:
        max_len = 0
        has_newlines = False
        column = col_cells[0].column_letter

        for cell in col_cells:
            if cell.value is None:
                continue

            merged = merged_starts.get((cell.row, cell.column))
            # only measure the top-left cell of a merge
            if merged and (cell.row != merged.min_row or cell.column != merged.min_col):
                continue

            text = str(cell.value)
            lines = text.splitlines()
            has_newlines = has_newlines or (len(lines) > 1)
            if not lines:
                continue

            raw_len = max((len(l) for l in lines))
            # if the cell spans multiple cols, distribute width
            colspan = 1
            if merged:
                colspan = merged.max_col - merged.min_col + 1
            effective_len = (raw_len + colspan - 1) // colspan  # ceil division
            max_len = max(max_len, effective_len)

        width = max_len + padding
        if width > max_width:
            wrap_columns.add(column)
        if has_newlines:
            wrap_columns.add(column)

        width = max(min_width, min(max_width, width))
        computed_widths[column] = width
        ws.column_dimensions[column].width = width

    # Enable wrapping for columns that contain long/multiline values.
    if wrap_columns:
        for column in wrap_columns:
            for cell in ws[column]:
                if cell.value is None:
                    continue
                merged = merged_starts.get((cell.row, cell.column))
                if merged and (cell.row != merged.min_row or cell.column != merged.min_col):
                    continue
                cell.alignment = cell.alignment.copy(wrap_text=True)

    # rows
    for row_cells in ws.iter_rows():
        max_lines = 1
        for cell in row_cells:
            if cell.value is None:
                continue
            merged = merged_starts.get((cell.row, cell.column))
            if merged and (cell.row != merged.min_row or cell.column != merged.min_col):
                continue
            text = str(cell.value)
            lines = text.splitlines() or [""]

            line_count = len(lines)
            column_letter = cell.column_letter
            if column_letter in wrap_columns and line_count == 1:
                # Roughly estimate wrapped lines from current column width.
                merged_width = computed_widths.get(column_letter, max_width)
                if merged:
                    # Sum widths across spanned columns (approx).
                    merged_width = 0
                    for col in range(merged.min_col, merged.max_col + 1):
                        letter = ws.cell(row=1, column=col).column_letter
                        merged_width += computed_widths.get(letter, max_width)

                chars_per_line = max(1, int(merged_width))
                est = (len(lines[0]) + chars_per_line - 1) // chars_per_line
                line_count = max(line_count, est)

            max_lines = max(max_lines, line_count)

        # Clamp to avoid extreme heights from very long text.
        ws.row_dimensions[row_cells[0].row].height = min(220, max_lines * 16)


LAB_JURNAL_ID = 2


def should_show_jurnal_field(profile):
    if not profile:
        return False
    return LabMembership.objects.filter(lab_id=LAB_JURNAL_ID, profile=profile).exists()


def AG_workbook(lab, month, year, show_jurnal=False):

    users = list(User.objects.all().order_by("last_name"))
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
    fixed_header = [
        "Data",
        "Nr ore",
        "Durata",
        "User",
        "Lab",
        "Activitate",
        "Descriere",
        "Individual",
        "Livrabil",
    ]
    if show_jurnal:
        fixed_header.append("Jurnal")
    fixed_header.append("Links")

    header = list(fixed_header)

    header += [get_initials(u) for u in users]

    header += [
    "Comentarii",
    "Validat L2",
    "Validat Aumovio",
    "Validat P. Demian"
    ]

    ws.append(header)
    for col_idx in range(1, len(header) + 1):
        ws.cell(row=1, column=col_idx).fill = header_fill
    
    base_columns = len(fixed_header)
    for idx, user in enumerate(users):
        col_idx = base_columns + 1 + idx
        full_name = f"{user.first_name} {user.last_name}"
        ws.cell(row=1, column=col_idx).comment = Comment(full_name, "")

    entries = WorkEntry.objects.select_related(
        "user", "lab", "activitate"
    ).filter(
        lab=lab,
        date__year=year,
        date__month=month
    )

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
            e.activitate.nume,
            e.activity_description,
            "Da" if e.individual else "Nu",
            e.livrabil or "",
        ]
        if show_jurnal:
            row.append(getattr(e, "jurnal", "") or "")
        row.append(e.links)
        row += member_columns
        row += [
            e.comentarii,
        ]
        ws.append(row)

    autofit_sheet(ws)

    for row in ws.iter_rows():
        for cell in row:
            cell.border = thin_border
    return wb

def upt_workbook(lab, users, month, year, director):
    days_in_month = calendar.monthrange(year, month)[1]
    month_name = months_to_RO(month)

    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    bold = Font(bold=True)
    center_wrapped = Alignment(horizontal="center", vertical="center", wrap_text=True)

    weekend_fill = PatternFill(start_color="E82F32", end_color="E82F32", fill_type="solid")

    last_col = days_in_month + 2

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Create a sheet for each user
    for user in users:
        ws = wb.create_sheet(title=f"{user.first_name}{user.last_name}")

        # HEADER
        ws["A1"] = "Universitatea Politehnica Timișoara"
        ws["A2"] = "Departamentul Electronică Aplicată"

        ws["A4"] = "FOAIE INDIVIDUALĂ DE PREZENȚĂ - EVIDENȚA NUMĂRULUI DE ORE LUCRATE (PONTAJ)"
        ws.merge_cells(start_row=4, start_column=1, end_row=4, end_column=last_col)
        ws.cell(row=4, column=1).alignment = center

        ws["A5"] = f"Laborator: {lab.name}"
        ws.merge_cells(start_row=5, start_column=1, end_row=5, end_column=last_col)
        ws.cell(row=5, column=1).alignment = center

        ws["A6"] = f"{month_name} {year}"
        ws.merge_cells(start_row=6, start_column=1, end_row=6, end_column=last_col)
        ws.cell(row=6, column=1).alignment = center

        row = 8

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

        # auto‑size sheet
        autofit_sheet(ws)

        final_row = row + 8
        ws.cell(row=final_row, column=1, value="Director/Responsabil Proiect Cercetare")
        ws.cell(row=final_row+1, column=1, value=f"Prof. dr. {director.last_name} {director.first_name}")

        ws.cell(row=final_row, column=last_col-2, value="Întocmit,")
        ws.cell(row=final_row+1, column=last_col-2, value=f"Prof. dr. {director.last_name} {director.first_name}")

    return wb

def mipe_workbook(lab, users, month, year, director):
    days_in_month = calendar.monthrange(year, month)[1]
    month_name = months_to_RO(month)

    wb = Workbook()
    wb.remove(wb.active)  # Remove default sheet

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    bold = Font(bold=True)
    center_wrapped = Alignment(horizontal="center", vertical="center", wrap_text=True)

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Create a sheet for each user
    for user in users:
        ws = wb.create_sheet(title=f"{user.first_name}{user.last_name}")

        # HEADER
        ws["B2"] = "Anexa 1"
        ws["B3"] = "Fișă individuala pontaj si de alocare a timpului de lucru"
        ws["B4"] = f"Luna {month_name} Anul {year}"
        for r in (2,3,4):
            ws.merge_cells(start_row=r,start_column=2,end_row=r,end_column=8)

        ws["B6"] = "Numele şi prenumele persoană"
        ws["B7"] = "CNP"
        ws["B8"] = "Funcția în Proiect¹"
        ws["B9"] = "Corespondenta cu HG Nr. 1188/2022 (50/35/25/15 euro)/Corespodența cu plafonul" \
                    " prevăzut în Ghidul Solicitantului/corespondenta cu Legea 153/2017"
        ws["B10"] = "Echivalent în lei a Limitei maxime în  euro/oră se calculează la cursul de " \
                    "schimb valutar comunicat de BNR pentru 1 euro la data semnării contractului de finanțare"
        ws["B11"] = "Denumire Lider/Partener"
        for r in range(6,12):
            ws.merge_cells(start_row=r,start_column=2,end_row=r,end_column=5)
            ws.cell(row=r, column=2).alignment = center

        # Add user information in F-I columns
        ws.merge_cells(start_row=6, start_column=6, end_row=6, end_column=9)
        ws.cell(row=6, column=6, value=f"{user.first_name} {user.last_name}")
        ws.cell(row=6, column=6).alignment = center
        ws.cell(row=6, column=6).font = bold

        ws.merge_cells(start_row=7, start_column=6, end_row=7, end_column=9)
        ws.cell(row=7, column=6, value=getattr(user, 'cnp', ''))
        ws.cell(row=7, column=6).alignment = center_wrapped
        ws.cell(row=7, column=6).font = bold

        for q in range(8,12):
            ws.merge_cells(start_row=q, start_column=6, end_row=q, end_column=9)
            ws.cell(row=8, column=6).alignment = center_wrapped

        # Contracts section
        num_contracts = 3  # TODO: Replace with dynamic endpoint call

        # Row 12 - Contract headers
        ws.merge_cells(start_row=12, start_column=2, end_row=13, end_column=2)
        ws.cell(row=12, column=2, value="Ziua")
        ws.cell(row=12, column=2).alignment = center_wrapped
        ws.cell(row=12, column=2).font = bold


        for i in range(num_contracts):
            start_col = 3 + (i * 2)
            end_col = start_col + 1
            ws.merge_cells(start_row=12, start_column=start_col, end_row=12, end_column=end_col)
            ws.cell(row=12, column=start_col, value=f"Contract Individual de Muncă/Act administrativ de numire. {i+1} ²")
            ws.cell(row=12, column=start_col).alignment = center_wrapped

        total_col = 3 + (num_contracts * 2)
        ws.merge_cells(start_row=12, start_column=total_col, end_row=13, end_column=total_col)
        ws.cell(row=12, column=total_col, value="Total ore lucrate/zi")
        ws.cell(row=12, column=total_col).alignment = center_wrapped
        ws.cell(row=12, column=total_col).font = bold

        # Row 13 - Contract details
        for i in range(num_contracts):
            col1 = 3 + (i * 2)
            col2 = col1 + 1
            ws.cell(row=13, column=col1, value="nr ore lucrate")
            ws.cell(row=13, column=col1).alignment = center
            ws.cell(row=13, column=col1).font = bold
            ws.cell(row=13, column=col2, value="interval orar")
            ws.cell(row=13, column=col2).alignment = center
            ws.cell(row=13, column=col2).font = bold

        row = 14
        col = 1
        activitati = list(lab.activitati.all().order_by('id')[:num_contracts])
        activitate_index = {act.id: i for i, act in enumerate(activitati)}

        # FETCH ENTRIES
        entries = WorkEntry.objects.filter(
            user=user,
            lab=lab,
            date__year=year,
            date__month=month
        ).select_related("lab")

        hours = {}
        durata = {}

        for e in entries:
            key = (e.activitate_id, e.date.day)
            hours[key] = e.nr_ore
            durata[key] = e.durata

        total_month = 0
        totals_activitate = {act.id: 0 for act in activitati}

        # DAYS HEADER
        for d in range(1, days_in_month + 1):
            ws.cell(row,2,d).alignment=center

            total_day = 0

            for act_id, i in activitate_index.items():

                col = 3+i*2

                h = hours.get((act_id, d), "")
                dur = durata.get((act_id, d), "")

                ws.cell(row,col,h).alignment=center
                ws.cell(row,col+1,dur).alignment=center

                if isinstance(h,(int,float)):
                    total_day += h
                    totals_activitate[act_id] += h

            ws.cell(row,total_col,total_day)

            total_month += total_day
            row=row+1

        end = row
        ws.cell(end,2,"Nr. total de ore").font=bold

        for act_id, i in activitate_index.items():
            col = 3+i*2
            ws.cell(end, col, totals_activitate[act_id])

        for j in range(1,9):
            ws.merge_cells(start_row=end+j, start_column=2, end_row=end+j, end_column=total_col)
            ws.cell(row=end+j, column=total_col).alignment = center_wrapped
        ws.cell(row=end+1, column=2, value="Subsemnatul/a declar, sub sancțiunea Codului penal, art. 326, privind falsul în declaraţii că \n" \
        "informațiile furnizate sunt adevărate și corecte în fiecare detaliu și înțeleg că AM/OI are dreptul să-mi solicite documente\n" \
        " doveditoare în scopul verificării și confirmării acestora")
        ws.cell(row=end+2,column=2, value=f"Nume și prenumele persoană: {user.first_name+" "+user.last_name}")
        ws.cell(row=end+3,column=2, value="Data:")
        ws.cell(row=end+5,column=2, value="Luat la cunoștință de către Responsabil Lider/Partener:")
        ws.cell(row=end+6,column=2, value="Semnătură:")
        ws.cell(row=end+7,column=2, value="Data:")

        
        for r in range(6, end+8):
            for c in range(2, total_col+1):
                ws.cell(row=r, column=c).border = thin_border

        # auto‑size columns and rows for this sheet
        autofit_sheet(ws)

    return wb


def build_sumary_sheet(wb, users, year, month, lab):

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
    ws.cell(header_row,7,"TOTAL").alignment = center
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
        hours[(e.user_id, e.activitate_id)] += e.nr_ore

    # determine labs automatically
    activitati = list(lab.activitati.all().order_by('id')[:4])
    activitate_index = {act.id: i for i, act in enumerate(activitati)}

    # ---------------- TABLE BODY ----------------

    start_row = header_row + 2
    row = start_row

    total_activitate = defaultdict(int)

    for i, user in enumerate(users, start=1):

        ws.cell(row,1,i).alignment = center
        ws.cell(row,2,f"{user.last_name} {user.first_name}")

        total_zi = 0

        for act_id, i_lab in activitate_index.items():
            col = 3 + i_lab

            h = hours.get((user.id, act_id), 0)

            ws.cell(row,col,h)

            total_zi += h
            total_activitate[act_id] += h

        ws.cell(row,7,total_zi).alignment = center

        row += 1

    # ---------------- MONTH TOTALS ----------------

    ws.cell(row,1,"TOTAL").font = bold
    grand_total = 0

    for act_id, i in activitate_index.items():

        col = 3 + i
        val = total_activitate[act_id]

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

    # auto‑size sheet
    autofit_sheet(ws)


def normalize_url(value):
        value = str(value or "").strip()
        if not value:
            return ""
        if value.startswith(("http://", "https://", "mailto:")):
            return value
        if value.startswith("www."):
            return f"https://{value}"
        return ""

def write_hyperlink(ws, row, col, raw_value):
    link_font = Font(color="215C98", underline="single")
    text = str(raw_value or "").strip()
    cell = ws.cell(row=row, column=col, value=text)
    url = normalize_url(text)
    if url:
        cell.hyperlink = url
        cell.font = link_font
    return cell

def conti_workbook(lab, users, month, year, director):

    days = calendar.monthrange(year, month)[1]
    month_name = months_to_RO(month)

    user_workbooks = []

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    center_wrapped = Alignment(horizontal="center", vertical="center", wrap_text=True)
    bold = Font(bold=True)
    color = Font(color="C00000", bold=True)
    wb_fill = PatternFill(start_color="DAF2D0", end_color="DAF2D0", fill_type="solid") 

    # Shared (director-entered) monthly fields are the same for every user sheet.
    activitati = list(lab.activitati.all().order_by("id"))
    activitate_index = {act.id: i for i, act in enumerate(activitati)}
    activitate_ids = {act.id for act in activitati}
    nr_Activitati = len(activitati)


    meta_entries = WorkEntry.objects.filter(
        user=director,
        lab=lab,
        date__year=year,
        date__month=month
    ).select_related("activitate").order_by("date", "id")

    links_by_act = {}
    livrabile_by_act = {}
    comentarii_by_act = {}

    for e in meta_entries:
        act_id = e.activitate_id
        if act_id not in activitate_ids:
            continue
        if e.links:
            links_by_act[act_id] = str(e.links).strip()
        if e.livrabil:
            livrabile_by_act[act_id] = str(e.livrabil).strip()
        if e.comentarii:
            comentarii_by_act[act_id] = str(e.comentarii).strip()

    membership_by_user_id = {
        m.profile.user_id: m
        for m in LabMembership.objects.filter(lab=lab, profile__user__in=users).select_related(
            "profile__user"
        )
    }

    for user in users:

        wb = Workbook()
        ws = wb.active
        ws.title = f"{user.last_name}_{user.first_name}"

        # ---------------- HEADER ----------------
        ws["A1"] = "Info:"
        ws["B1"] = f"Activitati de cercetare fundamentala in cadrul {lab}"
        ws["A2"] = (lab.titlu or "").strip()
        ws.cell(row=2, column=1).font = color
        ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=2)
        ws["A3"] = "PI:"
        ws["B3"] = "Universitatea Politehnica Timisoara"
        ws["A4"] = "Traductoare inteligente eficiente din punct de vedere energetic pentru sisteme auto  – inovație de-a lungul lanțului valoric (ASSET-IxC - UPT) "
        ws.merge_cells(start_row=4,start_column=1,end_row=4,end_column=2)
        ws.cell(row=4, column=1).font = color
        ws["A5"] = "NR:"
        ws["B5"] = "5.PI/I4/C9"

        ws["A7"] = "PONTAJ INDIVIDUAL PENTRU LUNA/ANUL:"
        ws["B7"] = f"{month_name.upper()}/{year}"
        ws.cell(row=7, column=1).font = bold

        ws["A8"] = "NUME SI PRENUME:"
        ws["B8"] = f"{user.last_name.upper()} {user.first_name}"
        ws.cell(row=8, column=1).font = bold

        ws["A10"] = "POST PROIECT"
        membership = membership_by_user_id.get(user.id)
        ws["B10"] = (membership.post or "") if membership else ""
        ws.cell(row=10, column=1).font = bold

        for r in (7,8,10):
            ws.cell(r,2).font = color
        for r in (1,3,5):
            for c in (1,2):
                ws.cell(r,c).font = bold
        for r in range(1,11):
            for c in range(1,3):
                ws.cell(r,c).alignment = center

        # Thin borders for the small header blocks
        apply_border(ws, 1, 1, 5, 2, thickness="thin")   # A1:B5
        apply_border(ws, 7, 1, 8, 2, thickness="thin")   # A7:B8
        apply_border(ws, 10, 1, 10, 2, thickness="thin") # A10

        # ------------- ACTIVITIES TABLE -------------
        start = 12

        ws.cell(start,1,"Activitate")
        ws.cell(start,2,"Denumire activitate sumar")
        ws.cell(start,3,"Scurta descriere activitate")
        ws.cell(start,4,"Link")
        ws.cell(start,5,"Livrabile")

        ws.cell(start,6,"Mapare activitate partener direct")
        ws.cell(start,7,"Comentarii/Scurta descriere actiuni cercetare")
        for c in range(1,8):
            ws.cell(start,c).font = bold
            ws.cell(start,c).alignment = center_wrapped

        # User entries for the daily table.
        entries = WorkEntry.objects.filter(
            user=user,
            lab=lab,
            date__year=year,
            date__month=month
        ).select_related("activitate")

        for i in range(1,nr_Activitati+1):
            r = start+i
            ws.cell(r,1,f"A{i}").font = bold
            ws.cell(row=r, column=1).alignment = center_wrapped

        # Fill the activity description block from admin-maintained Activitate.descriere.
        for i, act in enumerate(activitati):
            r = start + 1 + i
            ws.cell(r, 2, (act.denumire_activitate or "").strip() or act.nume)
            ws.cell(row=r, column=2).alignment = center_wrapped
            ws.cell(r, 3, act.descriere)
            ws.cell(row=r, column=3).alignment = center_wrapped
            act_id = act.id
            # Column 4: Link (from WorkEntry.links)
            link_cell = write_hyperlink(ws, r, 4, links_by_act.get(act_id, ""))
            link_cell.alignment = center_wrapped

            # Column 5: Livrabile (from WorkEntry.livrabil)
            liv_cell = write_hyperlink(ws, r, 5, livrabile_by_act.get(act_id, ""))
            liv_cell.alignment = center_wrapped

            # Comentarii (from WorkEntry.comentarii)
            comm_cell = ws.cell(r, 7, comentarii_by_act.get(act_id, ""))
            comm_cell.alignment = center_wrapped

        # Thin borders for the activitati block
        activitati_end_row = start + nr_Activitati
        last_activitati_col = 7
        apply_border(ws, start, 1, activitati_end_row, last_activitati_col, thickness="thin")

        # ------------- DAILY TABLE -------------
        r0 = 23

        ws.cell(r0,1,"DATA").font=bold
        ws.merge_cells(start_row=r0,start_column=1,end_row=r0+2,end_column=1)
        ws.cell(row=r0, column=1).alignment = center_wrapped

        ws.cell(r0,2,"ACTIVITATI").font=bold
        ws.merge_cells(start_row=r0,start_column=2,end_row=r0,end_column=9)
        ws.cell(row=r0, column=2).alignment = center_wrapped

        ws.cell(r0,10,"TOTAL").font=bold
        ws.merge_cells(start_row=r0,start_column=10,end_row=r0+2,end_column=10)
        ws.cell(row=r0, column=10).alignment = center_wrapped

        # headers A1-A4
        for i in range(len(activitati)):
            col = 2 + i*2

            cell = ws.cell(row=r0+1, column=col)
            cell.value = f"A{i+1}"
            cell.font = bold
            cell.alignment = center_wrapped

            ws.merge_cells(start_row=r0+1, start_column=col, end_row=r0+1, end_column=col+1)

            ws.cell(row=r0+2, column=col, value="nr ore").alignment=center
            ws.cell(row=r0+2, column=col+1, value="interval").alignment=center

        hours = {}
        durata = {}

        for e in entries:
            key = (e.activitate_id, e.date.day)
            hours[key] = e.nr_ore
            durata[key] = e.durata

        total_month = 0
        totals_activitate = {act.id: 0 for act in activitati}

        # days loop
        #va trebui inlocuit lab cu activitate
        for d in range(1,days+1):

            row = r0+2+d
            ws.cell(row,1,d).alignment=center

            total_day = 0

            for act_id, i in activitate_index.items():

                col = 2+i*2

                h = hours.get((act_id, d), "")
                dur = durata.get((act_id, d), "")

                ws.cell(row,col,h).alignment=center
                ws.cell(row,col+1,dur).alignment=center

                if isinstance(h,(int,float)):
                    total_day += h
                    totals_activitate[act_id] += h

            ws.cell(row,10,total_day)

            total_month += total_day

        # totals per lab
        end = r0+2+days+1
        ws.cell(end,1,"TOTAL Lab").font=bold

        for act_id, i in activitate_index.items():
            col = 2+i*2
            ws.cell(end, col, totals_activitate[act_id])
            

        ws.cell(end,10,total_month).font=bold

        # borders
        apply_border(ws, r0, 1, end, 10, thickness="thin")
                
        ws.cell(end+5,2,"Aprobat,")
        ws.cell(end+6,2,f"Responsabil laborator in cercetare-proiectare\n"
                        f"pentru activitatea {lab.name[-1]},")
        ws.merge_cells(start_row=end+6,start_column=2,end_row=end+6,end_column=3)
        ws.cell(end+7,2,f"{director.last_name.upper()} {director.first_name}")
        ws.cell(end+8,2,f"Semnătura")

        ws.cell(end+5,8,"Aprobat,")
        ws.cell(end+6,8,f"Responsabil AUMOVIO pentru activitatea {lab.name[-1]},")
        ws.cell(end+7,8,f"----Nume angajat conti----")
        ws.merge_cells(start_row=end+6,start_column=8,end_row=end+6,end_column=11)
        ws.cell(end+8,8,f"Semnătura")
        for r in range(1, end+9):
            for c in range(1,12):
                ws.cell(row=r, column=c).fill = wb_fill

        # auto‑size sheet
        autofit_sheet(ws)

        user_workbooks.append((user, wb))

    sumary_wb = Workbook()
    sumary_wb.remove(sumary_wb.active)
    build_sumary_sheet(sumary_wb, users, year, month, lab)
    return user_workbooks, sumary_wb

@require_http_methods(["GET"])
def export_excel(request):

    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    profile = request.user.userprofile

    lab_id = request.GET.get("lab_id")
    month = int(request.GET.get("month"))
    year = int(request.GET.get("year"))

    try:
        lab_id_int = int(lab_id)
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Invalid lab_id")

    lab = get_object_or_404(Lab, id=lab_id_int)

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

    director_membership = (
        LabMembership.objects.filter(lab=lab, role="director")
        .select_related("profile__user")
        .first()
    )
    director_user = (
        director_membership.profile.user
        if director_membership is not None
        else request.user
    )

    show_jurnal = should_show_jurnal_field(profile)
    include_ag = show_jurnal and lab.id == LAB_JURNAL_ID

    wb_AG = AG_workbook(lab, month, year, show_jurnal=show_jurnal) if include_ag else None
    wb_upt = upt_workbook(lab,users,month,year,director_user)
    conti_user_workbooks, conti_sumary_wb = conti_workbook(lab, users, month, year, director_user)
    wb_mipe =mipe_workbook(lab,users,month,year,director_user)

    AG_buffer = BytesIO() if wb_AG is not None else None
    upt_buffer = BytesIO()
    mipe_buffer = BytesIO()

    if wb_AG is not None and AG_buffer is not None:
        wb_AG.save(AG_buffer)
    wb_upt.save(upt_buffer)
    wb_mipe.save(mipe_buffer)

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer,"w") as z:
        if AG_buffer is not None:
            z.writestr("pontaj_tabel_AG.xlsx", AG_buffer.getvalue())
        z.writestr(f"pontaj_poli_{lab.name}_{month}_{year}.xlsx",upt_buffer.getvalue())
        conti_sumary_buffer = BytesIO()
        conti_sumary_wb.save(conti_sumary_buffer)
        z.writestr(
            f"pontaj_conti_sumary_{lab.name}_{month}_{year}.xlsx",
            conti_sumary_buffer.getvalue(),
        )
        for user, wb in conti_user_workbooks:
            user_buffer = BytesIO()
            wb.save(user_buffer)
            z.writestr(
                f"L{lab.name[-1]}_Pontaj_{month}_{months_to_RO(month)}_{user.last_name.upper()}_{user.first_name}.xlsx",
                user_buffer.getvalue(),
            )
        z.writestr(f"pontaj_MIPE_{lab.name}_{month}_{year}.xlsx",mipe_buffer.getvalue())

    zip_buffer.seek(0)

    response = HttpResponse(zip_buffer,content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="pontaj_{lab.name}_{month}_{year}.zip"'

    return response
