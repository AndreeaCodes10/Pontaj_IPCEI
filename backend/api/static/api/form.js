const Form = {

    init() {
        this.form = document.getElementById("workEntryForm");
        this.startTimeInput = document.getElementById("start_time");
        this.nrOreInput = document.getElementById("nr_ore");
        this.durataInput = document.getElementById("durata");
        this.monthlySection = document.getElementById("monthlySection");
        this.toggleMonthlyBtn = document.getElementById("toggleMonthlyBtn");
        this.monthlyMonthInput = document.getElementById("exportMonth");
        this.saveMonthlyBtn = document.getElementById("saveMonthlyBtn");
        this.linksGroup = document.getElementById("linksGroup");
        this.livrabilGroup = document.getElementById("livrabilGroup");
        this.comentariiGroup = document.getElementById("comentariiGroup");
        this.signatureFileInput = document.getElementById("signatureFile");
        this.uploadSignatureBtn = document.getElementById("uploadSignatureBtn");
        this.canEditMonthly = true;
        this.isMonthlyOpen = false;
        this.attachEvents();
        this.setDefaultMonthlyMonth();
        this.applyMonthlyVisibility();
    },

    setDefaultMonthlyMonth() {
        if (!this.monthlyMonthInput) return;
        if (this.monthlyMonthInput.value) return;
        const now = new Date();
        const yyyy = now.getFullYear();
        const mm = String(now.getMonth() + 1).padStart(2, "0");
        this.monthlyMonthInput.value = `${yyyy}-${mm}`;
    },

    attachEvents() {
        this.form.addEventListener("submit", (e) => this.submit(e));

        const onRecalc = () => this.updateDurataPreview();
        this.startTimeInput?.addEventListener("change", onRecalc);
        this.startTimeInput?.addEventListener("input", onRecalc);
        this.nrOreInput?.addEventListener("change", onRecalc);
        this.nrOreInput?.addEventListener("input", onRecalc);

        this.toggleMonthlyBtn?.addEventListener("click", () => {
            this.isMonthlyOpen = !this.isMonthlyOpen;
            this.applyMonthlyVisibility();
            if (this.isMonthlyOpen) this.loadMonthlyMeta({ silent: true });
        });

        this.saveMonthlyBtn?.addEventListener("click", () => this.saveMonthlyMeta());

        this.monthlyMonthInput?.addEventListener("change", () => this.loadMonthlyMeta({ silent: true }));
        this.uploadSignatureBtn?.addEventListener("click", () => this.uploadSignature());

        document.getElementById("lab")?.addEventListener("change", () => {
            if (this.isMonthlyOpen) this.loadMonthlyMeta({ silent: true });
        });
        document.getElementById("activitate")?.addEventListener("change", () => {
            if (this.isMonthlyOpen) this.loadMonthlyMeta({ silent: true });
        });
    },

    applyMonthlyVisibility() {
        if (this.monthlySection) {
            this.monthlySection.style.display = this.isMonthlyOpen ? "block" : "none";
        }
        if (this.toggleMonthlyBtn) {
            this.toggleMonthlyBtn.textContent = this.isMonthlyOpen ? "Inchide lunar" : "Lunar";
        }
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
            alert("Completeaza Start Time si Nr. ore.");
            return;
        }

        if (nrOre > 12) {
            alert("Nr. ore nu poate fi mai mare de 12.");
            this.durataInput.value = "";
            return;
        }

        const endTime = this.addHoursToTime(startTime, nrOre);
        this.durataInput.value = `${startTime.slice(0,2)}-${endTime.slice(0,2)}`;
    },

    getMonthYearFromMonthInput() {
        const monthInput = this.monthlyMonthInput?.value || "";
        if (!monthInput) return null;
        const [yearStr, monthStr] = monthInput.split("-");
        const year = parseInt(yearStr, 10);
        const month = parseInt(monthStr, 10);
        if (!Number.isFinite(year) || !Number.isFinite(month)) return null;
        return { year, month };
    },

    getMonthlyContext() {
        const labId = window.currentLabId || document.getElementById("lab")?.value;
        const activitateId = document.getElementById("activitate")?.value;
        const my = this.getMonthYearFromMonthInput();

        return {
            labId,
            activitateId,
            month: my?.month,
            year: my?.year
        };
    },

    async loadMonthlyMeta({ silent = false } = {}) {
        const ctx = this.getMonthlyContext();
        if (!ctx.labId || !ctx.activitateId || !ctx.month || !ctx.year) {
            if (!silent) alert("Selecteaza lab, activitate si luna.");
            return;
        }

        const url =
            `/api/monthly-meta/?lab=${encodeURIComponent(ctx.labId)}` +
            `&activitate=${encodeURIComponent(ctx.activitateId)}` +
            `&month=${encodeURIComponent(ctx.month)}` +
            `&year=${encodeURIComponent(ctx.year)}`;

        const res = await fetch(url, { credentials: "same-origin" });
        if (!res.ok) {
            if (!silent) alert("Eroare la incarcarea campurilor lunare.");
            return;
        }

        const data = await res.json();
        const linksEl = document.getElementById("links");
        const livrabilEl = document.getElementById("livrabil");
        const comentariiEl = document.getElementById("comentarii");

        if (linksEl) linksEl.value = data?.links ?? "";
        if (livrabilEl) livrabilEl.value = data?.livrabil ?? "";
        if (comentariiEl) comentariiEl.value = data?.comentarii ?? "";
    },

    async saveMonthlyMeta({ silent = false } = {}) {
        const ctx = this.getMonthlyContext();
        if (!ctx.labId || !ctx.activitateId || !ctx.month || !ctx.year) {
            if (!silent) alert("Selecteaza lab, activitate si luna.");
            return;
        }

        const payload = {
            lab: ctx.labId,
            activitate: ctx.activitateId,
            month: ctx.month,
            year: ctx.year,
            links: document.getElementById("links")?.value || "",
            livrabil: document.getElementById("livrabil")?.value || "",
            comentarii: document.getElementById("comentarii")?.value || ""
        };

        const res = await fetch("/api/monthly-meta/", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Auth.getCSRFToken()
            },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            let msg = "Eroare la salvarea campurilor lunare.";
            try {
                const data = await res.json();
                if (data?.error) msg = data.error;
            } catch {
            }
            if (!silent) alert(msg);
            return;
        }

        if (!silent) alert("Salvat lunar.");
    },

    applyPermissions(user) {
        this.canEditMonthly = !!user?.username;
    },

    async uploadSignature() {
        const labId = window.currentLabId || document.getElementById("lab")?.value;
        if (!labId) {
            alert("Selecteaza un lab.");
            return;
        }

        const labName = Labs.labMap?.[labId];
        if (labName !== "Lab2") {
            alert("Semnatura PNG este disponibila doar pentru Lab2.");
            return;
        }

        const file = this.signatureFileInput?.files?.[0];
        if (!file) {
            alert("Selecteaza un fisier PNG.");
            return;
        }
        if (file.type !== "image/png" && !file.name.toLowerCase().endsWith(".png")) {
            alert("Doar fisiere PNG sunt permise.");
            return;
        }

        const formData = new FormData();
        formData.append("signature", file);

        const res = await fetch(`/api/labs/${encodeURIComponent(labId)}/signature/`, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "X-CSRFToken": Auth.getCSRFToken()
            },
            body: formData
        });

        if (!res.ok) {
            let msg = "Eroare la upload semnatura.";
            try {
                const data = await res.json();
                if (data?.error) msg = data.error;
            } catch {
            }
            alert(msg);
            return;
        }

        alert("Semnatura a fost salvata.");
    },

    async submit(e) {
        e.preventDefault();

        const formattedDate = this.convertToBackendDate(document.getElementById("date").value);
        if (formattedDate) {
            const [yy, mm, dd] = formattedDate.split("-").map(n => parseInt(n, 10));
            const dateObj = new Date(yy, (mm || 1) - 1, dd || 1);
            const dow = dateObj.getDay();
            if (dow === 0 || dow === 6) {
                alert("Ati incercat sa pontati in weekend");
                return;
            }
        }

        const startTime = this.startTimeInput?.value || "";
        const nrOre = parseInt(this.nrOreInput?.value || "", 10);
        if (!Number.isFinite(nrOre) || nrOre < 1 || nrOre > 12) {
            alert("Nr. ore trebuie sa fie intre 1 si 12.");
            return;
        }

        const endTime = this.addHoursToTime(startTime, nrOre);
        const durata = `${startTime.slice(0,2)}-${endTime.slice(0,2)}`;
        if (this.durataInput) this.durataInput.value = durata;

        const data = {
            lab: document.getElementById("lab").value,
            activitate: document.getElementById("activitate").value,
            livrabil: document.getElementById("livrabil").value,
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
            const lab = document.getElementById("lab").value;
            alert("Saved successfully!");
            this.form.reset();
            if (lab) Calendar.loadCalendarForLab(lab);
        } else {
            let message = "Error saving entry.";
            try {
                const dataResp = await response.json();
                if (dataResp.error) message = dataResp.error;
            } catch {
            }
            alert(message);
        }
    }
};
