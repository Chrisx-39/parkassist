from django.core.management.base import BaseCommand
from parking.models import ParkingArea, ParkingSlot, SlotStatus, GarageLevel
from django.utils import timezone
import random

class Command(BaseCommand):
    help = "Load realistic sample parking areas, levels, slots, and statuses for Avondale Shops (Harare)."

    def handle(self, *args, **kwargs):
        # Clear existing data
        SlotStatus.objects.all().delete()
        ParkingSlot.objects.all().delete()
        GarageLevel.objects.all().delete()
        ParkingArea.objects.all().delete()

        self.stdout.write("🚗 Loading Avondale Shops parking data...")

        # --- Avondale Shops realistic parking zones ---
        areas = [
            {
                "name": "Avondale Mall Parking",
                "total_capacity": 80,
                "area_type": "lot",
                "center": (-17.7978, 31.0384),
                "levels": [],  # open-air
            },
            {
                "name": "Food Lovers Underground Parking",
                "total_capacity": 45,
                "area_type": "garage",
                "center": (-17.7982, 31.0389),
                "levels": ["B1"],  # single basement level
            },
            {
                "name": "King George Street Parking",
                "total_capacity": 30,
                "area_type": "street",
                "center": (-17.7971, 31.0375),
                "levels": [],  # roadside
            },
            {
                "name": "Avondale Flea Market Parking",
                "total_capacity": 50,
                "area_type": "lot",
                "center": (-17.7987, 31.0398),
                "levels": [],
            },
        ]

        for area_data in areas:
            area = ParkingArea.objects.create(
                name=area_data["name"],
                total_capacity=area_data["total_capacity"],
                area_type=area_data["area_type"],
                boundary=[
                    {"lat": area_data["center"][0] + random.uniform(-0.0004, 0.0004),
                     "lng": area_data["center"][1] + random.uniform(-0.0004, 0.0004)}
                    for _ in range(4)
                ]
            )

            # Create levels (for garages only)
            levels = []
            for level_name in area_data["levels"]:
                level = GarageLevel.objects.create(
                    area=area,
                    level_name=level_name,
                    level_capacity=area_data["total_capacity"] // max(1, len(area_data["levels"]))
                )
                levels.append(level)

            # Create parking slots
            for i in range(1, area.total_capacity + 1):
                lat = area_data["center"][0] + random.uniform(-0.0006, 0.0006)
                lng = area_data["center"][1] + random.uniform(-0.0006, 0.0006)
                level = random.choice(levels) if levels else None
                slot = ParkingSlot.objects.create(
                    slot_id=f"{area.name.split()[0][:3].upper()}-{i:03}",
                    area=area,
                    level=level,
                    latitude=lat,
                    longitude=lng,
                    is_handicapped=(i % 15 == 0),
                    reserved_for=random.choice([None, None, "VIP", "Staff"])
                )

                # Set realistic occupancy based on area type
                if area.area_type == "garage":
                    occupied_chance = 0.7
                elif area.area_type == "lot":
                    occupied_chance = 0.65
                else:  # street
                    occupied_chance = 0.5

                is_occupied = random.random() < occupied_chance

                SlotStatus.objects.create(
                    slot=slot,
                    is_occupied=is_occupied,
                    timestamp=timezone.now()
                )

        self.stdout.write(self.style.SUCCESS("✅ Avondale Shops parking data loaded successfully!"))
