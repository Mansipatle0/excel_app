Django Excel Upload Project (White + Blue theme)
------------------------------------------------

Run steps:
1. Create & activate virtualenv
   python -m venv venv
   # Windows: venv\Scripts\activate
   # mac/linux: source venv/bin/activate

2. Install deps
   pip install -r requirements.txt

3. Make migrations and migrate
   python manage.py makemigrations
   python manage.py migrate

4. Run server
   python manage.py runserver

Open http://127.0.0.1:8000 (Table page - homepage)
