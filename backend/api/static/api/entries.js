const Entries = {
    entries: [],
    sortDirections: {},

    renderLinkCell(value) {
        const v = (value ?? "").toString();
        return v ? `<a href="${v}" target="_blank">${v}</a>` : "";
    },

    renderColGroup(showJurnal) {
        const cols = showJurnal
            ? [
                { w: "8%" },  // Data
                { w: "6%" },  // Nr Ore
                { w: "8%" },  // Durata
                { w: "6%" },  // Lab
                { w: "18%" }, // Activitate
                { w: "20%" }, // Descriere
                { w: "8%" },  // Individual
                { w: "12%" }, // Jurnal
                { w: "12%" }, // Descriere jurnal
                { w: "2%" },  // Delete
            ]
            : [
                { w: "10%" }, // Data
                { w: "8%" },  // Nr Ore
                { w: "10%" }, // Durata
                { w: "8%" },  // Lab
                { w: "22%" }, // Activitate
                { w: "30%" }, // Descriere
                { w: "8%" },  // Individual
                { w: "4%" },  // Delete
            ];

        return `<colgroup>${cols.map(c => `<col style="width:${c.w}">`).join("")}</colgroup>`;
    },

    async loadUserEntries(month, year) {
        const res = await fetch(
            `/api/monthly-user-entries/?lab=${window.currentLabId}&month=${month}&year=${year}`
        );
        const entries = await res.json();

        this.entries = Array.isArray(entries) ? entries : [];

        const container = document.getElementById("userEntries");
        if (!container) return;

        if (!this.entries.length) {
            container.innerHTML = "<p>No entries this month</p>";
            return;
        }

        // Render the table shell once; sorting only re-renders <tbody>.
        // const showJurnal = !!window.canSeeJurnal && String(window.currentLabId) === "2";
        const showJurnal = !!window.canSeeJurnal;

        container.innerHTML = `
            <div class="entries-table-container">
            <table class="entries-table">
                ${this.renderColGroup(showJurnal)}
                <thead>
                    <tr>
                    <th data-sort="date">Data</th>
                    <th data-sort="nr_ore">Nr Ore</th>
                    <th data-sort="durata">Durata</th>
                    <th data-sort="lab">Lab</th>
                    <th data-sort="activitate">Activitate</th>
                    <th data-sort="activity_description">Descriere</th>
                    <th data-sort="individual">Individual</th>
                    ${
                        showJurnal
                            ? `<th data-sort="jurnal">Jurnal</th><th data-sort="scurta_descriere_jurnal">Descriere jurnal</th>`
                            : ""
                    }
                    <th></th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
            </div>
        `;

        this.renderBody();
        this.attachSorting();
        this.attachDelete();
    },

    parseDmyToMillis(dmy) {
        // dmy expected: DD-MM-YYYY
        const parts = String(dmy || "").split("-");
        if (parts.length !== 3) return 0;
        const dd = parseInt(parts[0], 10);
        const mm = parseInt(parts[1], 10);
        const yyyy = parseInt(parts[2], 10);
        if (!yyyy || !mm || !dd) return 0;
        return new Date(yyyy, mm - 1, dd).getTime();
    },

    renderBody() {
        const tbody = document.querySelector("#userEntries tbody");
        if (!tbody) return;
        // const showJurnal = !!window.canSeeJurnal && String(window.currentLabId) === "2";
        const showJurnal = !!window.canSeeJurnal;

        tbody.innerHTML = this.entries.map(e => `
            <tr>
                <td>${e.date ?? ""}</td>
                <td>${e.nr_ore ?? ""}</td>
                <td>${e.durata ?? ""}</td>
                <td>${e.lab ?? ""}</td>
                <td>${e.activitate ?? ""}</td>
                <td>${e.activity_description ?? ""}</td>
                <td>${e.individual ? "Da" : "Nu"}</td>
                ${
                    showJurnal
                        ? `<td>${this.renderLinkCell(e.jurnal)}</td><td>${e.scurta_descriere_jurnal ?? ""}</td>`
                        : ""
                }
                <td>
                    <button data-id="${e.id}" class="delete-entry">x</button>
                </td>
            </tr>
        `).join("");
    },

    attachSorting() {
        document.querySelectorAll("th[data-sort]").forEach(header => {
            header.onclick = () => {
                const key = header.dataset.sort;
                const dir = this.sortDirections[key] ? -this.sortDirections[key] : 1;
                this.sortDirections[key] = dir;

                this.entries.sort((a, b) => {
                    let valA = a?.[key];
                    let valB = b?.[key];

                    if (key === "date") {
                        valA = this.parseDmyToMillis(valA);
                        valB = this.parseDmyToMillis(valB);
                    } else if (key === "nr_ore") {
                        valA = Number(valA ?? 0);
                        valB = Number(valB ?? 0);
                    } else if (key === "individual") {
                        valA = valA ? 1 : 0;
                        valB = valB ? 1 : 0;
                    } else {
                        valA = String(valA ?? "");
                        valB = String(valB ?? "");
                    }

                    if (valA > valB) return 1 * dir;
                    if (valA < valB) return -1 * dir;
                    return 0;
                });

                this.renderBody();
                this.attachDelete();
            };
        });
    },

    attachDelete() {
        document.querySelectorAll(".delete-entry").forEach(btn => {
            btn.onclick = async () => {
                const id = btn.dataset.id;

                if (!confirm("Ștergi această înregistrare?")) return;

                const res = await fetch(`/api/work-entry/${id}/`, {
                    method: "DELETE",
                    headers: {
                        "X-CSRFToken": this.getCSRFToken()
                    },
                    credentials: "same-origin"
                });

                if (res.ok) {
                    btn.closest("tr").remove();
                } else {
                    alert("Eroare la ștergere.");
                }
            };
        });
    },

    getCSRFToken() {
        return document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="))
            ?.split("=")[1];
    }
};
