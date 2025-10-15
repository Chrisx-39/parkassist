from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SlotStatus, ParkingArea

@receiver(post_save, sender=SlotStatus)
def update_parking_area_counts(sender, instance, **kwargs):
    area = instance.slot.area
    
    # Get the latest status for each slot
    from django.db.models import OuterRef, Subquery
    from .models import SlotStatus

    latest_status = SlotStatus.objects.filter(slot=OuterRef('pk')).order_by('-timestamp')
    occupied_count = area.slots.annotate(
        latest_occupied=Subquery(latest_status.values('is_occupied')[:1])
    ).filter(latest_occupied=True).count()

    area.occupied_count = occupied_count
    area.save(update_fields=['occupied_count'])
