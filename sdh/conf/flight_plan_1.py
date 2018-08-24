# Import DroneKit-Python
from dronekit import connect, VehicleMode, LocationGlobalRelative

TARGET_ALTITUDE=15

#42.829654, -1.744908
W1_LOCATION = LocationGlobalRelative(42.829654, -1.744908, TARGET_ALTITUDE)

#42.829693, -1.746195
W2_LOCATION = LocationGlobalRelative(42.829693, -1.746195, TARGET_ALTITUDE)

#42.829905, -1.744416
W1_CENTROID_LOCATION = LocationGlobalRelative(42.829905, -1.744416, TARGET_ALTITUDE)

