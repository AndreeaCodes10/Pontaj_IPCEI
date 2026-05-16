const Entries = {
    entries: [],
    sortDirections: {},

    renderColGroup() {
        const cols = [
            { w: "7%" },
            { w: "7%" },
            { w: "10%" },
            { w: "8%" },
            { w: "10%" },
            { w: "48%" },
            { w: "6%" },
            { w: "4%" },
        ];
        return `<colgroup>${cols.map(c => `<col style="width:${c.w}">`).join("")}</colgroup>`;
    },

    async loadUserEntries(month, year) {
        const res = await fetch(`/api/monthly-user-entries/?lab=${window.currentLabId}&month=${month}&year=${year}`);
        const entries = await res.json();
        this.entries = Array.isArray(entries) ? entries : [];

        const container = document.getElementById("userEntries");
        if (!container) return;

        if (!this.entries.length) {
            container.innerHTML = "<p>No entries this month</p>";
            return;
        }

        container.innerHTML = `
            <div class="entries-table-container">
            <table class="entries-table">
                ${this.renderColGroup()}
                <thead>
                    <tr>
                    <th data-sort="date">Data</th>
                    <th data-sort="nr_ore">Nr Ore</th>
                    <th data-sort="durata">Durata</th>
                    <th data-sort="lab">Lab</th>
                    <th data-sort="activitate">Activitate</th>
                    <th data-sort="activity_description">Descriere</th>
                    <th></th>
                    <th></th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
            </div>
        `;

        this.renderBody();
        this.attachSorting();
        this.attachEdit();
        this.attachDelete();
    },

    parseDmyToMillis(dmy) {
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

        tbody.innerHTML = this.entries.map(e => `
            <tr data-id="${e.id}">
                <td data-field="date">${e.date ?? ""}</td>
                <td data-field="nr_ore">${e.nr_ore ?? ""}</td>
                <td data-field="durata">${e.durata ?? ""}</td>
                <td>${e.lab ?? ""}</td>
                <td>${e.activitate ?? ""}</td>
                <td>${e.activity_description ?? ""}</td>
                <td>
                    <button data-id="${e.id}" class="edit-entry">Edit</button>
                    <button data-id="${e.id}" class="save-entry" style="display:none;">Save</button>
                    <button data-id="${e.id}" class="cancel-entry" style="display:none;">Cancel</button>
                </td>
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
                    } else {
                        valA = String(valA ?? "");
                        valB = String(valB ?? "");
                    }

                    if (valA > valB) return 1 * dir;
                    if (valA < valB) return -1 * dir;
                    return 0;
                });

                this.renderBody();
                this.attachEdit();
                this.attachDelete();
            };
        });
    },

    attachEdit() {
        const parseDmyToIso = (dmy) => {
            const parts = String(dmy || "").trim().split("-");
            if (parts.length !== 3) return null;
            const dd = parseInt(parts[0], 10);
            const mm = parseInt(parts[1], 10);
            const yyyy = parseInt(parts[2], 10);
            if (!yyyy || !mm || !dd) return null;
            return `${yyyy}-${String(mm).padStart(2, "0")}-${String(dd).padStart(2, "0")}`;
        };

        const durationHours = (durata) => {
            const s = String(durata || "").trim();
            if (!s.includes("-")) return null;
            const [a, b] = s.split("-", 2).map(x => x.trim());
            const start = Number(a);
            const end = Number(b);
            if (!Number.isInteger(start) || !Number.isInteger(end)) return null;
            const diff = end - start;
            if (start < 0 || start > 23 || end < 1 || end > 24 || diff <= 0) return null;
            return diff;
        };

        const setEditing = (row, enabled) => {
            row.querySelectorAll("td[data-field]").forEach(td => {
                const field = td.dataset.field;
                const canEditField = ["date", "nr_ore", "durata"].includes(field);
                if (!canEditField) return;
                td.contentEditable = enabled ? "true" : "false";
                td.classList.toggle("is-editing", !!enabled);
                if (enabled) td.dataset.original = td.textContent ?? "";
            });

            const editBtn = row.querySelector(".edit-entry");
            const saveBtn = row.querySelector(".save-entry");
            const cancelBtn = row.querySelector(".cancel-entry");
            if (editBtn) editBtn.style.display = enabled ? "none" : "inline-block";
            if (saveBtn) saveBtn.style.display = enabled ? "inline-block" : "none";
            if (cancelBtn) cancelBtn.style.display = enabled ? "inline-block" : "none";
        };

        document.querySelectorAll(".edit-entry").forEach(btn => {
            btn.onclick = () => {
                const row = btn.closest("tr");
                if (!row) return;
                setEditing(row, true);
            };
        });

        document.querySelectorAll(".cancel-entry").forEach(btn => {
            btn.onclick = () => {
                this.renderBody();
                this.attachEdit();
                this.attachDelete();
            };
        });

        document.querySelectorAll(".save-entry").forEach(btn => {
            btn.onclick = async () => {
                const row = btn.closest("tr");
                const id = btn.dataset.id;
                if (!row || !id) return;

                const dateDmy = row.querySelector('td[data-field="date"]')?.textContent?.trim();
                const nrOreRaw = row.querySelector('td[data-field="nr_ore"]')?.textContent?.trim();
                const durata = row.querySelector('td[data-field="durata"]')?.textContent?.trim();

                const nrOre = parseInt(nrOreRaw || "", 10);
                if (!Number.isFinite(nrOre) || nrOre < 1 || nrOre > 12) {
                    alert("Nr. ore trebuie sa fie intre 1 si 12.");
                    return;
                }

                const durH = durationHours(durata);
                if (durH === null) {
                    alert("Durata format invalid (HH-HH).");
                    return;
                }
                if (durH !== nrOre) {
                    alert("Durata nu corespunde cu nr_ore. Te rog actualizeaza durata.");
                    return;
                }

                const isoDate = parseDmyToIso(dateDmy);
                if (!isoDate) {
                    alert("Data invalida. Foloseste formatul DD-MM-YYYY.");
                    return;
                }

                const payload = { date: isoDate, nr_ore: nrOre, durata: durata };

                const res = await fetch(`/api/work-entry/${id}/`, {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": this.getCSRFToken()
                    },
                    credentials: "same-origin",
                    body: JSON.stringify(payload)
                });

                if (!res.ok) {
                    let msg = "Eroare la salvare.";
                    try {
                        const data = await res.json();
                        if (data?.error) msg = data.error;
                    } catch {
                    }
                    alert(msg);
                    return;
                }

                const updated = await res.json();
                const idx = this.entries.findIndex(e => String(e.id) === String(id));
                if (idx >= 0) {
                    this.entries[idx] = { ...this.entries[idx], ...updated };
                }
                this.renderBody();
                this.attachEdit();
                this.attachDelete();
            };
        });
    },

    attachDelete() {
        document.querySelectorAll(".delete-entry").forEach(btn => {
            btn.onclick = async () => {
                const id = btn.dataset.id;

                if (!confirm("Stergi aceasta inregistrare?")) return;

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
                    alert("Eroare la stergere.");
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
