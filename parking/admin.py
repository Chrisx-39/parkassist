from django.contrib import admin
from .models import (
    ParkingArea, GarageLevel, ParkingSlot,
    Sensor, SlotStatus, RoadNetwork
)

# =====================================================================
# Inline Admins
# =====================================================================

class GarageLevelInline(admin.TabularInline):
    model = GarageLevel
    extra = 1
    show_change_link = True


class ParkingSlotInline(admin.TabularInline):
    model = ParkingSlot
    extra = 1
    show_change_link = True


class SlotStatusInline(admin.TabularInline):
    model = SlotStatus
    extra = 0
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)


# =====================================================================
# Main Model Admins
# =====================================================================

@admin.register(ParkingArea)
class ParkingAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'area_type', 'total_capacity', 'occupied_slots_count', 'available_slots_count')
    list_filter = ('area_type',)
    search_fields = ('name',)
    inlines = [GarageLevelInline, ParkingSlotInline]
    readonly_fields = ('occupied_slots_count', 'available_slots_count')

    fieldsets = (
        ("Basic Info", {"fields": ("name", "area_type", "total_capacity")}),
        ("Geometry", {"fields": ("boundary",)}),
    )


@admin.register(GarageLevel)
class GarageLevelAdmin(admin.ModelAdmin):
    list_display = ('level_name', 'area', 'level_capacity')
    list_filter = ('area',)
    search_fields = ('level_name', 'area__name')


@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_id', 'area', 'level', 'is_handicapped', 'reserved_for', 'latitude', 'longitude', 'status_display')
    list_filter = ('area', 'is_handicapped', 'level')
    search_fields = ('slot_id', 'area__name', 'reserved_for')
    inlines = [SlotStatusInline]

    def status_display(self, obj):
        latest = obj.latest_status
        if not latest:
            return "No Data"
        return "Occupied" if latest.is_occupied else "Free"
    status_display.short_description = "Current Status"
    status_display.admin_order_field = 'statuses__is_occupied'


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('sensor_id', 'slot', 'description')
    search_fields = ('sensor_id', 'slot__slot_id')


@admin.register(SlotStatus)
class SlotStatusAdmin(admin.ModelAdmin):
    list_display = ('slot', 'is_occupied', 'timestamp', 'sensor')
    list_filter = ('is_occupied', 'timestamp')
    search_fields = ('slot__slot_id', 'sensor__sensor_id')
    ordering = ('-timestamp',)


@admin.register(RoadNetwork)
class RoadNetworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'travel_weight')
    search_fields = ('name',)
    list_filter = ('travel_weight',)
