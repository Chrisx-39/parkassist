from django.core.management.base import BaseCommand
from parking.models import ParkingArea, ParkingSlot, SlotStatus, GarageLevel
from django.utils import timezone
import random

class Command(BaseCommand):
    help = "Load realistic sample parking areas, levels, slots, and statuses."

    def handle(self, *args, **kwargs):
        # Clear existing data
        SlotStatus.objects.all().delete()
        ParkingSlot.objects.all().delete()
        GarageLevel.objects.all().delete()
        ParkingArea.objects.all().delete()

        self.stdout.write("🚗 Loading realistic parking data...")

        # Define realistic areas
        areas = [
            {
                "name": "Central Garage",
                "total_capacity": 40,
                "area_type": "garage",
                "center": (-17.8290, 31.0520),
                "levels": ["B1", "L1", "L2"],
            },
            {
                "name": "Main Street Lot",
                "total_capacity": 25,
                "area_type": "lot",
                "center": (-17.8285, 31.0505),
                "levels": [],
            },
            {
                "name": "Downtown Street Parking",
                "total_capacity": 15,
                "area_type": "street",
                "center": (-17.8270, 31.0540),
                "levels": [],
            },
        ]

        for area_data in areas:
            area = ParkingArea.objects.create(
                name=area_data["name"],
                total_capacity=area_data["total_capacity"],
                area_type=area_data["area_type"],
                boundary=[
                    {"lat": area_data["center"][0] + random.uniform(-0.0005, 0.0005),
                     "lng": area_data["center"][1] + random.uniform(-0.0005, 0.0005)}
                    for _ in range(4)
                ]
            )

            # Create levels for garages
            levels = []
            for level_name in area_data["levels"]:
                level = GarageLevel.objects.create(
                    area=area,
                    level_name=level_name,
                    level_capacity=area_data["total_capacity"] // len(area_data["levels"])
                )
                levels.append(level)

            # Create slots
            for i in range(1, area.total_capacity + 1):
                lat = area_data["center"][0] + random.uniform(-0.0008, 0.0008)
                lng = area_data["center"][1] + random.uniform(-0.0008, 0.0008)
                level = random.choice(levels) if levels else None
                slot = ParkingSlot.objects.create(
                    slot_id=f"{area.name[:3].upper()}-{i:03}",
                    area=area,
                    level=level,
                    latitude=lat,
                    longitude=lng,
                    is_handicapped=(i % 12 == 0),
                    reserved_for=random.choice([None, None, "VIP", "Staff"])
                )

                # Occupancy probability varies by area type
                if area.area_type == "garage":
                    occupied_chance = 0.75
                elif area.area_type == "lot":
                    occupied_chance = 0.6
                else:
                    occupied_chance = 0.4

                is_occupied = random.random() < occupied_chance

                SlotStatus.objects.create(
                    slot=slot,
                    is_occupied=is_occupied,
                    timestamp=timezone.now()
                )

        self.stdout.write(self.style.SUCCESS("✅ Realistic parking data loaded successfully!"))
