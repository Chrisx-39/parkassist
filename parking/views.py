from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import ParkingArea, ParkingSlot, SlotStatus, Sensor
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from geopy.distance import geodesic
import random

# -------------------------
# Dashboard / Landing Page
# -------------------------
def index(request):
    areas = ParkingArea.objects.prefetch_related('slots', 'slots__statuses').all()
    recent_statuses = SlotStatus.objects.order_by('-timestamp')[:10]
    return render(request, 'parking/index.html', {
        'areas': areas,
        'recent_statuses': recent_statuses
    })


# -------------------------
# List all Parking Areas
# -------------------------
def parking_area_list(request):
    areas = ParkingArea.objects.all()
    return render(request, 'parking/parking_area_list.html', {'areas': areas})


# -------------------------
# List Slots in a Parking Area
# -------------------------
def parking_area_detail(request, area_id):
    area = get_object_or_404(ParkingArea, pk=area_id)
    slots = area.slots.all()
    return render(request, 'parking/parking_area_detail.html', {'area': area, 'slots': slots})


# -------------------------
# Slot Detail & Status
# -------------------------
def parking_slot_detail(request, slot_id):
    slot = get_object_or_404(ParkingSlot, pk=slot_id)
    latest_status = slot.latest_status
    return render(request, 'parking/parking_slot_detail.html', {
        'slot': slot,
        'latest_status': latest_status
    })


# -------------------------
# Update Slot Status (simulate IoT)
# -------------------------
def update_slot_status(request, slot_id):
    slot = get_object_or_404(ParkingSlot, pk=slot_id)
    
    if request.method == 'POST':
        is_occupied = request.POST.get('is_occupied') == 'true'
        sensor_id = request.POST.get('sensor_id', None)
        sensor = None
        if sensor_id:
            sensor, _ = Sensor.objects.get_or_create(sensor_id=sensor_id, slot=slot)
        SlotStatus.objects.create(slot=slot, is_occupied=is_occupied, sensor=sensor, timestamp=timezone.now())
        return HttpResponseRedirect(reverse('parking_slot_detail', args=[slot.id]))

    return render(request, 'parking/update_slot_status.html', {'slot': slot})


# -------------------------
# Find Free Slots in a Parking Area
# -------------------------
def find_free_slots(request, area_id):
    area = get_object_or_404(ParkingArea, pk=area_id)
    # Only slots that are free (latest_status not occupied)
    slots = [slot for slot in area.slots.all() if slot.is_available]
    return render(request, 'parking/free_slots.html', {'area': area, 'slots': slots})


# -------------------------
# Navigate to a Free Slot
# -------------------------
def navigate_to_slot(request, slot_id):
    slot = get_object_or_404(ParkingSlot, pk=slot_id)
    
    # Get user's location from GET parameters (lat & lng)
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    
    return render(request, 'parking/navigate_slot.html', {
        'slot': slot,
        'user_lat': user_lat,
        'user_lng': user_lng
    })


def available_slots_json(request):
    """
    Returns a JSON list of available parking slots with coordinates.
    """
    slots = ParkingSlot.objects.prefetch_related('statuses').all()
    available_slots = [
        {
            "slot_id": slot.slot_id,
            "area": slot.area.name,
            "latitude": float(slot.latitude) if slot.latitude else None,
            "longitude": float(slot.longitude) if slot.longitude else None,
            "is_handicapped": slot.is_handicapped,
            "reserved_for": slot.reserved_for,
            "status": "Available" if slot.is_available else "Occupied",
        }
        for slot in slots if slot.is_available and slot.latitude and slot.longitude
    ]
    return JsonResponse({"slots": available_slots})

import random
from django.utils import timezone
from django.http import JsonResponse
from geopy.distance import geodesic
from .models import ParkingSlot, SlotStatus, Sensor

def simulate_nearby_slots(request):
    """
    AJAX endpoint to simulate IoT updates for FREE slots near the user.
    Expects GET parameters: lat, lng, radius (km), count
    """
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    radius_km = float(request.GET.get('radius', 2.0))
    updates_count = int(request.GET.get('count', 5))

    if not lat or not lng:
        return JsonResponse({"error": "User location (lat/lng) required"}, status=400)

    user_location = (float(lat), float(lng))

    # Filter nearby free slots
    nearby_free_slots = []
    for slot in ParkingSlot.objects.all():
        if slot.latitude is not None and slot.longitude is not None:
            # Only consider free slots
            if getattr(slot, 'is_available', True):
                slot_location = (float(slot.latitude), float(slot.longitude))
                if geodesic(user_location, slot_location).km <= radius_km:
                    nearby_free_slots.append(slot)

    if not nearby_free_slots:
        return JsonResponse({"message": "No nearby free slots found"}, status=200)

    updated_slots = []

    for _ in range(updates_count):
        slot = random.choice(nearby_free_slots)
        new_status = random.choice([True, False])  # True = occupied, False = free
        sensor, _ = Sensor.objects.get_or_create(sensor_id=f"SIM-{slot.slot_id}", slot=slot)

        # Save new slot status
        SlotStatus.objects.create(
            slot=slot,
            is_occupied=new_status,
            sensor=sensor,
            timestamp=timezone.now()
        )

        updated_slots.append({
            "slot_id": slot.slot_id,
            "area": slot.area.name,
            "status": "Occupied" if new_status else "Available",
            "latitude": float(slot.latitude),
            "longitude": float(slot.longitude)
        })

    return JsonResponse({"updated_slots": updated_slots})