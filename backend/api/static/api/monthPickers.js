const MonthPickers = {
    init() {
        if (typeof flatpickr !== "function") return;
        if (typeof monthSelectPlugin !== "function") return;
        if (typeof SettingsMenu === "undefined" || !SettingsMenu?.getTheme) return; // Ensure SettingsMenu is available

        const theme = SettingsMenu.getTheme();

        document.querySelectorAll('input[type="month"]').forEach((el) => {
            if (!el) return;

            // Destroy existing flatpickr instance if it exists
            if (el._flatpickr) {
                el._flatpickr.destroy();
            }

            flatpickr(el, {
                disableMobile: true,
                plugins: [
                    new monthSelectPlugin({
                        shorthand: true,
                        theme: theme // Use dynamic theme
                    })
                ]
            });
        });
    }
};
