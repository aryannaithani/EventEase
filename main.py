from flask import Flask, render_template, url_for, request, redirect, session
from flask.views import MethodView
from db import get_connection


app = Flask(__name__)
app.secret_key = "super secret key"


class HomePage(MethodView):

    def get(self):
        return render_template('index.html')


class LoginPage(MethodView):

    def get(self):
        return render_template('login.html')

    def post(self):
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        connection = get_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users WHERE username=%s AND password=%s AND role=%s"
            cursor.execute(sql, (username, password, role))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['username'] = user['username']
                return redirect(url_for(f'{role}_dashboard'))
            else:
                return redirect(url_for("login_page"))


class StudentDashboard(MethodView):

    def get(self):
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE status='Approved' ORDER BY date ASC, time ASC LIMIT 3")
            upcoming_events = cursor.fetchall()
        return render_template('student-dashboard.html', user=session['username'], events=upcoming_events)


class ProposeEvent(MethodView):

    def get(self):
        return render_template('propose-event.html', user=session['username'])

    def post(self):
        title = request.form.get('title')
        description = request.form.get('description')
        date = request.form.get('date')
        time = request.form.get('time')
        duration = request.form.get('duration')
        expected_participants = request.form.get('expected_participants')
        venue_preference = request.form.get('venue_preference')
        proposer = session['user_id']

        connection = get_connection()
        with connection.cursor() as cursor:
            sql = """INSERT INTO events 
                    (title, description, date, time, expected_participants, venue_preference, proposed_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
            cursor.execute(sql, (
                title,
                description,
                date,
                time,
                expected_participants,
                venue_preference,
                proposer
            ))
            connection.commit()

        return redirect(url_for('student_dashboard'))


class ViewEvents(MethodView):

    def get(self):
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM events WHERE status='Approved';")
            events = cursor.fetchall()

        with connection.cursor() as cursor:
            cursor.execute(f"SELECT event_id FROM registrations WHERE student_id = {int(session['user_id'])};")
            results = cursor.fetchall()
            registered = {result['event_id'] for result in results}

        return render_template('view-events.html', user=session['username'], events=events, registered=registered)


@app.route("/register", methods=['POST'])
def register():
    event_id = request.form.get('event_id')
    connection = get_connection()
    with connection.cursor() as cursor:
        sql = '''INSERT INTO registrations (student_id, event_id)
        VALUES (%s, %s)'''
        cursor.execute(sql, (session['user_id'], event_id))
        connection.commit()
    return redirect(url_for("view_events"))


class FacultyDashboard(MethodView):

    def get(self):
        return render_template('faculty-dashboard.html', user=session['username'])


class ReviewProposals(MethodView):

    def get(self):
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                        SELECT events.*, users.username 
                        FROM events 
                        JOIN users ON events.proposed_by = users.id
                        WHERE status='Pending'
                        ORDER BY events.date ASC, events.time ASC
                    """)
            events = cursor.fetchall()

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM events WHERE status='Pending'")
            result = cursor.fetchone()
            count = result['count']
        return render_template('review-proposals.html', events=events, user=session['username'], count=count)


@app.route("/approve-event", methods=["POST"])
def approve_event():
    event_id = request.form.get('event_id')
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute(f"update events set status = 'Approved' where id = {event_id}")
        connection.commit()
    return redirect(url_for('review_proposals'))

@app.route("/reject-event", methods=["POST"])
def reject_event():
    event_id = request.form.get('event_id')
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute(f"update events set status = 'Rejected' where id = {event_id}")
        connection.commit()
    return redirect(url_for('review_proposals'))


class AdminDashboard(MethodView):

    def get(self):
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS active FROM events WHERE status='Approved'")
            result = cursor.fetchone()
            active = result['active']

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS user_count FROM users")
            result = cursor.fetchone()
            user_count = result['user_count']

        return render_template('admin-dashboard.html', user=session['username'], active=active, user_count=user_count)


class ManageVenues(MethodView):

    def get(self):
        return render_template('manage-venues.html', user=session['username'])


class CreateAccount(MethodView):

    def get(self):
        print(" get called")
        return render_template('create-account.html')

    def post(self):
        print(" post called")
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        connection = get_connection()
        with connection.cursor() as cursor:
            sql = '''insert into users(username, password, role) values(%s, %s, %s);'''
            cursor.execute(sql, (username, password, role))
            connection.commit()
        return redirect(url_for('admin_dashboard'))


app.add_url_rule('/', view_func=HomePage.as_view('home_page'))
app.add_url_rule('/login', view_func=LoginPage.as_view('login_page'))
app.add_url_rule('/student-dashboard', view_func=StudentDashboard.as_view('student_dashboard'))
app.add_url_rule('/propose-event', view_func=ProposeEvent.as_view('propose_event'))
app.add_url_rule('/view-events', view_func=ViewEvents.as_view('view_events'))
app.add_url_rule('/faculty-dashboard', view_func=FacultyDashboard.as_view('faculty_dashboard'))
app.add_url_rule('/review-proposals', view_func=ReviewProposals.as_view('review_proposals'))
app.add_url_rule('/admin-dashboard', view_func=AdminDashboard.as_view('admin_dashboard'))
app.add_url_rule('/manage-venues', view_func=ManageVenues.as_view('manage_venues'))
app.add_url_rule('/create-account', view_func=CreateAccount.as_view('create_account'))

app.run(debug=True)