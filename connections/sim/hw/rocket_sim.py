from typing import Dict
from enum import Enum, auto
from numpy import interp
from orhelper import OpenRocketInstance, Helper, FlightDataType, FlightEvent
from multiprocessing import Process, Queue

from .clock_sim import Clock
from util.detail import OPEN_ROCKET_PATH

class FlightState(Enum):
    STANDBY = auto()
    FLIGHT = auto()
    RECOVERY_DEPLOYED = auto()
    LANDED = auto()

class RocketSim:

    def __init__(self, clock: Clock, ork_file: str, random_seed: int = 0):
        self._clock = clock
        self._ork_file = ork_file
        self.random_seed = random_seed
        self._state: FlightState = FlightState.STANDBY

        self._launch_time: float = None
        self._recovery_deployment_time: float = None

        # Populate with initial data
        self._data, self._events = self._run_simulation()

    def launch(self):
        assert self.get_flight_state() == FlightState.STANDBY

        self._state = FlightState.FLIGHT
        self._launch_time = self.get_time()

    def deploy_recovery(self):
        assert self.get_flight_state() == FlightState.FLIGHT

        self._recovery_deployment_time = self.get_time_since_launch()
        new_data, new_events = self._run_simulation()

        assert abs(new_events[FlightEvent.RECOVERY_DEVICE_DEPLOYMENT] - self.get_time_since_launch()) < 0.1

        for event, time, in self._events.items():
            if time <= self.get_time_since_launch():
                assert abs(new_events[event] - time) < 0.1

        self._events = {e: t for e, t in self._events.items() if t <= self.get_time_since_launch()}  # Retain original events if already passed
        self._events.update({e: t for e, t in new_events.items() if t >= new_events[FlightEvent.RECOVERY_DEVICE_DEPLOYMENT]})  # Update with new events

        self._state = FlightState.RECOVERY_DEPLOYED
        self._data = new_data

    def get_flight_state(self) -> FlightState:
        if self._state != FlightState.STANDBY and self.get_time_since_launch() >= self._events[FlightEvent.GROUND_HIT]:
            self._state = FlightState.LANDED
        return self._state

    def get_pressure(self) -> float:
        return self._get_data_point(FlightDataType.TYPE_AIR_PRESSURE)

    def get_altitude(self) -> float:
        return self._get_data_point(FlightDataType.TYPE_ALTITUDE)

    def get_acceleration(self) -> float:
        return self._get_data_point(FlightDataType.TYPE_ACCELERATION_Z)

    def get_flight_events(self) -> Dict[FlightEvent, float]:
        if self._state == FlightState.STANDBY:
            return dict()
        else:
            return {e: t for e, t in self._events.items() if t <= self.get_time_since_launch()}

    def get_time(self) -> float:
        return self._clock.get_time_ms() / 1000

    def get_time_since_launch(self) -> float:
        assert self._launch_time is not None
        return self.get_time() - self._launch_time

    def _get_data_point(self, data_type: FlightDataType):
        if self.get_flight_state() == FlightState.STANDBY:
            return self._data[FlightDataType.TYPE_TIME][0]
        else:
            return interp(self.get_time_since_launch(), self._data[FlightDataType.TYPE_TIME], self._data[data_type])

    def _run_simulation(self):
        if self.get_flight_state() == FlightState.STANDBY:
            time_since_launch = None
        else:
            time_since_launch = self.get_time_since_launch()

        # Due to JPype limitations, the JVM cannot be restarted by the same process.
        # https://jpype.readthedocs.io/en/latest/install.html#known-bugs-limitations
        # To work around this, we spawn a new process each time we want to run a simulation.
        q = Queue()
        p = Process(target=_process_simulation, args=(self._ork_file, time_since_launch, self.random_seed, q))
        p.start()
        data, events = q.get()
        p.join()
        p.close()

        assert events[FlightEvent.IGNITION] == 0
        assert events[FlightEvent.LAUNCH] == 0
        assert abs(data[FlightDataType.TYPE_TIME][-1] - events[FlightEvent.GROUND_HIT]) < 0.1
        assert abs(data[FlightDataType.TYPE_TIME][-1] - events[FlightEvent.SIMULATION_END]) < 0.1
        return data, events


def _process_simulation(ork_file, time_since_launch, seed, result_queue):
    with OpenRocketInstance(jar_path=OPEN_ROCKET_PATH) as instance:
        orh = Helper(instance)

        doc = orh.load_doc(ork_file)
        sim = doc.getSimulation(0)

        # Configure
        sim.getOptions().setRandomSeed(seed)
        opts = sim.getOptions()
        opts.setGeodeticComputation(orh.openrocket.util.GeodeticComputationStrategy.FLAT)
        rocket = opts.getRocket()
        parachute = orh.get_component_named(rocket, 'Parachute')

        # From net/sf/openrocket/gui/dialogs/flightconfiguration/DeploymentSelectionDialog.java
        id = rocket.getDefaultConfiguration().getFlightConfigurationID()
        configuration = parachute.getDeploymentConfiguration().get(id).clone()

        if time_since_launch is None:
            configuration.setDeployEvent(orh.openrocket.rocketcomponent.DeploymentConfiguration.DeployEvent.NEVER)
        else:
            configuration.setDeployEvent(orh.openrocket.rocketcomponent.DeploymentConfiguration.DeployEvent.LAUNCH)
            configuration.setDeployDelay(time_since_launch)

        # parachute.getDeploymentConfiguration().set(id, configuration)
        parachute.getDeploymentConfiguration().setDefault(configuration)

        orh.run_simulation(sim)
        data = orh.get_timeseries(sim, [FlightDataType.TYPE_TIME, FlightDataType.TYPE_ALTITUDE,
                                              FlightDataType.TYPE_ACCELERATION_Z, FlightDataType.TYPE_AIR_PRESSURE])
        events = orh.get_events(sim)

    # JVM shut down on `while` statement exit
    result_queue.put((data, events))
