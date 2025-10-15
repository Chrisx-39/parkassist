from django.urls import path
from . import views

urlpatterns = [
    # -------------------------
    # Login / Logout
    # -------------------------
    path('login/', views.login_with_phone, name='login_with_phone'),  # separate login page
    path('', views.index, name='index'),  # default landing page (dashboard)
    path('logout/', views.logout_view, name='logout'), 

    # -------------------------
    # Dashboard / Landing Page
    # -------------------------
    path('dashboard/', views.index, name='index'),

    # -------------------------
    # Parking Areas
    # -------------------------
    path('areas/', views.parking_area_list, name='parking_area_list'),
    path('areas/<int:area_id>/', views.parking_area_detail, name='parking_area_detail'),

    # -------------------------
    # Find Free Slots
    # -------------------------
    path('areas/<int:area_id>/free/', views.find_free_slots, name='find_free_slots'),

    # -------------------------
    # Parking Slot Detail / Navigation
    # -------------------------
    path('slots/<int:slot_id>/', views.parking_slot_detail, name='parking_slot_detail'),
    path('slots/<int:slot_id>/navigate/', views.navigate_to_slot, name='navigate_slot'),
    path('slots/<int:slot_id>/update/', views.update_slot_status, name='update_slot_status'),
    path('slots/<int:slot_id>/occupy/', views.occupy_slot, name='occupy_slot'),
    path('slots/<int:slot_id>/leave/', views.leave_slot, name='leave_slot'),

    # -------------------------
    # API & Simulation
    # -------------------------
    path('api/available-slots/', views.available_slots_json, name='available_slots_json'),
    path('simulate-nearby/', views.simulate_nearby_slots, name='simulate_nearby_slots'),

    # -------------------------
    # Find by phone & payment
    # -------------------------
    path('find-by-phone/', views.find_by_phone, name='find_by_phone'),
    path('pay/<int:session_id>/', views.pay_for_parking, name='pay_for_parking'),


    path('suggestions/', views.suggestion_box, name='suggestion_box'),
]
