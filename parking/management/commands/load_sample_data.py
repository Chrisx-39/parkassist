from django.core.management.base import BaseCommand
from parking.models import ParkingArea, ParkingSlot, SlotStatus
from django.utils import timezone
import random
import math


class Command(BaseCommand):
    help = "Load Avondale Mall parking data (A–F) in circular slot layout with variable slot counts."

    def handle(self, *args, **kwargs):
        self.stdout.write("🅿️ Loading Avondale parking spots A–F (circular layout)...")

        # Clear existing data
        SlotStatus.objects.all().delete()
        ParkingSlot.objects.all().delete()
        ParkingArea.objects.all().delete()

        # --- Polygon boundaries (for reference and centroid calculation) ---
        parking_areas = {
            "A": [
                (-17.802552777777777, 31.038430555555557),
                (-17.802577777777778, 31.038330555555557),
                (-17.80291111111111,  31.03841666666667),
                (-17.80288611111111,  31.038486111111112),
            ],
            "B": [
                (-17.802622222222222, 31.038163888888892),
                (-17.80292777777778,  31.038258333333335),
                (-17.802902777777778, 31.038352777777778),
                (-17.80259722222222,  31.03827777777778),
            ],
            "C": [
                (-17.80263888888889,  31.03810277777778),
                (-17.802672222222224, 31.037997222222224),
                (-17.803002777777778, 31.038072222222223),
                (-17.802975,          31.038183333333336),
            ],
            "D": [
                (-17.802675,          31.037944444444445),
                (-17.8027,            31.03784166666667),
                (-17.80305277777778,  31.03793055555556),
                (-17.80302222222222,  31.038027777777778),
            ],
            "E": [
                (-17.80271666666667,  31.03777777777778),
                (-17.80272777777778,  31.037686111111114),
                (-17.80307777777778,  31.037775),
                (-17.803055555555556, 31.03786666666667),
            ],
            "F": [
                (-17.802913888888888, 31.037572222222224),
                (-17.802897222222224, 31.03764166666667),
                (-17.80308888888889,  31.037691666666667),
                (-17.8031,            31.03761111111111),
            ],
        }

        def centroid(points):
            """Return centroid (average of coordinates)."""
            lat = sum(p[0] for p in points) / len(points)
            lng = sum(p[1] for p in points) / len(points)
            return lat, lng

        # --- Create circular slots around centroid ---
        for label, corners in parking_areas.items():
            # Define slot count
            if label == "F":
                total_slots = 8
            else:
                total_slots = 14

            # Compute area centroid
            center_lat, center_lng = centroid(corners)

            # Radius of circular layout (small variations)
            base_radius = 0.0001 + random.uniform(-0.00002, 0.00002)

            # Create area
            area = ParkingArea.objects.create(
                name=f"Avondale Spot {label}",
                total_capacity=total_slots,
                area_type="lot",
                boundary=[{"lat": lat, "lng": lng} for lat, lng in corners],
            )

            self.stdout.write(f"Created area {area.name} with {total_slots} circular slots.")

            # Distribute slots evenly around 360 degrees
            for i in range(total_slots):
                angle_deg = (360 / total_slots) * i
                angle_rad = math.radians(angle_deg)

                # Add slight random offset to radius and angle
                r = base_radius + random.uniform(-0.000015, 0.000015)
                jitter_angle = random.uniform(-5, 5)
                angle_rad += math.radians(jitter_angle)

                lat = center_lat + (r * math.cos(angle_rad))
                lng = center_lng + (r * math.sin(angle_rad))

                slot = ParkingSlot.objects.create(
                    slot_id=f"AVM-{label}-{i+1:02}",
                    area=area,
                    latitude=lat,
                    longitude=lng,
                    is_handicapped=((i + 1) % total_slots == 0),
                    reserved_for=random.choice([None, None, "VIP", "Staff"]),
                )

                SlotStatus.objects.create(
                    slot=slot,
                    is_occupied=random.random() < 0.55,
                    timestamp=timezone.now(),
                )

            self.stdout.write(self.style.SUCCESS(f"✅ {area.name}: {total_slots} slots arranged in a circle."))

        self.stdout.write(self.style.SUCCESS("🎯 Circular Avondale parking data loaded successfully!"))
