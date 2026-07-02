from django.core.management.base import BaseCommand
from alerts.lasair_query import fetch_lasair_alerts


class Command(BaseCommand):

    help = "Fetch lasair alerts and save it to jsonfile."

    def handle(self, *args, **kwargs):

        self.stdout.write("Starting Lasair Update")

        try:
            fetch_lasair_alerts()

            self.stdout.write(self.style.SUCCESS("Alerts updated succesfully"))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"failed to update alerts: {e}")
            )