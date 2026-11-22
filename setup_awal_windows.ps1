py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py makemigrations store
python manage.py migrate
python manage.py seed_kuliner
Write-Host 'Setup selesai. Jalankan: python manage.py createsuperuser lalu python manage.py runserver'
