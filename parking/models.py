from django.db import models
from django.utils import timezone
from django.db.models import OuterRef, Subquery


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
    boundary = models.JSONField(blank=True, null=True, help_text="List of coordinates defining area boundary")
    occupied_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Parking Area"
        verbose_name_plural = "Parking Areas"

    def __str__(self):
        return self.name

    @property
    def occupied_slots_count(self):
        """
        Count only slots whose latest status is occupied.
        """
        latest_status = SlotStatus.objects.filter(slot=OuterRef('pk')).order_by('-timestamp')
        return self.slots.annotate(
            latest_occupied=Subquery(latest_status.values('is_occupied')[:1])
        ).filter(latest_occupied=True).count()

    @property
    def available_slots_count(self):
        return self.total_capacity - self.occupied_slots_count


class GarageLevel(models.Model):
    """
    Optional: Multi-level garages within a ParkingArea.
    """
    area = models.ForeignKey(ParkingArea, on_delete=models.CASCADE, related_name='levels')
    level_name = models.CharField(max_length=50)
    level_capacity = models.IntegerField(default=0)
    boundary = models.JSONField(blank=True, null=True, help_text="List of coordinates defining level boundary")

    class Meta:
        verbose_name = "Garage Level"
        verbose_name_plural = "Garage Levels"
        unique_together = ('area', 'level_name')

    def __str__(self):
        return f"{self.area.name} - {self.level_name}"


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
    reserved_for = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Parking Slot"
        verbose_name_plural = "Parking Slots"
        unique_together = ('slot_id', 'area')

    def __str__(self):
        return f"{self.slot_id} ({self.area.name})"

    @property
    def latest_status(self):
        return self.statuses.order_by('-timestamp').first()

    @property
    def is_available(self):
        latest = self.latest_status
        return latest is None or not latest.is_occupied


class Sensor(models.Model):
    """
    Represents IoT sensors monitoring parking slots.
    """
    sensor_id = models.CharField(max_length=50, unique=True)
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, related_name='sensors')
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.sensor_id} ({self.slot.slot_id})"


class RoadNetwork(models.Model):
    """
    Stores street/road data for routing.
    """
    name = models.CharField(max_length=100, blank=True)
    path = models.JSONField(blank=True, null=True, help_text="List of coordinates defining the road segment")
    travel_weight = models.FloatField(default=1.0)

    class Meta:
        verbose_name = "Road Network Segment"
        verbose_name_plural = "Road Network Segments"

    def __str__(self):
        return self.name or f"Road Segment {self.pk}"


# =====================================================================
# 2. Dynamic IoT/Survey Model (Real-Time Status)
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


# =====================================================================
# 3. User & Session Models
# =====================================================================

class UserProfile(models.Model):
    """
    Stores user information (phone-based login).
    """
    phone_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone_number


class ParkingSession(models.Model):
    """
    Tracks a user's parking session, linked to UserProfile.
    """
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='sessions')
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE, related_name='sessions')
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    amount_due = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    feedback = models.TextField(blank=True, null=True)
    is_paid = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"Session for {self.user.phone_number} at {self.slot.slot_id}"

    def calculate_fee(self):
        """
        Calculates parking cost based on duration.
        Example: 0.50 per 30 min.
        """
        end_time = self.end_time or timezone.now()
        duration_minutes = (end_time - self.start_time).total_seconds() / 60
        self.amount_due = round(0.50 * (duration_minutes / 30), 2)
        return self.amount_due


class Suggestions(models.Model):
    """
    Collects user feedback and suggestions.
    """
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='suggestions')
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Suggestion"
        verbose_name_plural = "Suggestions"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Suggestion by {self.user.phone_number if self.user else 'Anonymous'} at {self.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}"