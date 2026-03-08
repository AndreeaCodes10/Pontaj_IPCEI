const Form = {

    init() {
        this.form = document.getElementById("workEntryForm");
        this.attachEvents();
    },

    attachEvents() {
        this.form.addEventListener("submit", (e) => this.submit(e));
    },

    convertToBackendDate(dmy) {
        const [day, month, year] = dmy.split("-");
        return `${year}-${month}-${day}`;
    },

    addHoursToTime(timeStr, hoursToAdd) {
        const [h, m] = timeStr.split(":").map(Number);
        const date = new Date();
        date.setHours(h, m, 0, 0);
        date.setHours(date.getHours() + hoursToAdd);

        const hh = String(date.getHours()).padStart(2, "0");
        const mm = String(date.getMinutes()).padStart(2, "0");
        return `${hh}:${mm}`;
    },

    async submit(e) {
        e.preventDefault();

        const formattedDate = this.convertToBackendDate(
            document.getElementById("date").value
        );

        const startTime = document.getElementById("start_time").value;
        const nrOre = parseInt(document.getElementById("nr_ore").value, 10);

        const selectedMembers = [
            ...document.querySelectorAll("#members input:checked")
        ].map(cb => cb.value);

        const endTime = this.addHoursToTime(startTime, nrOre);
        const durata = `${startTime}-${endTime}`;

        const data = {
            lab: document.getElementById("lab").value,
            subactivitate: document.getElementById("subactivitate").value,
            livrabil: document.getElementById("livrabil").value,
            individual: document.getElementById("individual").value,
            members: selectedMembers,
            date: formattedDate,
            durata: durata,
            nr_ore: nrOre,
            activity_description: document.getElementById("activity_description").value,
            comentarii: document.getElementById("comentarii").value,
            links: document.getElementById("links").value,
        };

        const response = await fetch("/api/work-entry/", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Auth.getCSRFToken()
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const lab = document.getElementById("lab").value;  // capture BEFORE reset

            alert("Saved successfully!");
            this.form.reset();

            if (lab) Calendar.loadCalendarForLab(lab);
        }else {
            alert("Error saving entry.");
        }
    }
};