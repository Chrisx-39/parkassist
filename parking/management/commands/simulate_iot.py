import random
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from parking.models import ParkingSlot, SlotStatus, Sensor

class Command(BaseCommand):
    help = "Simulate IoT sensor updates for parking slots"

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval', type=int, default=5,
            help='Time in seconds between each simulation update'
        )
        parser.add_argument(
            '--count', type=int, default=50,
            help='Number of random updates to simulate'
        )

    def handle(self, *args, **kwargs):
        interval = kwargs['interval']
        count = kwargs['count']

        slots = list(ParkingSlot.objects.all())
        if not slots:
            self.stdout.write(self.style.WARNING("No parking slots found. Please load sample data first."))
            return

        self.stdout.write(self.style.SUCCESS(f"Starting IoT simulation for {count} updates..."))

        for i in range(count):
            slot = random.choice(slots)
            new_status = random.choice([True, False])

            # Optional: associate a sensor
            sensor, _ = Sensor.objects.get_or_create(sensor_id=f"SIM-{slot.slot_id}", slot=slot)

            SlotStatus.objects.create(
                slot=slot,
                is_occupied=new_status,
                sensor=sensor,
                timestamp=timezone.now()
            )

            status_text = "Occupied" if new_status else "Empty"
            self.stdout.write(f"[{i+1}/{count}] Slot {slot.slot_id} -> {status_text}")

            time.sleep(interval)

        self.stdout.write(self.style.SUCCESS("IoT simulation completed!"))
