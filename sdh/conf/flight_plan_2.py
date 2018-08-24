# Import DroneKit-Python
from dronekit import connect, VehicleMode, LocationGlobalRelative

TARGET_ALTITUDE=15

#42.829693, -1.746195
W1_LOCATION = LocationGlobalRelative(42.829693, -1.746195, TARGET_ALTITUDE)

#42.828755, -1.743634
W2_LOCATION = LocationGlobalRelative(42.828755, -1.743634, TARGET_ALTITUDE)

#42.829780, -1.744387 
W1_CENTROID_LOCATION = LocationGlobalRelative(42.829780, -1.744387, TARGET_ALTITUDE)

