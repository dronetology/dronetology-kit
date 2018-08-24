import dronekit

# Import DroneKit-Python
from dronekit import connect, VehicleMode, LocationGlobalRelative


def sensors_locations(flight_params):

    sensors_locations=[]
    
    if(flight_params.find("|1")>-1):
        S1_LOCATION = LocationGlobalRelative(42.829882, -1.744423, 0)
        S2_LOCATION = LocationGlobalRelative(42.829862, -1.744728, 0)
        S3_LOCATION = LocationGlobalRelative(42.829848, -1.744865, 0)
        S4_LOCATION = LocationGlobalRelative(42.829854, -1.745154, 0)
    else:
        S1_LOCATION = LocationGlobalRelative(42.829747, -1.745882, 0)
        S2_LOCATION = LocationGlobalRelative(42.828945, -1.744003, 0)
        S3_LOCATION = LocationGlobalRelative(42.829747, -1.745882, 0)
        S4_LOCATION = LocationGlobalRelative(42.828945, -1.744003, 0)

    sensors_locations.append(S1_LOCATION)
    sensors_locations.append(S2_LOCATION)
    sensors_locations.append(S3_LOCATION)
    sensors_locations.append(S4_LOCATION)

    return sensors_locations