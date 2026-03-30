const Export = {
    init() {
        this.exportBtn = document.getElementById("exportBtn");
        this.exportMonth = document.getElementById("exportMonth");
    },

    applyPermissions(user) {
        const canExport = !!user?.username;

        if (!this.exportBtn || !this.exportMonth) return;

        if (!canExport) {
            this.exportBtn.style.display = "none";
            this.exportMonth.style.display = "none";
            this.exportBtn.onclick = null;
            return;
        }

        this.exportBtn.style.display = "inline-block";
        this.exportMonth.style.display = "inline-block";

        // Use onclick to avoid stacking listeners as Auth.loadAuthArea runs multiple times.
        this.exportBtn.onclick = () => {
            const monthInput = this.exportMonth.value;
            if (!monthInput) {
                alert("Selecteaza luna pentru export.");
                return;
            }

            const [year, month] = monthInput.split("-");
            const labId = window.currentLabId || document.getElementById("lab")?.value;

            if (!labId || labId === "undefined") {
                alert("Selecteaza un lab inainte de export.");
                return;
            }

            window.location.href =
                `/api/export-monthly-sheet/?lab_id=${labId}&month=${month}&year=${year}`;
        };
    }
};
