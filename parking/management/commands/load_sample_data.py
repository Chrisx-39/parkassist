from django.core.management.base import BaseCommand
from parking.models import ParkingArea, ParkingSlot, SlotStatus, GarageLevel
from django.utils import timezone
import random

class Command(BaseCommand):
    help = "Load realistic parking data for Avondale Mall Parking (Harare) with exact coordinates."

    def handle(self, *args, **kwargs):
        # Clear existing data
        SlotStatus.objects.all().delete()
        ParkingSlot.objects.all().delete()
        GarageLevel.objects.all().delete()
        ParkingArea.objects.all().delete()

        self.stdout.write("🚗 Loading Avondale Mall Parking data...")

        # Exact center coordinates for Avondale Mall
        avondale_center = (-17.80316172143422, 31.03789527991053)

        # Create the Avondale Mall Parking area
        area = ParkingArea.objects.create(
            name="Avondale Mall Parking",
            total_capacity=80,
            area_type="lot",  # open-air
            boundary=[
                {"lat": avondale_center[0] + random.uniform(-0.0002, 0.0002),
                 "lng": avondale_center[1] + random.uniform(-0.0002, 0.0002)}
                for _ in range(4)
            ]
        )

        self.stdout.write(f"Created ParkingArea: {area.name}")

        # Create parking slots
        for i in range(1, area.total_capacity + 1):
            lat = avondale_center[0] + random.uniform(-0.0003, 0.0003)
            lng = avondale_center[1] + random.uniform(-0.0003, 0.0003)

            slot = ParkingSlot.objects.create(
                slot_id=f"AVM-{i:03}",
                area=area,
                level=None,  # open-air lot
                latitude=lat,
                longitude=lng,
                is_handicapped=(i % 15 == 0),
                reserved_for=random.choice([None, None, "VIP", "Staff"])
            )

            # Random occupancy
            occupied_chance = 0.65  # open-air lot
            is_occupied = random.random() < occupied_chance

            SlotStatus.objects.create(
                slot=slot,
                is_occupied=is_occupied,
                timestamp=timezone.now()
            )

        self.stdout.write(self.style.SUCCESS("✅ Avondale Mall Parking data loaded successfully!"))
