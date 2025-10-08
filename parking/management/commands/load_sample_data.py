from django.core.management.base import BaseCommand
from parking.models import ParkingArea, ParkingSlot, SlotStatus
from django.utils import timezone
import random

class Command(BaseCommand):
    help = "Load sample parking areas, slots, and statuses"

    def handle(self, *args, **kwargs):
        # Clear existing data
        ParkingSlot.objects.all().delete()
        ParkingArea.objects.all().delete()
        SlotStatus.objects.all().delete()

        self.stdout.write("Loading sample parking areas and slots...")

        # Sample areas
        areas = [
            {"name": "Central Garage", "total_capacity": 20, "area_type": "garage"},
            {"name": "Main Street Lot", "total_capacity": 15, "area_type": "lot"},
            {"name": "Downtown Street Parking", "total_capacity": 10, "area_type": "street"},
        ]

        for area_data in areas:
            area = ParkingArea.objects.create(
                name=area_data["name"],
                total_capacity=area_data["total_capacity"],
                area_type=area_data["area_type"]
            )

            # Generate slots for each area
            for i in range(1, area.total_capacity + 1):
                lat = -17.825 + random.uniform(-0.001, 0.001)  # example coordinates
                lng = 31.053 + random.uniform(-0.001, 0.001)
                slot = ParkingSlot.objects.create(
                    slot_id=f"{area.name[:3].upper()}-{i}",
                    area=area,
                    latitude=lat,
                    longitude=lng,
                    is_handicapped=random.choice([False, True]),
                    reserved_for=random.choice([None, "VIP", "Staff"])
                )

                # Random initial status
                SlotStatus.objects.create(
                    slot=slot,
                    is_occupied=random.choice([False, True]),
                    timestamp=timezone.now()
                )

        self.stdout.write(self.style.SUCCESS("Sample parking data loaded successfully!"))
