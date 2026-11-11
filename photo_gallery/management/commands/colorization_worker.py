import time
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from photo_gallery.services.jobs import run_one


class Command(BaseCommand):
    help = 'Process persisted DDColor jobs (one inference at a time).'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true')

    def handle(self, *args, **options):
        waiting = False
        try:
            while True:
                close_old_connections()
                try:
                    with requests.get(
                        settings.DDCOLOR_URL.rstrip('/') + '/health/ready',
                        timeout=(settings.DDCOLOR_CONNECT_TIMEOUT, 5),
                    ) as response:
                        ready = response.status_code == 200
                except requests.RequestException:
                    ready = False
                if not ready:
                    if not waiting:
                        self.stdout.write('Waiting for DDColor readiness; queued jobs are preserved.')
                    waiting = True
                    if options['once']:
                        return
                    time.sleep(5)
                    continue
                if waiting:
                    self.stdout.write('DDColor ready; resuming queued jobs.')
                    waiting = False
                processed = run_one()
                if options['once']:
                    return
                if not processed:
                    time.sleep(2)
        except KeyboardInterrupt:
            return
