const Form = {

    init() {
        this.form = document.getElementById("workEntryForm");
        this.startTimeInput = document.getElementById("start_time");
        this.nrOreInput = document.getElementById("nr_ore");
        this.durataInput = document.getElementById("durata");
        this.monthlySection = document.getElementById("monthlySection");
        this.linksGroup = document.getElementById("linksGroup");
        this.livrabilGroup = document.getElementById("livrabilGroup");
        this.comentariiGroup = document.getElementById("comentariiGroup");
        this.generateJurnalBtn = document.getElementById("generateJurnalBtn");
        this.canEditMonthly = true;
        this.attachEvents();
    },

    attachEvents() {
        this.form.addEventListener("submit", (e) => this.submit(e));

        const onRecalc = () => this.updateDurataPreview();
        this.startTimeInput?.addEventListener("change", onRecalc);
        this.startTimeInput?.addEventListener("input", onRecalc);
        this.nrOreInput?.addEventListener("change", onRecalc);
        this.nrOreInput?.addEventListener("input", onRecalc);

        this.generateJurnalBtn?.addEventListener("click", () => this.generateJurnal());
    },

    convertToBackendDate(dmy) {
        const [day, month, year] = dmy.split("-");
        return `${year}-${month}-${day}`;
    },

    addHoursToTime(timeStr, hoursToAdd) {
        const [h, m] = timeStr.split(":").map(Number);
        const date = new Date();
        date.setHours(h, m, 0, 0);
        date.setHours(date.getHours() + hoursToAdd);

        const hh = String(date.getHours()).padStart(2, "0");
        const mm = String(date.getMinutes()).padStart(2, "0");
        return `${hh}:${mm}`;
    },

    updateDurataPreview() {
        if (!this.durataInput) return;

        const startTime = this.startTimeInput?.value || "";
        const nrOre = parseInt(this.nrOreInput?.value || "", 10);
        if (!startTime || !Number.isFinite(nrOre) || nrOre <= 0) {
            alert("CompleteazÄƒ Start Time È™i Nr. ore.");
            return;
        }

        if (!startTime || !Number.isFinite(nrOre) || nrOre <= 0) {
            this.durataInput.value = "";
            return;
        }

        const endTime = this.addHoursToTime(startTime, nrOre);
        this.durataInput.value = `${startTime}-${endTime}`;
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

    getMonthYearFromDateInput() {
        const dateStr = document.getElementById("date")?.value || "";
        const parts = String(dateStr).split("-"); // DD-MM-YYYY
        if (parts.length === 3) {
            const month = parseInt(parts[1], 10);
            const year = parseInt(parts[2], 10);
            if (Number.isFinite(month) && Number.isFinite(year)) return { month, year };
        }
        const now = new Date();
        return { month: now.getMonth() + 1, year: now.getFullYear() };
    },

    async generateJurnal() {
        const labId = window.currentLabId || document.getElementById("lab")?.value;
        if (!labId) {
            alert("Selecteaza un lab.");
            return;
        }
        if (String(labId) !== "2") {
            alert("Jurnalul se genereaza doar pentru Lab 2.");
            return;
        }

        const monthInput = document.getElementById("jurnalMonth")?.value || "";
        let month;
        let year;
        if (monthInput) {
            const parts = monthInput.split("-"); // YYYY-MM
            year = parseInt(parts[0], 10);
            month = parseInt(parts[1], 10);
        } else {
            ({ month, year } = this.getMonthYearFromDateInput());
        }

        if (!Number.isFinite(month) || !Number.isFinite(year)) {
            alert("Selecteaza luna pentru jurnal.");
            return;
        }

        const url = `/api/generate-jurnal-docx/?lab=${encodeURIComponent(labId)}&month=${encodeURIComponent(month)}&year=${encodeURIComponent(year)}`;

        const res = await fetch(url, { credentials: "same-origin" });
        if (!res.ok) {
            let msg = "Eroare la generarea jurnalului.";
            try {
                const data = await res.json();
                if (data?.error) msg = data.error;
            } catch {
                // ignore
            }
            alert(msg);
            return;
        }

        const blob = await res.blob();
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `jurnal_${year}-${String(month).padStart(2, "0")}.docx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(a.href);
    },

    applyPermissions(user) {
        const canEditMonthly =
            user?.global_role === "admin" || user?.lab_role === "director";

        this.canEditMonthly = !!canEditMonthly;

        const canSeeJurnalForLab =
            !!(user?.can_see_jurnal ?? window.canSeeJurnal) &&
            String(window.currentLabId) === "2";

        const showMonthlySection = this.canEditMonthly || canSeeJurnalForLab;

        if (this.monthlySection) {
            this.monthlySection.style.display = showMonthlySection ? "block" : "none";
        }

        const showMonthlyFields = this.canEditMonthly;
        if (this.linksGroup) this.linksGroup.style.display = showMonthlyFields ? "flex" : "none";
        if (this.livrabilGroup) this.livrabilGroup.style.display = showMonthlyFields ? "flex" : "none";
        if (this.comentariiGroup) this.comentariiGroup.style.display = showMonthlyFields ? "flex" : "none";

        if (!showMonthlyFields) {
            const linksEl = document.getElementById("links");
            const livrabilEl = document.getElementById("livrabil");
            const comentariiEl = document.getElementById("comentarii");

            if (linksEl) linksEl.value = "";
            if (livrabilEl) livrabilEl.value = "";
            if (comentariiEl) comentariiEl.value = "";
        }
    },

    async submit(e) {
        e.preventDefault();

        const formattedDate = this.convertToBackendDate(
            document.getElementById("date").value
        );

        const startTime = this.startTimeInput?.value || "";
        const nrOre = parseInt(this.nrOreInput?.value || "", 10);

        const selectedMembers = [
            ...document.querySelectorAll("#members input:checked")
        ].map(cb => cb.value);

        const endTime = this.addHoursToTime(startTime, nrOre);
        const durata = `${startTime}-${endTime}`;
        if (this.durataInput) this.durataInput.value = durata;

        const data = {
            lab: document.getElementById("lab").value,
            activitate: document.getElementById("activitate").value,
            livrabil: document.getElementById("livrabil").value,
            individual: document.getElementById("individual").value,
            members: selectedMembers,
            date: formattedDate,
            durata: durata,
            nr_ore: nrOre,
            comentarii: document.getElementById("comentarii").value,
            links: document.getElementById("links").value,
        };

        if (!this.canEditMonthly) {
            data.livrabil = "";
            data.comentarii = "";
            data.links = "";
        }

        const jurnalEl = document.getElementById("jurnal");
        if (jurnalEl) {
            data.jurnal = jurnalEl.value;
        }

        const scurtaEl = document.getElementById("scurta_descriere_jurnal");
        if (scurtaEl) {
            data.scurta_descriere_jurnal = scurtaEl.value;
        }

        const response = await fetch("/api/work-entry/", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Auth.getCSRFToken()
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const lab = document.getElementById("lab").value;  // capture BEFORE reset

            alert("Saved successfully!");
            this.form.reset();

            if (lab) Calendar.loadCalendarForLab(lab);
        }else {
            alert("Error saving entry.");
        }
    }
};
