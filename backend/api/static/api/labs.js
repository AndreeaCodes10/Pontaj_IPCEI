const Labs = {

    init() {
        this.labSelect = document.getElementById("lab");
        if (!this.labSelect) return;
        // Kept as "subSelect" to minimize downstream changes from the old subactivitate UI.
        this.subSelect = document.getElementById("activitate");
        this.livrabilSelect = document.getElementById("livrabil");
        this.signatureGroup = document.getElementById("signatureGroup");

        this.attachEvents();
        this.loadLabs();
    },

    async loadLabs() {
        const response = await fetch("/api/labs/");
        const labs = await response.json();
        this.labMap = {};

        this.labSelect.innerHTML = "<option value=''>Select Labs</option>";

        labs.forEach(lab => {
            this.labMap[lab.id] = lab.name;

            const opt = document.createElement("option");
            opt.value = lab.id;
            opt.textContent = lab.name;
            this.labSelect.appendChild(opt);
        });

        if (Array.isArray(labs) && labs.length === 1) {
            this.labSelect.value = String(labs[0].id);
            this.labSelect.dispatchEvent(new Event("change"));
        }
    },

    attachEvents() {
        this.labSelect.addEventListener("change", async (e) => {
            const labId = e.target.value;
            window.currentLabId = labId;
            if (!labId) return;
            const user = await Auth.getCurrentUser(labId);
            Members.applyLabPermissions(user);
            Form.applyPermissions(user);
            Members.loadLabMembers(labId);
            Auth.loadAuthArea(labId); 
            await this.loadActivitati(labId);
            Calendar.loadCalendarForLab(labId);

            if (this.signatureGroup) {
                const labName = this.labMap[labId] || "";
                this.signatureGroup.style.display = labName === "Lab2" ? "block" : "none";
            }
        });

        if (this.subSelect) {
            this.subSelect.addEventListener("change", (e) => {
                const selected = e.target.selectedOptions[0];
                if (!selected) return;

                const descriereInput = document.getElementById("activity_description");
                if (descriereInput) {
                    descriereInput.value = selected.dataset.descriere || "";
                }

                // Activitate no longer carries livrabil; only set this if present.
                if (this.livrabilSelect && selected.dataset.livrabil) {
                    this.livrabilSelect.value = selected.dataset.livrabil;
                }
            });
        }
    },

    async loadActivitati(labId) {
        const response = await fetch(`/api/activitati/${labId}/`);
        const data = await response.json();

        if (!this.subSelect) return;
        this.subSelect.innerHTML = "<option value=''>Selecteaza activitate</option>";

        data.forEach(sub => {
            const option = document.createElement("option");
            option.value = sub.id;
            option.textContent = sub.nume;
            option.dataset.descriere = sub.descriere || "";
            this.subSelect.appendChild(option);
        });
    }
};
