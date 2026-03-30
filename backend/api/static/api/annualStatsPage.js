const AnnualStatsPage = {
    init() {
        this.labSelect = document.getElementById("lab");
        this.yearSelect = document.getElementById("yearSelect");
        this.tableHost = document.getElementById("annualStatsTable");

        Auth.init();
        this.readQueryDefaults();
        this.setDefaultYear();
        this.attachEvents();
        this.loadLabs();
    },

    readQueryDefaults() {
        const params = new URLSearchParams(window.location.search || "");
        const qLab = params.get("lab");
        const qYear = params.get("year");

        if (qLab) this.initialLabId = String(qLab);
        const yearInt = qYear ? parseInt(qYear, 10) : null;
        if (this.yearSelect && yearInt) {
            this.yearSelect.value = String(yearInt);
        }
    },

    setDefaultYear() {
        if (!this.yearSelect || this.yearSelect.value) return;
        this.yearSelect.value = String(new Date().getFullYear());
    },

    attachEvents() {
        if (this.labSelect) {
            this.labSelect.addEventListener("change", () => this.refresh());
        }
        if (this.yearSelect) {
            this.yearSelect.addEventListener("change", () => this.refresh());
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

    async refresh() {
        if (!this.tableHost) return;

        const labId = this.labSelect?.value;
        const year = this.yearSelect?.value;

        if (!labId || !year) {
            this.tableHost.innerHTML = "";
            return;
        }

        Auth.loadAuthArea(labId);

        const url = `/api/members-yearly-hours/?lab=${encodeURIComponent(labId)}&year=${encodeURIComponent(year)}`;
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
        const members = Array.isArray(data?.members) ? data.members : [];

        const monthLabels = ["Ian", "Feb", "Mar", "Apr", "Mai", "Iun", "Iul", "Aug", "Sep", "Oct", "Nov", "Dec"];

        const container = document.createElement("div");
        container.className = "entries-table-container";

        const table = document.createElement("table");
        table.className = "entries-table";

        const colgroup = document.createElement("colgroup");
        const nameCol = document.createElement("col");
        nameCol.style.width = "220px";
        colgroup.appendChild(nameCol);
        for (let i = 0; i < 12; i++) {
            const col = document.createElement("col");
            col.style.width = "70px";
            colgroup.appendChild(col);
        }
        const totalCol = document.createElement("col");
        totalCol.style.width = "80px";
        colgroup.appendChild(totalCol);
        table.appendChild(colgroup);

        const thead = document.createElement("thead");
        const hr = document.createElement("tr");
        const thName = document.createElement("th");
        thName.textContent = "Nume";
        hr.appendChild(thName);
        monthLabels.forEach((lbl) => {
            const th = document.createElement("th");
            th.textContent = lbl;
            hr.appendChild(th);
        });
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

            const monthly = Array.isArray(m?.monthly_hours) ? m.monthly_hours : [];
            for (let i = 0; i < 12; i++) {
                const td = document.createElement("td");
                const val = monthly[i] || 0;
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

