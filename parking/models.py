from django.db import models
from django.utils import timezone

# =====================================================================
# 1. Static Models (No GIS)
# =====================================================================

class ParkingArea(models.Model):
    """
    Represents a larger parking structure or zoned area.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Area Name")
    total_capacity = models.IntegerField(default=0)
    area_type = models.CharField(
        max_length=50, 
        choices=[('street','Street'), ('garage','Garage'), ('lot','Lot')]
    )
    # Optional coordinates for approximate boundary (JSON: list of lat/lng)
    boundary = models.JSONField(blank=True, null=True, help_text="List of coordinates defining area boundary")

    class Meta:
        verbose_name = "Parking Area"
        verbose_name_plural = "Parking Areas"

    def __str__(self):
        return self.name

    @property
    def occupied_slots_count(self):
        return self.slots.filter(statuses__is_occupied=True).count()

    @property
    def available_slots_count(self):
        return self.total_capacity - self.occupied_slots_count

# ---------------------------------------------------------------------

class GarageLevel(models.Model):
    """
    Optional: Multi-level garages within a ParkingArea.
    """
    area = models.ForeignKey(ParkingArea, on_delete=models.CASCADE, related_name='levels')
    level_name = models.CharField(max_length=50)
    level_capacity = models.IntegerField(default=0)
    # Optional coordinates for approximate level boundary
    boundary = models.JSONField(blank=True, null=True, help_text="List of coordinates defining level boundary")

    class Meta:
        verbose_name = "Garage Level"
        verbose_name_plural = "Garage Levels"
        unique_together = ('area', 'level_name')

    def __str__(self):
        return f"{self.area.name} - {self.level_name}"

# ---------------------------------------------------------------------

class ParkingSlot(models.Model):
    """
    Represents an individual, uniquely identifiable parking space.
    """
    slot_id = models.CharField(max_length=20, verbose_name="Slot ID")
    area = models.ForeignKey(ParkingArea, on_delete=models.CASCADE, related_name='slots')
    level = models.ForeignKey(GarageLevel, on_delete=models.CASCADE, related_name='slots', null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    is_handicapped = models.BooleanField(default=False)
    reserved_for = models.CharField(max_length=50, blank=True, null=True)  # e.g., VIP, staff

    class Meta:
        verbose_name = "Parking Slot"
        verbose_name_plural = "Parking Slots"
        unique_together = ('slot_id', 'area')

    def __str__(self):
        return f"{self.slot_id} ({self.area.name})"

    @property
    def latest_status(self):
        """Return the most recent status, or None if no status exists."""
        return self.statuses.order_by('-timestamp').first()

    @property
    def is_available(self):
        """Return True if the slot is free (no latest status or not occupied)."""
        latest = self.latest_status
        return latest is None or not latest.is_occupied

# ---------------------------------------------------------------------

class Sensor(models.Model):
    """
    Represents IoT sensors monitoring parking slots.
    """
    sensor_id = models.CharField(max_length=50, unique=True)
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, related_name='sensors')
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.sensor_id} ({self.slot.slot_id})"

# ---------------------------------------------------------------------

class RoadNetwork(models.Model):
    """
    Stores street/road data for routing.
    """
    name = models.CharField(max_length=100, blank=True)
    # Optional list of coordinates representing the road path
    path = models.JSONField(blank=True, null=True, help_text="List of coordinates defining the road segment")
    travel_weight = models.FloatField(default=1.0)  # e.g., travel time factor

    class Meta:
        verbose_name = "Road Network Segment"
        verbose_name_plural = "Road Network Segments"

    def __str__(self):
        return self.name or f"Road Segment {self.pk}"

# =====================================================================
# 2. Dynamic IoT/Survey Model (The Real-Time Status)
# =====================================================================

class SlotStatus(models.Model):
    """
    Ingests real-time data from IoT sensors. True = Occupied, False = Empty.
    """
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, related_name='statuses')
    is_occupied = models.BooleanField()
    timestamp = models.DateTimeField(default=timezone.now)
    sensor = models.ForeignKey(Sensor, on_delete=models.SET_NULL, null=True, blank=True, related_name='statuses')

    class Meta:
        verbose_name = "Slot Status"
        verbose_name_plural = "Slot Statuses"
        ordering = ['-timestamp']

    def __str__(self):
        status = "Occupied" if self.is_occupied else "Empty"
        return f"{self.slot.slot_id}: {status} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
