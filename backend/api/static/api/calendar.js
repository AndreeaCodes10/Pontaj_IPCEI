const Calendar = {

    datePickerInstance: null,

    init() {
        this.initializeTimePickers();
        // this.loadMonthlyHours();
        // const now = new Date();
        // loadUserEntries(now.getMonth() + 1, now.getFullYear());
        // loadUsers();
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
        const now = new Date();
        this.loadMonthlyHours(now.getMonth() + 1, now.getFullYear());
        loadUserEntries(now.getMonth() + 1, now.getFullYear());
        
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

async function loadUserEntries(month, year) {
    const res = await fetch(`/api/monthly-user-entries/?lab=${window.currentLabId}&month=${month}&year=${year}`);
    const entries = await res.json();

    const container = document.getElementById("userEntries");
    if (!container) return;

    if (!entries.length) {
        container.innerHTML = "<p>No entries this month</p>";
        return;
    }

    container.innerHTML = `
        <div class="entries-table-container">
        <table class="entries-table">
            <thead>
                <tr>
                <th data-sort="date">Data</th>
                <th data-sort="nr_ore">Nr Ore</th>
                <th data-sort="durata">Durata</th>
                <th data-sort="lab">Lab</th>
                <th data-sort="subactivitate">Subactivitate</th>
                <th data-sort="activity_description">Descriere</th>
                <th data-sort="individual">Individual</th>
                <th data-sort="livrabil">Livrabil</th>
                <th data-sort="links">Links</th>
                <th data-sort="comentarii">Comentarii</th>
                <th></th>
                </tr>
            </thead>
            <tbody>
                ${entries.map(e => `
                    <tr>
                        <td>${e.date}</td>
                        <td>${e.nr_ore}</td>
                        <td>${e.durata}</td>
                        <td>${e.lab}</td>
                        <td>${e.subactivitate}</td>
                        <td>${e.activity_description}</td>
                        <td>${e.individual ? "Da" : "Nu"}</td>
                        <td>${e.livrabil}</td>
                        <td><a href="${e.links}" target="_blank">${e.links}</a></td>
                        <td>${e.comentarii}</td>
                        <td>
                            <button data-id="${e.id}" class="delete-entry">✖</button>
                        </td>
                    </tr>
                `).join("")}
            </tbody>
        </table>
        </div>
        `;

    let sortDirection = 1;

    container.querySelectorAll("th[data-sort]").forEach(header => {
        header.addEventListener("click", () => {
            const key = header.dataset.sort;
            entries.sort((a, b) => {

                let valA = a[key];
                let valB = b[key];

                if (key === "date") {
                    valA = new Date(valA);
                    valB = new Date(valB);
                }

                if (valA > valB) return 1 * sortDirection;
                if (valA < valB) return -1 * sortDirection;
                return 0;

            });
            sortDirection *= -1;
            loadUserEntries(month, year);
        });

    });    

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