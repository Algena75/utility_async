from celery import Celery
import asyncio

app = Celery("backend")

app.config_from_object("dbase.core.config", namespace="CELERY")
app.conf.broker_connection_retry_on_startup = True

app.autodiscover_tasks()

from dbase.services.utils import calculate_bill


@app.task
def calculate_bills(job_params: dict):
    """
    Задача вызывает функцию расчёта квартплаты для квартир заданного дома
    в заданный период времени.
    """
    asyncio.run(calculate_bill(job_params.get('id'),
                               job_params.get('month'),
                               job_params.get('year')))
