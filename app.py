from flask import Flask, render_template, request, redirect, url_for, flash, session
import json
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'  

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Проверка допустимых расширений файлов
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Форма подачи заявки на сервер
@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        nickname = request.form['nickname']
        age = request.form['age']
        reason = request.form['reason']

        application_data = {
            'nickname': nickname,
            'age': age,
            'reason': reason
        }

        if not os.path.exists('applications'):
            os.makedirs('applications')

        application_id = len(os.listdir('applications')) + 1
        with open(f'applications/{application_id}.json', 'w') as f:
            json.dump(application_data, f, ensure_ascii=False, indent=4)

        flash('Ваша заявка успешно отправлена.')
        return redirect(url_for('index'))

    return render_template('apply.html')

# Страница с правилами сервера
@app.route('/rules')
def rules():
    return render_template('rules.html')

# Форма подачи жалобы
@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        nickname = request.form['nickname']
        description = request.form['description']
        coordinates = request.form.get('coordinates')
        offender = request.form.get('offender')

        # Обработка прикрепленных файлов
        files = request.files.getlist('screenshots')
        file_urls = []
        for file in files:
            if file and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{original_filename}"
                if not os.path.exists('static/uploads'):
                    os.makedirs('static/uploads')
                filepath = os.path.join('static/uploads', unique_filename)
                file.save(filepath)
                file_urls.append(f'uploads/{unique_filename}')

        # Сохранение жалобы
        complaint_data = {
            'nickname': nickname,
            'description': description,
            'coordinates': coordinates,
            'offender': offender,
            'screenshots': file_urls,
            'status': 'Новая',
            'assigned_to': None
        }

        if not os.path.exists('complaints'):
            os.makedirs('complaints')

        complaint_id = len(os.listdir('complaints')) + 1
        with open(f'complaints/{complaint_id}.json', 'w') as f:
            json.dump(complaint_data, f, ensure_ascii=False, indent=4)

        flash('Ваша жалоба успешно отправлена.')
        return redirect(url_for('index'))

    return render_template('complaint_form.html')

# Вход администратора
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        nickname = request.form['nickname']
        token = request.form['token']

        try:
            with open('admin_tokens.json', 'r') as f:
                tokens = json.load(f)
        except FileNotFoundError:
            tokens = {}

        if tokens.get(nickname) == token:
            session['admin_nickname'] = nickname
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверный никнейм или токен.')
            return redirect(url_for('admin_login'))

    return render_template('login.html')

# Выход администратора
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_nickname', None)
    return redirect(url_for('index'))

# Панель администратора
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_nickname' not in session:
        return redirect(url_for('admin_login'))

    # Загрузка заявок и жалоб
    applications = []
    if os.path.exists('applications'):
        for filename in os.listdir('applications'):
            if filename.endswith('.json'):
                with open(os.path.join('applications', filename), 'r') as f:
                    application = json.load(f)
                    application['id'] = filename.split('.')[0]
                    applications.append(application)

    complaints = []
    if os.path.exists('complaints'):
        for filename in os.listdir('complaints'):
            if filename.endswith('.json'):
                with open(os.path.join('complaints', filename), 'r') as f:
                    complaint = json.load(f)
                    complaint['id'] = filename.split('.')[0]
                    complaints.append(complaint)

    return render_template('admin_dashboard.html', applications=applications, complaints=complaints)

# Просмотр жалобы
@app.route('/admin/complaint/<complaint_id>', methods=['GET', 'POST'])
def view_complaint(complaint_id):
    if 'admin_nickname' not in session:
        return redirect(url_for('admin_login'))

    complaint_file = f'complaints/{complaint_id}.json'
    if not os.path.exists(complaint_file):
        flash('Жалоба не найдена.')
        return redirect(url_for('admin_dashboard'))

    with open(complaint_file, 'r') as f:
        complaint = json.load(f)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'take':
            complaint['status'] = 'В работе'
            complaint['assigned_to'] = session['admin_nickname']
            with open(complaint_file, 'w') as f:
                json.dump(complaint, f, ensure_ascii=False, indent=4)
            flash('Вы взяли жалобу в работу.')
        elif action == 'close':
            complaint['status'] = 'Закрыта'
            with open(complaint_file, 'w') as f:
                json.dump(complaint, f, ensure_ascii=False, indent=4)
            flash('Жалоба закрыта.')

        return redirect(url_for('admin_dashboard'))

    return render_template('view_complaint.html', complaint=complaint, complaint_id=complaint_id)

# Просмотр заявки
@app.route('/admin/application/<application_id>', methods=['GET', 'POST'])
def view_application(application_id):
    if 'admin_nickname' not in session:
        return redirect(url_for('admin_login'))

    application_file = f'applications/{application_id}.json'
    if not os.path.exists(application_file):
        flash('Заявка не найдена.')
        return redirect(url_for('admin_dashboard'))

    with open(application_file, 'r') as f:
        application = json.load(f)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'accept':
            flash('Заявка принята.')
        elif action == 'reject':
            flash('Заявка отклонена.')

        os.remove(application_file)
        return redirect(url_for('admin_dashboard'))

    return render_template('view_application.html', application=application, application_id=application_id)

# Обработчик ошибки 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
