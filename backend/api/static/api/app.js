const App = {
    init() {
        Labs.init();
        Calendar.init();
        Form.init();
        Auth.init();
        Export.init();
    }
};

document.addEventListener("DOMContentLoaded", () => {
    App.init();
});

// document.addEventListener("DOMContentLoaded", () => {

//     /* ============================================================
//        ELEMENT REFERENCES
//     ============================================================ */

//     const labSelect = document.getElementById("lab");
//     const subSelect = document.getElementById("subactivitate");
//     const livrabilSelect = document.getElementById("livrabil");
//     const individualSelect = document.getElementById("individual");
//     const form = document.getElementById("workEntryForm");
//     const exportBtn = document.getElementById("exportBtn");
//     const logoutBtn = document.getElementById("logoutBtn");

//     let datePickerInstance = null;


//     /* ============================================================
//        INITIALIZATION
//     ============================================================ */

//     loadLabs();
//     initializeTimePickers();


//     /* ============================================================
//        LABS
//     ============================================================ */

//     async function loadLabs() {
//         const response = await fetch("/api/labs/");
//         const labs = await response.json();

//         labSelect.innerHTML = "<option value=''>Select Labs</option>";

//         labs.forEach(lab => {
//             const opt = document.createElement("option");
//             opt.value = lab.id;
//             opt.textContent = lab.name;
//             labSelect.appendChild(opt);
//         });
//     }

//     /* ============================================================
//        SUBACTIVITATI (Filtered by Lab)
//     ============================================================ */

//     labSelect.addEventListener("change", async function () {
//         const labId = this.value;

//         if (!labId) return;

//         await loadSubactivitati(labId);
//         loadCalendarForLab(labId);
//     });


//     async function loadSubactivitati(labId) {
//         const response = await fetch(`/api/subactivitati/${labId}/`);
//         const data = await response.json();

//         subSelect.innerHTML = "";

//         data.forEach(sub => {
//             const option = document.createElement("option");
//             option.value = sub.id;
//             option.textContent = sub.nume;

//             // Store extra data
//             option.dataset.livrabil = sub.display_livrabil;
//             option.dataset.individual = sub.individual;

//             subSelect.appendChild(option);
//         });
//     }


//     /* ============================================================
//        CALENDAR (Lab-specific colored days)
//        - Display format: d-m-Y
//        - Backend format: Y-m-d
//        - FIXED timezone bug
//     ============================================================ */
//     // trebuie revenit aici
//     async function loadCalendarForLab(labId) {

//         const response = await fetch(`/api/pontaj-dates/?lab_id=${labId}`);
//         const workedDates = await response.json();  // Y-m-d format from backend

//         // Destroy old instance if exists
//         if (datePickerInstance) {
//             datePickerInstance.destroy();
//         }

//         datePickerInstance = flatpickr("#date", {
//             dateFormat: "d-m-Y",   // what user sees
//             altInput: false,

//             onChange: function(selectedDates, dateStr, instance) {
//             if (!selectedDates.length) return;
//             const month = selectedDates[0].getMonth() + 1;
//             const year = selectedDates[0].getFullYear();
//             loadMonthlyHours(month, year);
//             },
//             onMonthChange: function(monthObj) {
//                 const month = monthObj.currentMonth + 1;
//                 const year = monthObj.currentYear;
//                 loadMonthlyHours(month, year);
//             },

//             onDayCreate: function (dObj, dStr, fp, dayElem) {

//                 // 🚨 DO NOT use toISOString() (timezone bug)
//                 const year = dayElem.dateObj.getFullYear();
//                 const month = String(dayElem.dateObj.getMonth() + 1).padStart(2, "0");
//                 const day = String(dayElem.dateObj.getDate()).padStart(2, "0");

//                 const localDate = `${year}-${month}-${day}`;

//                 if (workedDates.includes(localDate)) {
//                     dayElem.style.background = "#8e6bff";
//                     dayElem.style.color = "white";
//                     dayElem.style.borderRadius = "50%";
//                 }
//             }
//         });
//     }


//     /* ============================================================
//        TIME PICKERS (Hour Only, AM/PM, No Minutes)
//     ============================================================ */

//     function initializeTimePickers() {

//         flatpickr("#start_time", {
//             enableTime: true,
//             noCalendar: true,
//             dateFormat: "H:00",
//             time_24hr: false,
//             minuteIncrement: 60,
//             enableSeconds: false
//         });

//         flatpickr("#end_time", {
//             enableTime: true,
//             noCalendar: true,
//             dateFormat: "H:00",
//             time_24hr: false,
//             minuteIncrement: 60,
//             enableSeconds: false
//         });
//     }


//     /* ============================================================
//        AUTO UPDATE LIVRABIL + INDIVIDUAL
//     ============================================================ */

//     subSelect.addEventListener("change", (e) => {
//         const selected = e.target.selectedOptions[0];
//         if (!selected) return;

//         livrabilSelect.value = selected.dataset.livrabil || "";
//         individualSelect.value =
//             selected.dataset.individual === "true" ? "true" : "false";
//     });


//     /* ============================================================
//        FORM SUBMISSION
//        - Converts d-m-Y → Y-m-d for backend
//     ============================================================ */

//     form.addEventListener("submit", async function (e) {
//         e.preventDefault();

//         const formattedDate = convertToBackendDate(
//             document.getElementById("date").value
//         );

//         const startTime = document.getElementById("start_time").value;
//         const nrOre = parseInt(document.getElementById("nr_ore").value, 10);

//         function addHoursToTime(timeStr, hoursToAdd) {
//             const [h, m] = timeStr.split(":").map(Number);
//             const date = new Date();
//             date.setHours(h, m, 0, 0);
//             date.setHours(date.getHours() + hoursToAdd);

//             const hh = String(date.getHours()).padStart(2, "0");
//             const mm = String(date.getMinutes()).padStart(2, "0");
//             return `${hh}:${mm}`;
//         }

//         const endTime = addHoursToTime(startTime, nrOre);
//         const durata = `${startTime}-${endTime}`;


//         const data = {
//             lab: labSelect.value,
//             subactivitate: subSelect.value,
//             livrabil: livrabilSelect.value,
//             individual: individualSelect.value,
//             date: formattedDate,  // Y-m-d format
//             durata: durata,
//             nr_ore: nrOre,
//             activity_description: document.getElementById("activity_description").value,
//             comentarii: document.getElementById("comentarii").value,
//             links: document.getElementById("links").value,
//         };

//         const response = await fetch("/api/work-entry/", {
//             method: "POST",
//             credentials: "same-origin",
//             headers: {
//                 "Content-Type": "application/json",
//                 "X-CSRFToken": getCSRFToken()
//             },
//             body: JSON.stringify(data)
//         });

//         if (response.ok) {
//             alert("Saved successfully!");
//             form.reset();

//             // reload calendar coloring
//             if (labSelect.value) {
//                 loadCalendarForLab(labSelect.value);
//             }

//         } else {
//             const error = await response.json();
//             console.error(error);
//             alert("Error saving entry.");
//         }
//     });


//     function convertToBackendDate(dmy) {
//         // Converts d-m-Y → Y-m-d
//         const [day, month, year] = dmy.split("-");
//         return `${year}-${month}-${day}`;
//     }


//     /* ============================================================
//        EXPORT EXCEL old endpoint (REPLACED BY MONTHLY SHEET EXPORT)
//     ============================================================ */
//     // if (exportBtn) {
//     //     exportBtn.addEventListener("click", () => {
//     //         window.location.href = "/api/send-to-excel/";
//     //     });
//     // }


//     function loadMonthlyHours(month = null, year = null) {
//     // month/year default to current if not provided
//         const now = new Date();
//         month = month || now.getMonth() + 1;
//         year = year || now.getFullYear();

//         fetch(`/api/monthly-hours/?month=${month}&year=${year}`)
//             .then(res => res.json())
//             .then(data => {
//                 document.getElementById("usedHours").innerText = data.used_hours;
//                 document.getElementById("limitHours").innerText = data.limit;
//                 document.getElementById("remainingHours").innerText = data.remaining;

//                 const percent = (data.used_hours / data.limit) * 100;
//                 document.getElementById("progressBar").style.width = percent + "%";
//             });
//     }

//     loadMonthlyHours();

//     /* ============================================================
//         CURRENT USER INFO
//     ============================================================ */
//     // get CSRF token from cookie
//     function getCSRFToken() {
//         return document.cookie
//             .split("; ")
//             .find(row => row.startsWith("csrftoken="))
//             ?.split("=")[1];
//     }

//     // call logout API
//     function logout() {
//         fetch("/api/logout/", {
//             method: "POST",
//             headers: {
//                 "X-CSRFToken": getCSRFToken()
//             }
//         }).then(() => {
//             window.location.href = "/api/login/";
//         });
//     }

//     // load current user and render header
//     // function loadAuthArea() {
//     //     fetch("/api/current-user/")
//     //         .then(res => res.json())
//     //         .then(user => {
//     //             const authArea = document.getElementById("authArea");

//     //             if (!user.username) {
//     //                 authArea.textContent = "Not logged in";
//     //                 return;
//     //             }

//     //             authArea.innerHTML = `
//     //                 <span class="auth-user">${user.username}</span>
//     //                 <span class="auth-role">(${user.role})</span>
//     //                 <button class="logout-btn" id="logoutBtn">Logout</button>
//     //             `;

//     //             document
//     //                 .getElementById("logoutBtn")
//     //                 .addEventListener("click", logout);
//     //     });
//     // }
//     /* ============================================================
//     CURRENT USER INFO + EXPORT PERMISSIONS
//     ============================================================ */

//     function getCSRFToken() {
//         return document.cookie
//             .split("; ")
//             .find(row => row.startsWith("csrftoken="))
//             ?.split("=")[1];
//     }

//     function logout() {
//         fetch("/api/logout/", {
//             method: "POST",
//             headers: { "X-CSRFToken": getCSRFToken() }
//         }).then(() => {
//             window.location.href = "/api/login/";
//         });
//     }

//     function loadAuthArea() {
//         fetch("/api/current-user/")
//             .then(res => res.json())
//             .then(user => {

//                 const authArea = document.getElementById("authArea");
//                 const exportBtn = document.getElementById("exportBtn");
//                 const exportMonth = document.getElementById("exportMonth");

//                 if (!user.username) {
//                     authArea.textContent = "Not logged in";
//                     return;
//                 }

//                 // ===== render header user =====
//                 authArea.innerHTML = `
//                     <span class="auth-user">${user.username}</span>
//                     <span class="auth-role">(${user.role})</span>
//                     <button class="logout-btn" id="logoutBtn">Logout</button>
//                 `;

//                 document
//                     .getElementById("logoutBtn")
//                     .addEventListener("click", logout);

//                 // ===== role permissions =====
//                 const canExport = user.role === "director" || user.role === "admin";

//                 if (exportBtn && exportMonth) {
//                     if (canExport) {
//                         exportBtn.style.display = "inline-block";
//                         exportMonth.style.display = "inline-block";

//                         exportBtn.addEventListener("click", () => {
//                             const monthInput = exportMonth.value;

//                             if (!monthInput) {
//                                 alert("Selectează luna pentru export.");
//                                 return;
//                             }

//                             const [year, month] = monthInput.split("-");
//                             window.location.href =
//                                 `/api/export-monthly-sheet/?month=${month}&year=${year}`;
//                         });

//                     } else {
//                         exportBtn.style.display = "none";
//                         exportMonth.style.display = "none";
//                     }
//                 }
//             });
//         }

//     loadAuthArea();

// });