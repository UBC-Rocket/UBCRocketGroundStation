from connections.sim.hw.clock_sim import Clock
from connections.sim.hw.rocket_sim import RocketSim, FlightState, FlightEvent, FlightDataType

S_TO_US = int(1e6)

def test_simple_flight():
    rocket_sim = RocketSim('simple.ork')
    clock = rocket_sim.get_clock()

    assert rocket_sim.get_data(FlightDataType.TYPE_ALTITUDE) == 0
    assert rocket_sim.get_flight_state() == FlightState.STANDBY
    assert len(rocket_sim.get_flight_events()) == 0

    clock.add_time(5 * S_TO_US)
    assert rocket_sim.get_data(FlightDataType.TYPE_ALTITUDE) == 0
    assert rocket_sim.get_flight_state() == FlightState.STANDBY
    assert len(rocket_sim.get_flight_events()) == 0

    rocket_sim.launch()
    assert rocket_sim.get_data(FlightDataType.TYPE_ALTITUDE) == 0
    assert rocket_sim.get_flight_state() == FlightState.FLIGHT
    assert rocket_sim.get_flight_events()[FlightEvent.IGNITION][0] == 0
    assert rocket_sim.get_flight_events()[FlightEvent.LAUNCH][0] == 0

    clock.add_time(5 * S_TO_US)
    pre_deploy_alt = rocket_sim.get_data(FlightDataType.TYPE_ALTITUDE)
    assert pre_deploy_alt > 20
    assert rocket_sim.get_flight_state() == FlightState.FLIGHT

    rocket_sim.deploy_main()
    assert abs(rocket_sim.get_data(FlightDataType.TYPE_ALTITUDE) - pre_deploy_alt) < 0.5  # Sim is re-run on deployment, ensure smooth transition
    assert rocket_sim.get_flight_state() == FlightState.MAIN_DESCENT

    clock.add_time(5 * S_TO_US)
    assert rocket_sim.get_data(FlightDataType.TYPE_ALTITUDE) > 10
    assert rocket_sim.get_flight_state() == FlightState.MAIN_DESCENT
    assert rocket_sim.get_flight_events()[FlightEvent.RECOVERY_DEVICE_DEPLOYMENT][0] < rocket_sim.get_time_since_launch()

    clock.add_time(5 * S_TO_US)
    assert rocket_sim.get_data(FlightDataType.TYPE_ALTITUDE) <= 0
    assert rocket_sim.get_flight_state() == FlightState.LANDED
    assert rocket_sim.get_flight_events()[FlightEvent.GROUND_HIT][0] < rocket_sim.get_time_since_launch()

    clock.add_time(5 * S_TO_US)
    assert rocket_sim.get_data(FlightDataType.TYPE_ALTITUDE) <= 0
    assert rocket_sim.get_flight_state() == FlightState.LANDED