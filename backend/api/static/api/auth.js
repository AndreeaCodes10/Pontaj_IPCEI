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

            Export.applyPermissions(user);

        });
    }
    
};