from django.urls import path
from . import views


urlpatterns = [
    # -------------------------
    # Dashboard / Landing Page
    # -------------------------
    path('', views.index, name='index'),

    # -------------------------
    # Parking Areas
    # -------------------------
    path('areas/', views.parking_area_list, name='parking_area_list'),
    path('areas/<int:area_id>/', views.parking_area_detail, name='parking_area_detail'),

    # -------------------------
    # Find Free Slots in a Parking Area
    # -------------------------
    path('areas/<int:area_id>/free/', views.find_free_slots, name='find_free_slots'),

    # -------------------------
    # Parking Slot Detail
    # -------------------------
    path('slots/<int:slot_id>/', views.parking_slot_detail, name='parking_slot_detail'),

    # -------------------------
    # Navigate to a Free Slot
    # -------------------------
    path('slots/<int:slot_id>/navigate/', views.navigate_to_slot, name='navigate_slot'),

    # -------------------------
    # Update Slot Status (occupy / free)
    # -------------------------
    path('slots/<int:slot_id>/update/', views.update_slot_status, name='update_slot_status'),

      # JSON endpoint
    path('api/available-slots/', views.available_slots_json, name='available_slots_json'),

    path('simulate-nearby/', views.simulate_nearby_slots, name='simulate_nearby_slots'),

]
