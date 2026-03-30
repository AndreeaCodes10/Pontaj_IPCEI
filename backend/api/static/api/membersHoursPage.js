const MembersHoursPage = {
    init() {
        this.labSelect = document.getElementById("lab");
        this.monthSelect = document.getElementById("monthSelect");
        this.tableHost = document.getElementById("membersHoursTable");

        Auth.init();
        this.readQueryDefaults();
        this.setDefaultMonth();
        if (typeof MonthPickers !== "undefined") {
            MonthPickers.init();
        }
        this.attachEvents();
        this.loadLabs();
    },

    readQueryDefaults() {
        const params = new URLSearchParams(window.location.search || "");
        const qLab = params.get("lab");
        const qMonth = params.get("month");
        const qYear = params.get("year");

        if (qLab) this.initialLabId = String(qLab);

        const monthInt = qMonth ? parseInt(qMonth, 10) : null;
        const yearInt = qYear ? parseInt(qYear, 10) : null;
        if (this.monthSelect && monthInt && yearInt && monthInt >= 1 && monthInt <= 12) {
            const mm = String(monthInt).padStart(2, "0");
            this.monthSelect.value = `${yearInt}-${mm}`;
        }
    },

    setDefaultMonth() {
        if (!this.monthSelect || this.monthSelect.value) return;
        const now = new Date();
        const yyyy = now.getFullYear();
        const mm = String(now.getMonth() + 1).padStart(2, "0");
        this.monthSelect.value = `${yyyy}-${mm}`;
    },

    attachEvents() {
        if (this.labSelect) {
            this.labSelect.addEventListener("change", () => this.refresh());
        }
        if (this.monthSelect) {
            this.monthSelect.addEventListener("change", () => this.refresh());
        }
    },

    async loadLabs() {
        if (!this.labSelect) return;

        const res = await fetch("/api/director-labs/");
        const labs = await res.json();

        this.labSelect.innerHTML = "<option value=''>Select Labs</option>";
        (labs || []).forEach((lab) => {
            const opt = document.createElement("option");
            opt.value = lab.id;
            opt.textContent = lab.name;
            this.labSelect.appendChild(opt);
        });

        if (this.initialLabId) {
            this.labSelect.value = this.initialLabId;
        }

        if (Array.isArray(labs) && labs.length === 1) {
            this.labSelect.value = String(labs[0].id);
        }

        await this.refresh();
    },

    getSelectedMonthYear() {
        const monthInput = this.monthSelect?.value;
        if (!monthInput) return null;
        const [year, month] = monthInput.split("-");
        const yearInt = parseInt(year, 10);
        const monthInt = parseInt(month, 10);
        if (!yearInt || !monthInt) return null;
        return { year: yearInt, month: monthInt };
    },

    async refresh() {
        if (!this.tableHost) return;

        const labId = this.labSelect?.value;
        const my = this.getSelectedMonthYear();

        if (!labId || !my) {
            this.tableHost.innerHTML = "";
            return;
        }

        Auth.loadAuthArea(labId);

        const url = `/api/members-monthly-hours/?lab=${encodeURIComponent(labId)}&month=${my.month}&year=${my.year}`;
        const res = await fetch(url);

        if (!res.ok) {
            const msg =
                res.status === 403
                    ? "Nu ai acces la acest lab."
                    : "Eroare la incarcarea datelor.";
            this.tableHost.innerHTML = `<p>${msg}</p>`;
            return;
        }

        const data = await res.json();
        this.renderTable(data);
    },

    renderTable(data) {
        const daysInMonth = data?.days_in_month || 0;
        const members = Array.isArray(data?.members) ? data.members : [];

        const container = document.createElement("div");
        container.className = "entries-table-container";

        const table = document.createElement("table");
        table.className = "entries-table";

        const colgroup = document.createElement("colgroup");
        const nameCol = document.createElement("col");
        nameCol.style.width = "220px";
        colgroup.appendChild(nameCol);
        for (let i = 0; i < daysInMonth; i++) {
            const col = document.createElement("col");
            col.style.width = "35px";
            colgroup.appendChild(col);
        }
        const totalCol = document.createElement("col");
        totalCol.style.width = "60px";
        colgroup.appendChild(totalCol);
        table.appendChild(colgroup);

        const thead = document.createElement("thead");
        const hr = document.createElement("tr");
        const thName = document.createElement("th");
        thName.textContent = "Nume";
        hr.appendChild(thName);
        for (let d = 1; d <= daysInMonth; d++) {
            const th = document.createElement("th");
            th.textContent = String(d);
            hr.appendChild(th);
        }
        const thTotal = document.createElement("th");
        thTotal.textContent = "Total";
        hr.appendChild(thTotal);
        thead.appendChild(hr);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");

        members.forEach((m) => {
            const tr = document.createElement("tr");

            const tdName = document.createElement("td");
            tdName.textContent = m?.name || "";
            tr.appendChild(tdName);

            const daily = Array.isArray(m?.daily_hours) ? m.daily_hours : [];
            for (let i = 0; i < daysInMonth; i++) {
                const td = document.createElement("td");
                const val = daily[i] || 0;
                td.textContent = val ? String(val) : "";
                tr.appendChild(td);
            }

            const tdTotal = document.createElement("td");
            tdTotal.textContent = m?.total ? String(m.total) : "";
            tr.appendChild(tdTotal);

            tbody.appendChild(tr);
        });

        table.appendChild(tbody);
        container.appendChild(table);

        this.tableHost.innerHTML = "";
        this.tableHost.appendChild(container);
    }
};
