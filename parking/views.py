from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from geopy.distance import geodesic
import random
from .decorators import login_required_phone

from .models import ParkingArea, ParkingSlot, SlotStatus, Sensor, ParkingSession, UserProfile,Suggestions
from django.contrib import messages

# -------------------------
# Phone-based Login
# -------------------------
def login_with_phone(request):
    user_id = request.session.get('user_id')

    # Already logged in
    if user_id:
        try:
            user = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            request.session.flush()
            return redirect('login_with_phone')

        # Check for active session
        active_session = ParkingSession.objects.filter(user=user, end_time__isnull=True).first()
        if active_session:
            # Redirect to the slot detail page of the active session
            return redirect('parking_slot_detail', slot_id=active_session.slot.id)
        else:
            return redirect('index')

    # Handle POST login/create
    if request.method == 'POST':
        phone = request.POST.get('phone')
        if not phone:
            return render(request, 'parking/login.html', {'error': 'Phone number required.'})

        user, _ = UserProfile.objects.get_or_create(phone_number=phone)
        request.session['user_id'] = user.id

        # Check for active session
        active_session = ParkingSession.objects.filter(user=user, end_time__isnull=True).first()
        if active_session:
            return redirect('parking_slot_detail', slot_id=active_session.slot.id)
        else:
            return redirect('index')

    # Handle logout
    if request.GET.get('logout') == '1':
        request.session.flush()
        return redirect('login_with_phone')

    return render(request, 'parking/login.html')

def logout_view(request):
    request.session.flush()  # clear all session data
    return redirect('login_with_phone')  # redirect to login page


# -------------------------
# Dashboard / Landing Page
# -------------------------
@login_required_phone
def index(request):
    areas = ParkingArea.objects.prefetch_related('slots', 'slots__statuses').all()
    recent_statuses = SlotStatus.objects.order_by('-timestamp')[:10]

    user_obj = None
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user_obj = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            request.session.flush()

    user_sessions = ParkingSession.objects.filter(user=user_obj, end_time__isnull=True) if user_obj else []

    return render(request, 'parking/index.html', {
        'areas': areas,
        'recent_statuses': recent_statuses,
        'user_sessions': user_sessions,
    })


# -------------------------
# Parking Areas
# -------------------------
@login_required_phone
def parking_area_list(request):
    areas = ParkingArea.objects.all()
    return render(request, 'parking/parking_area_list.html', {'areas': areas})


@login_required_phone
def parking_area_detail(request, area_id):
    area = get_object_or_404(ParkingArea, pk=area_id)
    slots = area.slots.all()
    return render(request, 'parking/parking_area_detail.html', {'area': area, 'slots': slots})


# -------------------------
# Parking Slot Detail
# -------------------------
@login_required_phone
def parking_slot_detail(request, slot_id):
    slot = get_object_or_404(ParkingSlot, pk=slot_id)
    latest_status = slot.latest_status
    return render(request, 'parking/parking_slot_detail.html', {
        'slot': slot,
        'latest_status': latest_status
    })


# -------------------------
# Occupy / Leave Slot
# -------------------------
@login_required_phone
def occupy_slot(request, slot_id):
    slot = get_object_or_404(ParkingSlot, pk=slot_id)
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login_with_phone')
    user = get_object_or_404(UserProfile, pk=user_id)

    if slot.is_available:
        ParkingSession.objects.create(user=user, slot=slot)
        SlotStatus.objects.create(slot=slot, is_occupied=True, timestamp=timezone.now())

    return redirect('parking_slot_detail', slot_id=slot.id)


@login_required_phone
def leave_slot(request, slot_id):
    slot = get_object_or_404(ParkingSlot, pk=slot_id)
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login_with_phone')
    user = get_object_or_404(UserProfile, pk=user_id)

    session = ParkingSession.objects.filter(user=user, slot=slot, end_time__isnull=True).first()
    if session:
        session.end_time = timezone.now()
        session.calculate_fee()
        session.save()

    SlotStatus.objects.create(slot=slot, is_occupied=False, timestamp=timezone.now())
    return redirect('parking_slot_detail', slot_id=slot.id)


# -------------------------
# Update Slot Status
# -------------------------
@login_required_phone
def update_slot_status(request, slot_id):
    slot = get_object_or_404(ParkingSlot, pk=slot_id)

    if request.method == 'POST':
        is_occupied = request.POST.get('is_occupied') == 'true'
        sensor_id = request.POST.get('sensor_id')
        sensor = None
        if sensor_id:
            sensor, _ = Sensor.objects.get_or_create(sensor_id=sensor_id, slot=slot)
        SlotStatus.objects.create(slot=slot, is_occupied=is_occupied, sensor=sensor, timestamp=timezone.now())
        return redirect('parking_slot_detail', slot_id=slot.id)

    return render(request, 'parking/update_slot_status.html', {'slot': slot})


# -------------------------
# Free Slots, Navigation & API
# -------------------------
@login_required_phone
def find_free_slots(request, area_id):
    area = get_object_or_404(ParkingArea, pk=area_id)
    slots = [slot for slot in area.slots.all() if slot.is_available]
    return render(request, 'parking/free_slots.html', {'area': area, 'slots': slots})


@login_required_phone
def navigate_to_slot(request, slot_id):
    slot = get_object_or_404(ParkingSlot, pk=slot_id)
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')
    return render(request, 'parking/navigate_slot.html', {
        'slot': slot,
        'user_lat': user_lat,
        'user_lng': user_lng
    })


@login_required_phone
def available_slots_json(request):
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


@login_required_phone
def simulate_nearby_slots(request):
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    radius_km = float(request.GET.get('radius', 2.0))
    updates_count = int(request.GET.get('count', 5))

    if not lat or not lng:
        return JsonResponse({"error": "User location (lat/lng) required"}, status=400)

    user_location = (float(lat), float(lng))
    nearby_free_slots = [
        slot for slot in ParkingSlot.objects.all()
        if slot.latitude and slot.longitude and slot.is_available
        and geodesic(user_location, (float(slot.latitude), float(slot.longitude))).km <= radius_km
    ]

    updated_slots = []
    for _ in range(min(updates_count, len(nearby_free_slots))):
        slot = random.choice(nearby_free_slots)
        new_status = random.choice([True, False])
        sensor, _ = Sensor.objects.get_or_create(sensor_id=f"SIM-{slot.slot_id}", slot=slot)
        SlotStatus.objects.create(slot=slot, is_occupied=new_status, sensor=sensor, timestamp=timezone.now())
        updated_slots.append({
            "slot_id": slot.slot_id,
            "area": slot.area.name,
            "status": "Occupied" if new_status else "Available",
            "latitude": float(slot.latitude),
            "longitude": float(slot.longitude)
        })

    return JsonResponse({"updated_slots": updated_slots})


@login_required_phone
def find_by_phone(request):
    phone = request.GET.get('phone')
    if not phone:
        return render(request, 'parking/find_by_phone.html')

    user = UserProfile.objects.filter(phone_number=phone).first()
    if not user:
        return render(request, 'parking/find_by_phone.html', {'error': 'No user found for this number.'})

    session = ParkingSession.objects.filter(user=user, end_time__isnull=True).first()
    if not session:
        return render(request, 'parking/find_by_phone.html', {'error': 'No active session found.'})

    return redirect('parking_slot_detail', slot_id=session.slot.id)


@login_required_phone
def pay_for_parking(request, session_id):
    session = get_object_or_404(ParkingSession, pk=session_id)
    if not session.end_time:
        session.end_time = timezone.now()
    session.calculate_fee()

    if request.method == 'POST':
        session.amount_paid = session.amount_due
        session.is_paid = True
        session.save()
        return render(request, 'parking/payment_success.html', {'session': session})

    return render(request, 'parking/pay_for_parking.html', {'session': session})


@login_required_phone
def suggestion_box(request):
    user_obj = None
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user_obj = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            request.session.flush()

    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            Suggestions.objects.create(user=user_obj, message=message)
            messages.success(request, "Thank you! Your suggestion has been submitted.")
            return redirect('suggestion_box')
        else:
            messages.error(request, "Please enter a suggestion before submitting.")

    suggestions = Suggestions.objects.all()[:10]  # show latest 10 suggestions
    return render(request, 'parking/suggestion_box.html', {
        'suggestions': suggestions,
        'user_obj': user_obj,
    })