from os import path

from connections.sim.hw.clock_sim import Clock
from connections.sim.hw.rocket_sim import RocketSim, FlightState, FlightEvent
from util.detail import ORK_FILES_PATH

S_TO_US = int(1e6)

def test_simple_flight():
    clock = Clock()
    rocket_sim = RocketSim(clock, path.join(ORK_FILES_PATH, 'simple.ork'))

    assert rocket_sim.get_altitude() == 0
    assert rocket_sim.get_flight_state() == FlightState.STANDBY
    assert len(rocket_sim.get_flight_events()) == 0

    clock.add_time(5 * S_TO_US)
    assert rocket_sim.get_altitude() == 0
    assert rocket_sim.get_flight_state() == FlightState.STANDBY
    assert len(rocket_sim.get_flight_events()) == 0

    rocket_sim.launch()
    assert rocket_sim.get_altitude() == 0
    assert rocket_sim.get_flight_state() == FlightState.FLIGHT
    assert rocket_sim.get_flight_events()[FlightEvent.IGNITION] == 0
    assert rocket_sim.get_flight_events()[FlightEvent.LAUNCH] == 0

    clock.add_time(5 * S_TO_US)
    pre_deploy_alt = rocket_sim.get_altitude()
    assert pre_deploy_alt > 20
    assert rocket_sim.get_flight_state() == FlightState.FLIGHT

    rocket_sim.deploy_recovery()
    assert abs(rocket_sim.get_altitude() - pre_deploy_alt) < 0.5  # Sim is re-run on deployment, ensure smooth transition
    assert rocket_sim.get_flight_state() == FlightState.RECOVERY_DEPLOYED

    clock.add_time(5 * S_TO_US)
    assert rocket_sim.get_altitude() > 10
    assert rocket_sim.get_flight_state() == FlightState.RECOVERY_DEPLOYED
    assert rocket_sim.get_flight_events()[FlightEvent.RECOVERY_DEVICE_DEPLOYMENT] < rocket_sim.get_time_since_launch()

    clock.add_time(5 * S_TO_US)
    assert rocket_sim.get_altitude() <= 0
    assert rocket_sim.get_flight_state() == FlightState.LANDED
    assert rocket_sim.get_flight_events()[FlightEvent.GROUND_HIT] < rocket_sim.get_time_since_launch()

    clock.add_time(5 * S_TO_US)
    assert rocket_sim.get_altitude() <= 0
    assert rocket_sim.get_flight_state() == FlightState.LANDED