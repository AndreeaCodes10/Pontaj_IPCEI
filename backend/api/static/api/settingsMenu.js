const SettingsMenu = {
    getTheme() {
        return localStorage.getItem("theme") || "light";
    },

    applyTheme() {
        const link = document.getElementById("darkTheme");
        if (!link) return;

        const theme = this.getTheme();
        const isDark = theme === "dark";
        link.disabled = !isDark;

        document.querySelectorAll('[data-action="toggle-theme"]').forEach((btn) => {
            if (!(btn instanceof HTMLElement)) return;
            btn.textContent = isDark ? "Dark mode: On" : "Dark mode: Off";
        });

        // Apply dark mode to specific form fields (selects, textareas, and relevant inputs)
        const themeableElements = [
            document.getElementById("lab"),
            document.getElementById("activitate"),
            document.getElementById("livrabil"), // This is an input field
            document.getElementById("individual"),
            document.getElementById("jurnal"), // This is a textarea
            document.getElementById("scurta_descriere_jurnal"), // This is a textarea
            document.getElementById("comentarii"), // This is a textarea
            document.getElementById("links"), // This is a textarea
            ...document.querySelectorAll(".member-limit-input"), // From members.js, these are number inputs
        ];

        themeableElements.forEach(el => {
            if (el) {
                if (isDark) {
                    el.classList.add("dark-mode-field");
                } else {
                    el.classList.remove("dark-mode-field");
                }
            }
        });
    },

    initDropdown(menu) {
        const toggleBtn = menu.querySelector(".settings-btn");
        const dropdown = menu.querySelector(".settings-dropdown");
        if (!toggleBtn || !dropdown) return;

        const close = () => {
            dropdown.classList.remove("open");
        };

        toggleBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropdown.classList.toggle("open");
        });

        dropdown.addEventListener("click", (e) => {
            e.stopPropagation();
        });

        document.addEventListener("click", close);
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") close();
        });

        dropdown.querySelectorAll('[data-action="toggle-theme"]').forEach((btn) => {
            btn.addEventListener("click", () => {
                const current = this.getTheme();
                localStorage.setItem("theme", current === "dark" ? "light" : "dark");
                // Re-initialize Flatpickr instances to apply theme changes
                if (typeof MonthPickers !== "undefined" && MonthPickers?.init) {
                    MonthPickers.init();
                }
                if (typeof Calendar !== "undefined" && Calendar?.init) Calendar.init();
                this.applyTheme();
                close();
            });
        });
    },

    init() {
        this.applyTheme();
        document.querySelectorAll(".settings-menu").forEach((menu) => this.initDropdown(menu));
    }
};

document.addEventListener("DOMContentLoaded", () => {
    SettingsMenu.init();
});
