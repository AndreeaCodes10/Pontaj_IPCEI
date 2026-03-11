const Members = {

    applyLabPermissions(user) {

        const sidebar = document.getElementById("labMembersPanel");
        if (!sidebar) return;

        const isAdmin = user.global_role === "admin";
        const isDirector = user.lab_role === "director";

        sidebar.style.display = (isAdmin || isDirector) ? "block" : "none";
    },

    async loadLabMembers(labId) {

        const res = await fetch(`/api/labs/${labId}/members/`);
        const members = await res.json();

        const user = await Auth.getCurrentUser(labId);

        const list = document.getElementById("labMembersList");
        const membersBox = document.getElementById("members");

        if (membersBox) {

            membersBox.innerHTML = members.map(m => `
                <label class="member-pill">
                    <input type="checkbox" value="${m.id}">
                    ${m.username}
                </label>
            `).join("");

        }

        if (!list) return;

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
                    headers: { "X-CSRFToken": Utils.getCSRFToken() },
                    credentials: "same-origin"
                });

                this.loadLabMembers(labId);
            });

        });
    },

    async loadAllUsers(labId) {

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
                headers: { "X-CSRFToken": Utils.getCSRFToken() },
                credentials: "same-origin"
            });

            this.loadLabMembers(labId);
        };
    },

    async loadUsers() {

        const res = await fetch("/api/users/");
        const users = await res.json();

        const select = document.getElementById("userSelect");

        if (!select) return;

        select.innerHTML = '<option value="">Select user</option>';

        users.forEach(u => {
            select.innerHTML += `<option value="${u.id}">${u.username}</option>`;
        });

    }

};