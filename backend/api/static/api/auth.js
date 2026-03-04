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

    loadAuthArea(labId = null) {
        let url = "/api/current-user/";
        if (labId) url += `?lab_id=${labId}`;

        fetch(url)
            .then(res => res.json())
            .then(user => {
                const authArea = document.getElementById("authArea");

                if (!user.username) {
                    authArea.textContent = "Not logged in";
                    return;
                }

                authArea.innerHTML = `
                    <span class="auth-user">${user.username}</span>
                    <span class="auth-role">(${user.lab_role || user.global_role})</span>
                    <button class="logout-btn" id="logoutBtn">Logout</button>
                `;

                document
                    .getElementById("logoutBtn")
                    .addEventListener("click", () => this.logout());

                Export.applyPermissions(user);

            });
    }
    
};