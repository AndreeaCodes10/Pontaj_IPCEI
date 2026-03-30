const Auth = {

    init() {
        this.loadAuthArea();
    },

    getCSRFToken() {
        return document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="))
            ?.split("=")[1];
    },

    logout() {
        fetch("/api/logout/", {
            method: "POST",
            headers: { "X-CSRFToken": this.getCSRFToken() }
        }).then(() => {
            window.location.href = "/api/login/";
        });
    },
    
    async getCurrentUser(labId = null) {
        let url = "/api/current-user/";
        if (labId) url += `?lab=${labId}`;

        const res = await fetch(url);
        return await res.json();
    },

    loadAuthArea(labId = null) {

    let url = "/api/current-user/";
    if (labId) url += `?lab=${labId}`;

    fetch(url)
        .then(res => res.json())
        .then(user => {

            if (typeof user?.can_see_jurnal !== "undefined") {
                window.canSeeJurnal = !!user.can_see_jurnal;
            }

            const usernameEl = document.getElementById("authUser");
            const roleEl = document.getElementById("authRole");
            const logoutBtn = document.getElementById("logoutBtn");

            if (!user.username) {
                usernameEl.textContent = "Not logged in";
                roleEl.textContent = "";
                logoutBtn.style.display = "none";
                return;
            }

            usernameEl.textContent = user.username;
            roleEl.textContent = `(${user.lab_role || user.global_role})`;

            logoutBtn.addEventListener("click", () => this.logout());

            if (typeof Export !== "undefined" && Export?.applyPermissions) {
                Export.applyPermissions(user);
            }

            const membersHoursBtn = document.getElementById("openMembersHoursPage");
            if (membersHoursBtn) {
                const canSeeMembersHours =
                    user.lab_role === "director" || user.global_role === "admin";
                membersHoursBtn.style.display = canSeeMembersHours ? "inline-block" : "none";
            }

            const annualStatsBtn = document.getElementById("openAnnualStatsPage");
            if (annualStatsBtn) {
                const canSeeAnnualStats =
                    user.lab_role === "director" || user.global_role === "admin";
                annualStatsBtn.style.display = canSeeAnnualStats ? "inline-block" : "none";
            }

        });
    }
    
};
