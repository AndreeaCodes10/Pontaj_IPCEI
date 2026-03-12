# Features
## Authentication
Login/logout system

Role-based access control

User roles:

* **Admin** – manages labs and exports reports

* **Director** – manages lab members and work entries

* **Member** – limited access

## Lab Management

Users can belong to multiple labs

Each lab has:
* members
* directors
### Directors and admins can:
* add users to labs
* remove users from labs
* view lab membership
* **export**

## **Work Entry System**
Users can log their daily progress with detailed metadata:
* **Entry Details**
    * **Lab** selection
    * Deliverable documentation
    * **Collaboration**
        * Individual/Collaborative flags to distinguish workflow types.

    * **Calendar Visualization**
        * The application leverages **Flatpickr** to provide a seamless user experience:
            * **Activity Heatmap:** Worked days are visually highlighted.
            * **Navigation:** Smooth monthly navigation to view past entries.
            * **Live Stats:** Dynamic calculation of hours based on selected dates.
    * Links and Comments
    
In a separate page the users can see their past entries by selecting the lab and the month.

### **Monthly Hours Tracking**
The system automates the math so you don't have to:
* **Daily Totals:** Precise calculation of hours worked per day.
* **Monthly Aggregates:** Automated summation of total monthly labor.

## **Export Functionality**
Designed for administrative oversight:
* **Excel Integration:** Directors and admins can export comprehensive monthly reports directly to `.xlsx` format.

# 🛠 Installation & Setup

Follow these steps to get your local development environment running.

### 1. Clone the repository
* `git clone https://github.com/AndreeaCodes10/Pontaj_IPCEI.git`
* `cd Pontaj_IPCEI`

### 2. Create a virtual environment
Linux / macOS:
* `python3 -m venv venv`
* `source venv/bin/activate`

Windows:
* `python -m venv venv`
* `venv\Scripts\activate`

### 3. Install dependencies
* `pip install -r requirements.txt`

### 4. Go in backend
* `cd backend`

### 5. Apply migrations
* `python manage.py migrate`

### 6. Create an admin user
* `python manage.py createsuperuser`

### 7. Run the server
* `python manage.py runserver 0.0.0.0:8000`

### 8. Create users and labs
* Open: [http://127.0.0.1:8000/admin/api/](http://127.0.0.1:8000/admin/api/)
* Log in with the <mark>admin username and password</mark>

### 9. Access the application
* Open: [http://127.0.0.1:8000/api/login/](http://127.0.0.1:8000/api/app/)