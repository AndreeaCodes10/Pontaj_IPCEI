const Calendar = {

    datePickerInstance: null,

    init() {
        this.initializeTimePickers();
    },

    async loadCalendarForLab(labId) {
        const response = await fetch(`/api/pontaj-dates/?lab=${labId}`);
        const workedDates = await response.json();

        if (this.datePickerInstance) {
            this.datePickerInstance.destroy();
        }

        const theme = SettingsMenu.getTheme(); // Get theme from SettingsMenu

        const defaultDate = new Date();
        const dow = defaultDate.getDay(); // 0=Sun .. 6=Sat
        if (dow === 6) defaultDate.setDate(defaultDate.getDate() + 2);
        if (dow === 0) defaultDate.setDate(defaultDate.getDate() + 1);

        this.datePickerInstance = flatpickr("#date", {
            defaultDate,
            dateFormat: "d-m-Y",
            disableMobile: true,
            disable: [
                (date) => date.getDay() === 0 || date.getDay() === 6
            ],

            onChange: (selectedDates) => {
                if (!selectedDates.length) return;
                const month = selectedDates[0].getMonth() + 1;
                const year = selectedDates[0].getFullYear();
                this.loadMonthlyHours(month, year);
                Entries.loadUserEntries(month, year);
            },

            onMonthChange: (monthObj) => {
                const month = monthObj.currentMonth + 1;
                const year = monthObj.currentYear;
                this.loadMonthlyHours(month, year);
                Entries.loadUserEntries(month, year);
            },

            onDayCreate: (dObj, dStr, fp, dayElem) => {
                const y = dayElem.dateObj.getFullYear();
                const m = String(dayElem.dateObj.getMonth() + 1).padStart(2, "0");
                const d = String(dayElem.dateObj.getDate()).padStart(2, "0");
                const localDate = `${y}-${m}-${d}`;

                if (workedDates.includes(localDate)) {
                    dayElem.style.background = "#8e6bff";
                    dayElem.style.color = "white";
                    dayElem.style.borderRadius = "50%";
                }
            }
        });
        const now = new Date();
        this.loadMonthlyHours(now.getMonth() + 1, now.getFullYear());
        Entries.loadUserEntries(now.getMonth() + 1, now.getFullYear());
        
    },
    
    initializeDatePickerWithoutLab() {
        // This function is called when no lab is selected yet, or when re-initializing without a specific lab context.
        // It sets up a basic date picker without the workedDates highlighting.
        if (this.datePickerInstance) {
            this.datePickerInstance.destroy();
        }

        const defaultDate = new Date();
        const dow = defaultDate.getDay(); // 0=Sun .. 6=Sat
        if (dow === 6) defaultDate.setDate(defaultDate.getDate() + 2);
        if (dow === 0) defaultDate.setDate(defaultDate.getDate() + 1);

        const theme = SettingsMenu.getTheme();

        this.datePickerInstance = flatpickr("#date", {
            defaultDate,
            dateFormat: "d-m-Y",
            disableMobile: true,
            disable: [
                (date) => date.getDay() === 0 || date.getDay() === 6
            ],
            theme: theme,

            onChange: (selectedDates) => {
                if (!selectedDates.length) return;
                const month = selectedDates[0].getMonth() + 1;
                const year = selectedDates[0].getFullYear();
                this.loadMonthlyHours(month, year);
                Entries.loadUserEntries(month, year);
            },
        });
    },

    initializeTimePickers() {
        const theme = SettingsMenu.getTheme(); // Get theme from SettingsMenu

        this.startTimePickerInstance = flatpickr("#start_time", {
            defaultDate: "16:00",
            enableTime: true,
            noCalendar: true,
            dateFormat: "H:00",
            theme: theme, // Use dynamic theme
        });
    },

    loadMonthlyHours(month = null, year = null) {
        const now = new Date();
        month = month || now.getMonth() + 1;
        year = year || now.getFullYear();

        // Only load monthly hours if a lab is selected
        if (!window.currentLabId) {
            document.getElementById("usedHours").innerText = "0";
            document.getElementById("limitHours").innerText = "0";
            document.getElementById("remainingHours").innerText = "0";
            document.getElementById("progressBar").style.width = "0%";
            return;
        }
        fetch(`/api/monthly-hours/?lab=${window.currentLabId}&month=${month}&year=${year}`)
            .then(res => res.json())
            .then(data => {
                console.log("monthly-hours response:", data);
                if (!data || data.used_hours === undefined) {
                    console.error("Invalid monthly-hours response:", data);
                    return;
                }
                document.getElementById("usedHours").innerText = data.used_hours;
                document.getElementById("limitHours").innerText = data.limit;
                document.getElementById("remainingHours").innerText = data.remaining;

                const percent = (data.used_hours / data.limit) * 100;
                document.getElementById("progressBar").style.width = percent + "%";
            });
    }

};

function getCSRFToken() {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="))
        ?.split("=")[1];
}
