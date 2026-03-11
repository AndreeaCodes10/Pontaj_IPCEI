const Entries = {

    async loadUserEntries(month, year) {

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

        this.attachSorting(entries, month, year);
        this.attachDelete();
    },

    attachSorting(entries, month, year) {

        let sortDirection = 1;

        document.querySelectorAll("th[data-sort]").forEach(header => {

            header.onclick = () => {

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

                this.loadUserEntries(month, year);
            };

        });
    },

    attachDelete() {

        document.querySelectorAll(".delete-entry").forEach(btn => {

            btn.onclick = async () => {

                const id = btn.dataset.id;

                if (!confirm("Ștergi această înregistrare?")) return;

                const res = await fetch(`/api/work-entry/${id}/`, {
                    method: "DELETE",
                    headers: {
                        "X-CSRFToken": this.getCSRFToken()
                    },
                    credentials: "same-origin"
                });

                if (res.ok) {
                    btn.closest("tr").remove();
                } else {
                    alert("Eroare la ștergere.");
                }
            };
        });
    },

    getCSRFToken() {
        return document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="))
            ?.split("=")[1];
    }

};