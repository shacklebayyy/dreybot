import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drey_docs.settings.development')

app = Celery('drey_docs')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
