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

        this.datePickerInstance = flatpickr("#date", {
            defaultDate: new Date(),
            dateFormat: "d-m-Y",

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

    initializeTimePickers() {
        flatpickr("#start_time", {
            defaultDate: "16:00",
            enableTime: true,
            noCalendar: true,
            dateFormat: "H:00",
            time_24hr: false,
            minuteIncrement: 60
        });
    },

    loadMonthlyHours(month = null, year = null) {
        const now = new Date();
        month = month || now.getMonth() + 1;
        year = year || now.getFullYear();

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