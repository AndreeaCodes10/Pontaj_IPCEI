const Export = {

    init() {
        this.exportBtn = document.getElementById("exportBtn");
        this.exportMonth = document.getElementById("exportMonth");
    },

    applyPermissions(user) {
        const canExport = user.is_director || user.global_role === "admin";

        if (!this.exportBtn || !this.exportMonth) return;

        if (canExport) {
            this.exportBtn.style.display = "inline-block";
            this.exportMonth.style.display = "inline-block";

            this.exportBtn.addEventListener("click", () => {
                const monthInput = this.exportMonth.value;

                if (!monthInput) {
                    alert("Selectează luna pentru export.");
                    return;
                }

                const [year, month] = monthInput.split("-");
                const labId = document.getElementById("lab").value;

                window.location.href =
                `/api/export-monthly-sheet/?lab_id=${labId}&month=${month}&year=${year}`;
            });

        } else {
            this.exportBtn.style.display = "none";
            this.exportMonth.style.display = "none";
        }
    }
};