const Calendar = {

    datePickerInstance: null,

    init() {
        this.initializeTimePickers();
        this.loadMonthlyHours();
        const now = new Date();
        loadUserEntries(now.getMonth() + 1, now.getFullYear());
        loadUsers();
    },

    async loadCalendarForLab(labId) {
        const response = await fetch(`/api/pontaj-dates/?lab_id=${labId}`);
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
                loadUserEntries(month, year);
            },

            onMonthChange: (monthObj) => {
                const month = monthObj.currentMonth + 1;
                const year = monthObj.currentYear;
                this.loadMonthlyHours(month, year);
                loadUserEntries(month, year);
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

        fetch(`/api/monthly-hours/?lab_id=${window.currentLabId}&month=${month}&year=${year}`)
            .then(res => res.json())
            .then(data => {
                document.getElementById("usedHours").innerText = data.used_hours;
                document.getElementById("limitHours").innerText = data.limit;
                document.getElementById("remainingHours").innerText = data.remaining;

                const percent = (data.used_hours / data.limit) * 100;
                document.getElementById("progressBar").style.width = percent + "%";
            });
    }

};

async function loadUsers() {
    const res = await fetch("/api/users/");
    const users = await res.json();

    const select = document.getElementById("userSelect");
    select.innerHTML = '<option value="">Select user</option>';

    users.forEach(u => {
        select.innerHTML += `<option value="${u.id}">${u.username}</option>`;
    });
}

async function loadUserEntries(month, year) {
    const res = await fetch(`/api/monthly-user-entries/?month=${month}&year=${year}`);
    const entries = await res.json();

    const container = document.getElementById("userEntries");
    if (!container) return;

    if (!entries.length) {
        container.innerHTML = "<p>No entries this month</p>";
        return;
    }

    container.innerHTML = `
        <table class="entries-table">
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Lab</th>
                    <th>Subactivitate</th>
                    <th>Livrabil</th>
                    <th>Descriere</th>
                    <th>Durata</th>
                    <th>Comentarii</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                ${entries.map(e => `
                    <tr>
                        <td>${e.date}</td>
                        <td>${e.lab}</td>
                        <td>${e.subactivitate}</td>
                        <td>${e.livrabil}</td>
                        <td>${e.activity_description}</td>
                        <td>${e.durata}</td>
                        <td>${e.comentarii}</td>
                        <td>
                            <button data-id="${e.id}" class="delete-entry">✖</button>
                        </td>
                    </tr>
                `).join("")}
            </tbody>
        </table>
        `;

    container.querySelectorAll(".delete-entry").forEach(btn => {
    btn.addEventListener("click", async () => {

        const id = btn.dataset.id;

        if (!confirm("Ștergi această înregistrare?")) return;

        const res = await fetch(`/api/work-entry/${id}/`, {
            method: "DELETE",
            headers: {
                "X-CSRFToken": getCSRFToken()
            },
            credentials: "same-origin"
        });

        if (res.ok) {
            btn.closest("tr").remove();
        } else {
            alert("Eroare la ștergere.");
        }
    });
});
}
function getCSRFToken() {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="))
        ?.split("=")[1];
}