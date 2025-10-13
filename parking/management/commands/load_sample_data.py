from django.core.management.base import BaseCommand
from parking.models import ParkingArea, ParkingSlot, SlotStatus
from django.utils import timezone
import random

def dms_to_decimal(deg, minutes, seconds, direction):
    """Convert GPS DMS to decimal degrees."""
    decimal = deg + minutes / 60 + seconds / 3600
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

class Command(BaseCommand):
    help = "Load real Avondale Shopping Centre parking data with true GPS coordinates."

    def handle(self, *args, **kwargs):
        self.stdout.write("🅿️ Loading real Avondale Parking spots (A–F)...")

        # Clear old data
        SlotStatus.objects.all().delete()
        ParkingSlot.objects.all().delete()
        ParkingArea.objects.all().delete()

        # Real parking spot coordinates (converted from your data)
        parking_spots = {
            "A": [
                (-17.80255278, 31.03843056),
                (-17.80257778, 31.03833056),
                (-17.80291111, 31.03841667),
                (-17.80288611, 31.03848611),
            ],
            "B": [
                (-17.80262222, 31.03816389),
                (-17.80292778, 31.03825833),
                (-17.80290278, 31.03835278),
                (-17.80259722, 31.038278),
            ],
            "C": [
                (-17.80263889, 31.03754722),
                (-17.80267222, 31.03744167),
                (-17.80299167, 31.03751667),
                (-17.80296389, 31.03763333),
            ],
            "D": [
                (-17.802675, 31.037389),
                (-17.8027, 31.037286),
                (-17.80305, 31.037375),
                (-17.803022, 31.037472),
            ],
            "E": [
                (-17.802717, 31.037222),
                (-17.802728, 31.037131),
                (-17.803078, 31.037219),
                (-17.803056, 31.037311),
            ],
            "F": [
                (-17.802914, 31.037017),
                (-17.802899, 31.037086),
                (-17.803089, 31.037136),
                (-17.8031, 31.037056),
            ],
        }

        for label, boundary in parking_spots.items():
            area = ParkingArea.objects.create(
                name=f"Avondale Spot {label}",
                total_capacity=10,
                area_type="lot",
                boundary=[{"lat": lat, "lng": lng} for lat, lng in boundary]
            )

            # Create 10 slots per area (simulate small cluster per section)
            for i in range(1, 11):
                center_lat = sum(p[0] for p in boundary) / len(boundary)
                center_lng = sum(p[1] for p in boundary) / len(boundary)

                slot = ParkingSlot.objects.create(
                    slot_id=f"AVM-{label}-{i:02}",
                    area=area,
                    latitude=center_lat + random.uniform(-0.00002, 0.00002),
                    longitude=center_lng + random.uniform(-0.00002, 0.00002),
                    is_handicapped=(i % 10 == 0),
                    reserved_for=random.choice([None, "VIP", "Staff", None])
                )

                # Random initial occupancy
                occupied = random.random() < 0.6
                SlotStatus.objects.create(
                    slot=slot,
                    is_occupied=occupied,
                    timestamp=timezone.now()
                )

            self.stdout.write(f"✅ Created area {label} with 10 slots")

        self.stdout.write(self.style.SUCCESS("🎯 Avondale Shopping Centre parking data loaded successfully!"))
