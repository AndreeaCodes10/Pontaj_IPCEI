const EntriesPage = {

    init() {

        const labSelect = document.getElementById("lab");
        const monthInput = document.getElementById("monthSelect");

        this.initFilters(labSelect, monthInput);
        this.attachEvents(labSelect, monthInput);
    },

    async initFilters(labSelect, monthInput) {

        await Labs.init();
        Auth.init();

        const now = new Date();

        const params = new URLSearchParams(window.location.search);

        const labParam = params.get("lab");
        const monthParam = params.get("month");
        const yearParam = params.get("year");

        if (monthParam && yearParam) {
            monthInput.value = `${yearParam}-${String(monthParam).padStart(2,"0")}`;
        } else {
            monthInput.value = now.toISOString().slice(0,7);
        }

        if (labParam) {
            labSelect.value = labParam;
        }

        if (labSelect.options.length === 1) {
            labSelect.selectedIndex = 0;
        }

        window.currentLabId = labSelect.value;

        await Auth.loadAuthArea(window.currentLabId);

        this.updateEntries();
    },

    attachEvents(labSelect, monthInput) {

        labSelect.addEventListener("change", async () => {

            window.currentLabId = labSelect.value;

            await Auth.loadAuthArea(window.currentLabId);

            this.updateEntries();
        });

        monthInput.addEventListener("change", () => {
            this.updateEntries();
        });
    },

    updateEntries() {

        const lab = document.getElementById("lab").value;
        const monthValue = document.getElementById("monthSelect").value;

        if (!monthValue || !lab) return;

        const [year, month] = monthValue.split("-");

        window.currentLabId = lab;

        Entries.loadUserEntries(month, year);
    }

};