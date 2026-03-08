const Labs = {

    init() {
        this.labSelect = document.getElementById("lab");
        this.subSelect = document.getElementById("subactivitate");
        this.livrabilSelect = document.getElementById("livrabil");
        this.individualSelect = document.getElementById("individual");

        this.loadLabs();
        this.attachEvents();
    },

    async loadLabs() {
        const response = await fetch("/api/labs/");
        const labs = await response.json();

        this.labSelect.innerHTML = "<option value=''>Select Labs</option>";

        labs.forEach(lab => {
            const opt = document.createElement("option");
            opt.value = lab.id;
            opt.textContent = lab.name;
            this.labSelect.appendChild(opt);
        });
    },

    attachEvents() {
        this.labSelect.addEventListener("change", async (e) => {
            const labId = e.target.value;
            window.currentLabId = labId;
            if (!labId) return;
            const user = await Auth.getCurrentUser(labId);
            applyLabPermissions(user);
            loadLabMembers(labId);
            if (user.global_role === "admin" || user.lab_role === "director") {
                // loadLabMembers(labId);
                loadAllUsers(labId);
            }
            Auth.loadAuthArea(labId); 
            await this.loadSubactivitati(labId);
            Calendar.loadCalendarForLab(labId);
        });

        this.subSelect.addEventListener("change", (e) => {
            const selected = e.target.selectedOptions[0];
            if (!selected) return;

            this.livrabilSelect.value = selected.dataset.livrabil || "";
            this.individualSelect.value =
                selected.dataset.individual === "true" ? "true" : "false";
        });

        this.individualSelect.addEventListener("change", () => {
            const membersBox = document.getElementById("membersContainer");

            if (this.individualSelect.value === "false") {
                membersBox.style.display = "flex";
            } else {
                membersBox.style.display = "none";
            }
        });
    },

    async loadSubactivitati(labId) {
        const response = await fetch(`/api/subactivitati/${labId}/`);
        const data = await response.json();

        this.subSelect.innerHTML = "";

        data.forEach(sub => {
            const option = document.createElement("option");
            option.value = sub.id;
            option.textContent = sub.nume;
            option.dataset.livrabil = sub.livrabil;
            option.dataset.individual = sub.individual;
            this.subSelect.appendChild(option);
        });
    }
};

function applyLabPermissions(user) {
    const sidebar = document.getElementById("labMembersPanel");

    const isAdmin = user.global_role === "admin";
    const isDirector = user.lab_role === "director";

    if (isAdmin || isDirector) {
        sidebar.style.display = "block";
    } else {
        sidebar.style.display = "none";
    }
}

async function loadLabMembers(labId) {
    const res = await fetch(`/api/labs/${labId}/members/`);
    const members = await res.json();
    const user = await Auth.getCurrentUser(labId);
    const list = document.getElementById("labMembersList");
    const membersBox = document.getElementById("members");

    if (membersBox){
        membersBox.innerHTML = members.map(m => {
            return `
            <label class="member-pill">
                <input type="checkbox" value="${m.id}">
                ${m.username}
            </label>
        `;
    }).join("");

    }

    list.innerHTML = members.map(m => {

        const isAdmin = user.global_role === "admin";
        const isDirector = user.lab_role === "director";

        const canRemove =
            isAdmin ||
            (isDirector && m.username !== user.username);

        return `
            <div class="member-row">
                <span>${m.username}</span>
                ${
                    canRemove
                        ? `<button class="remove-member" data-id="${m.id}">✖</button>`
                        : ""
                }
            </div>
        `;
    }).join("");

    list.querySelectorAll(".remove-member").forEach(btn => {
        btn.addEventListener("click", async () => {
            const uid = btn.dataset.id;

            if (!confirm("Ștergi acest utilizator?")) return;

            await fetch(`/api/labs/${labId}/remove/${uid}/`, {
                method: "DELETE",
                headers: { "X-CSRFToken": getCSRFToken() },
                credentials: "same-origin"
            });

            loadLabMembers(labId);
        });
    });
}


async function loadAllUsers(labId) {
    const res = await fetch("/api/all-users/");
    const users = await res.json();

    const select = document.getElementById("addUserSelect");
    const btn = document.getElementById("addUserBtn");
    if (!select || !btn) return;

    select.innerHTML = users
        .map(u => `<option value="${u.id}">${u.username}</option>`)
        .join("");

    btn.onclick = async () => {
        const uid = select.value;

        await fetch(`/api/labs/${labId}/add/${uid}/`, {
            method: "POST",
            headers: { "X-CSRFToken": getCSRFToken() },
            credentials: "same-origin"
        });

        loadLabMembers(labId);
    };
}
// nu imi e clar de ce exista
async function loadUsers() {
    const res = await fetch("/api/users/");
    const users = await res.json();

    const select = document.getElementById("userSelect");
    select.innerHTML = '<option value="">Select user</option>';

    users.forEach(u => {
        select.innerHTML += `<option value="${u.id}">${u.username}</option>`;
    });
}
