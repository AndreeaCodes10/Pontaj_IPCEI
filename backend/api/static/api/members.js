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
        const canEditLimits =
            user?.global_role === "admin" || user?.lab_role === "director";

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

        list.innerHTML = members.map(m => `
            <div class="member-row" data-user-id="${m.id}">
                <div class="member-meta">
                    <div class="member-name">${m.username}</div>
                    <div class="member-role">${m.role}</div>
                </div>

                ${
                    canEditLimits
                        ? `
                            <div class="member-limit">
                                <input
                                    class="member-limit-input"
                                    type="number"
                                    min="0"
                                    max="1000"
                                    step="1"
                                    value="${Number.isFinite(m.monthly_hour_limit) ? m.monthly_hour_limit : ""}"
                                    aria-label="Monthly hour limit"
                                />
                                <button class="save-limit-btn" type="button">Save</button>
                            </div>
                          `
                        : `<div class="member-limit-readonly">${m.monthly_hour_limit ?? ""}</div>`
                }
            </div>
        `).join("");

        if (!canEditLimits) return;

        list.querySelectorAll(".member-row").forEach(row => {
            const uid = row.dataset.userId;
            const input = row.querySelector(".member-limit-input");
            const btn = row.querySelector(".save-limit-btn");
            if (!uid || !input || !btn) return;

            const save = async () => {
                btn.disabled = true;
                btn.textContent = "Saving...";

                try {
                    const limit = parseInt(input.value, 10);
                    if (!Number.isFinite(limit)) {
                        alert("Monthly hour limit must be a number.");
                        return;
                    }

                    const res = await fetch(
                        `/api/labs/${labId}/members/${uid}/monthly-hour-limit/`,
                        {
                            method: "PATCH",
                            headers: {
                                "Content-Type": "application/json",
                                "X-CSRFToken": Utils.getCSRFToken()
                            },
                            credentials: "same-origin",
                            body: JSON.stringify({ monthly_hour_limit: limit })
                        }
                    );

                    if (!res.ok) {
                        const err = await res.json().catch(() => ({}));
                        alert(err?.message || "Failed to update monthly hour limit.");
                        return;
                    }

                    btn.textContent = "Saved";
                    setTimeout(() => {
                        btn.textContent = "Save";
                    }, 800);
                } finally {
                    btn.disabled = false;
                }
            };

            btn.addEventListener("click", save);
        });
    }

};
