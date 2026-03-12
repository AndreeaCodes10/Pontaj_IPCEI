const Labs = {

    init() {
        this.labSelect = document.getElementById("lab");
        if (!this.labSelect) return;
        // Kept as "subSelect" to minimize downstream changes from the old subactivitate UI.
        this.subSelect = document.getElementById("activitate");
        this.livrabilSelect = document.getElementById("livrabil");
        this.individualSelect = document.getElementById("individual");

        this.loadLabs();
        this.attachEvents();
    },

    async loadLabs() {
        const response = await fetch("/api/labs/");
        const labs = await response.json();

        this.labSelect.innerHTML = "<option value=''>Select Labs</option>";

        labs.forEach(lab => {
            const opt = document.createElement("option");
            opt.value = lab.id;
            opt.textContent = lab.name;
            this.labSelect.appendChild(opt);
        });
    },

    attachEvents() {
        this.labSelect.addEventListener("change", async (e) => {
            const labId = e.target.value;
            window.currentLabId = labId;
            if (!labId) return;
            const user = await Auth.getCurrentUser(labId);
            Members.applyLabPermissions(user);
            Members.loadLabMembers(labId);
            if (user.global_role === "admin" || user.lab_role === "director") {
                // loadLabMembers(labId);
                Members.loadAllUsers(labId);
            }
            Auth.loadAuthArea(labId); 
            await this.loadActivitati(labId);
            Calendar.loadCalendarForLab(labId);
        });

        if (this.subSelect) {
            this.subSelect.addEventListener("change", (e) => {
                const selected = e.target.selectedOptions[0];
                if (!selected) return;

                const descriereInput = document.getElementById("activity_description");
                if (descriereInput) {
                    descriereInput.value = selected.dataset.descriere || "";
                }

                // Activitate no longer carries livrabil/individual; only set these if present.
                if (this.livrabilSelect && selected.dataset.livrabil) {
                    this.livrabilSelect.value = selected.dataset.livrabil;
                }

                if (this.individualSelect && selected.dataset.individual) {
                    this.individualSelect.value =
                        selected.dataset.individual === "true" ? "true" : "false";
                }
            });
        }

        if (this.individualSelect) {
            this.individualSelect.addEventListener("change", () => {
                const membersBox = document.getElementById("membersContainer");

                if (!membersBox) return;

                if (this.individualSelect.value === "false") {
                    membersBox.style.display = "flex";
                } else {
                    membersBox.style.display = "none";
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

