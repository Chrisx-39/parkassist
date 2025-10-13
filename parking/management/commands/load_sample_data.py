from django.core.management.base import BaseCommand
from parking.models import ParkingArea, ParkingSlot, SlotStatus
from django.utils import timezone
import random
import math

class Command(BaseCommand):
    help = "Load Avondale Mall parking data (A–F) with realistic slot offsets distributed within each polygon."

    def handle(self, *args, **kwargs):
        self.stdout.write("🅿️ Loading Avondale parking spots A–F with improved slot offsets...")

        # Clear existing data
        SlotStatus.objects.all().delete()
        ParkingSlot.objects.all().delete()
        ParkingArea.objects.all().delete()

        # --- Exact polygon boundaries (converted from DMS to decimal) ---
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
            """Compute centroid (average of vertices)."""
            lat = sum(p[0] for p in points) / len(points)
            lng = sum(p[1] for p in points) / len(points)
            return lat, lng

        def interpolate(p1, p2, t):
            """Linear interpolation between two points."""
            return (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)

        # --- Create areas & slots ---
        for label, corners in parking_areas.items():
            area = ParkingArea.objects.create(
                name=f"Avondale Spot {label}",
                total_capacity=12,
                area_type="lot",
                boundary=[{"lat": lat, "lng": lng} for lat, lng in corners]
            )

            self.stdout.write(f"Created area {area.name} with {len(corners)} corners.")

            # We’ll create 3x4 grid slots across two polygon edges
            edge_bottom = [corners[0], corners[1]]
            edge_top = [corners[3], corners[2]]

            slot_index = 1
            rows, cols = 3, 4
            for r in range(rows):
                row_t = r / (rows - 1)
                start_row = interpolate(edge_bottom[0], edge_top[0], row_t)
                end_row = interpolate(edge_bottom[1], edge_top[1], row_t)

                for c in range(cols):
                    col_t = c / (cols - 1)
                    lat, lng = interpolate(start_row, end_row, col_t)

                    # Small jitter: random few meters offset
                    lat += random.uniform(-0.000015, 0.000015)
                    lng += random.uniform(-0.000015, 0.000015)

                    slot = ParkingSlot.objects.create(
                        slot_id=f"AVM-{label}-{slot_index:02}",
                        area=area,
                        latitude=lat,
                        longitude=lng,
                        is_handicapped=(slot_index % 12 == 0),
                        reserved_for=random.choice([None, None, "VIP", "Staff"])
                    )

                    # Initial occupancy (~55%)
                    occupied = random.random() < 0.55
                    SlotStatus.objects.create(
                        slot=slot,
                        is_occupied=occupied,
                        timestamp=timezone.now()
                    )

                    slot_index += 1

            self.stdout.write(self.style.SUCCESS(f"✅ {area.name}: {slot_index - 1} slots placed neatly."))

        self.stdout.write(self.style.SUCCESS("🎯 Avondale precise parking data with better offsets loaded successfully!"))
