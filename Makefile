.SILENT:

start:
	python manage.py runserver 0.0.0.0:8000

sync_db:
	python manage.py syncdb

