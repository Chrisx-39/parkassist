import random
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from parking.models import ParkingSlot, SlotStatus, Sensor

class Command(BaseCommand):
    help = "Simulate realistic IoT updates for parking slots."

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=3, help='Seconds between updates.')
        parser.add_argument('--count', type=int, default=100, help='Number of updates to simulate.')

    def handle(self, *args, **kwargs):
        interval = kwargs['interval']
        count = kwargs['count']
        slots = list(ParkingSlot.objects.all())

        if not slots:
            self.stdout.write(self.style.WARNING("⚠️ No slots found. Run 'load_sample_data' first."))
            return

        self.stdout.write(self.style.SUCCESS(f"🚦 Simulating {count} IoT updates..."))

        for i in range(count):
            slot = random.choice(slots)
            sensor, _ = Sensor.objects.get_or_create(sensor_id=f"SENS-{slot.slot_id}", slot=slot)

            last_status = slot.latest_status
            # 80% chance to keep same state, 20% to toggle
            toggle = random.random() < 0.2
            new_status = not last_status.is_occupied if (last_status and toggle) else (last_status.is_occupied if last_status else False)

            # Add a 5% sensor error chance
            if random.random() < 0.05:
                new_status = not new_status

            SlotStatus.objects.create(
                slot=slot,
                is_occupied=new_status,
                sensor=sensor,
                timestamp=timezone.now()
            )

            text = "Occupied" if new_status else "Empty"
            self.stdout.write(f"[{i+1}/{count}] {slot.slot_id} ({slot.area.name}) -> {text}")

            time.sleep(interval)

        self.stdout.write(self.style.SUCCESS("✅ IoT simulation complete!"))
