import multiprocessing
import numpy as np
from os import path
from typing import Dict, List, Union, Tuple, Iterable
from enum import Enum, auto
from orhelper import OpenRocketInstance, Helper, FlightDataType, FlightEvent
from multiprocessing import Process, Queue

from .clock_sim import Clock
from util.detail import LOGGER, OPEN_ROCKET_PATH, ORK_FILES_PATH


class FlightState(Enum):
    STANDBY = auto()
    FLIGHT = auto()
    DROGUE_DESCENT = auto()
    MAIN_DESCENT = auto()
    LANDED = auto()


class RocketSim:

    def __init__(self, ork_file_name: str, random_seed: int = 0,
                 drogue_component_name: str = 'Drogue', main_component_name: str = 'Main'):
        self._clock = Clock()
        self._ork_file = path.join(ORK_FILES_PATH, ork_file_name)
        self._random_seed = random_seed
        self._drogue_component_name = drogue_component_name
        self._main_component_name = main_component_name

        self._state: FlightState = FlightState.STANDBY
        self._launch_time: float = None
        self._drogue_deployment_time: float = None
        self._main_deployment_time: float = None

        multiprocessing.set_start_method('spawn', True)

        # Populate with initial data
        self._data, self._events = self._run_simulation()

    def launch(self) -> None:
        assert self.get_flight_state() == FlightState.STANDBY

        self._state = FlightState.FLIGHT
        self._launch_time = self.get_time()

        LOGGER.info(
            f"Rocket launched at time {self.get_time()} s, and altitude {self.get_data(FlightDataType.TYPE_ALTITUDE)} m")

    def deploy_drogue(self) -> None:
        assert self.get_flight_state() == FlightState.FLIGHT
        self._state = FlightState.DROGUE_DESCENT
        self._deploy_recovery()

    def deploy_main(self) -> None:
        assert self.get_flight_state() in (FlightState.FLIGHT, FlightState.DROGUE_DESCENT)
        self._state = FlightState.MAIN_DESCENT
        self._deploy_recovery()

    def _deploy_recovery(self):
        if self.get_flight_state() == FlightState.DROGUE_DESCENT: # Drogue deploying
            self._drogue_deployment_time = self.get_time_since_launch()
        elif self.get_flight_state() == FlightState.MAIN_DESCENT: # Main deploying
            self._main_deployment_time = self.get_time_since_launch()
        else:
            assert False

        new_data, new_events = self._run_simulation()

        assert abs(new_events[FlightEvent.RECOVERY_DEVICE_DEPLOYMENT][-1] - self.get_time_since_launch()) < 0.1

        merged_events = dict()

        # Retain original events if already passed
        for event, times in self._events.items():
            for i in range(len(times)):
                time = times[i]
                if time <= self.get_time_since_launch():

                    if i in range(len(new_events[event])):
                        assert abs(new_events[event][i] - time) < 0.5 # TODO: Figure out where slight discrepancies come from

                    if event in merged_events:
                        merged_events[event].append(time)
                    else:
                        merged_events[event] = [time]

        # Update with new events
        for event, times in new_events.items():
            for time in times:
                if time >= new_events[FlightEvent.RECOVERY_DEVICE_DEPLOYMENT][-1]:
                    if event in merged_events:
                        merged_events[event].append(time)
                    else:
                        merged_events[event] = [time]

        self._data = new_data
        self._events = merged_events

        LOGGER.info(
            f"Recovery deployed at time {self.get_time()} s, and altitude {self.get_data(FlightDataType.TYPE_ALTITUDE)} m")

    def get_flight_state(self) -> FlightState:
        if self._state != FlightState.STANDBY and self.get_time_since_launch() >= self._events[FlightEvent.GROUND_HIT][0]:
            self._state = FlightState.LANDED
        return self._state

    def get_flight_events(self) -> Dict[FlightEvent, List[float]]:
        if self._state == FlightState.STANDBY:
            return dict()
        else:
            events = dict()

            # Retain original events if already passed
            for event, times in self._events.items():
                for time in times:
                    if time <= self.get_time_since_launch():
                        if event in events:
                            events[event].append(time)
                        else:
                            events[event] = [time]

        return events

    def get_time(self) -> float:
        return self._clock.get_time_ms() / 1000

    def get_time_since_launch(self) -> float:
        assert self._launch_time is not None
        return self.get_time() - self._launch_time

    def get_time_series(self, data_type: FlightDataType) -> Tuple[Iterable[float], Iterable[float]]:
        times = self._data[FlightDataType.TYPE_TIME]
        data = self._data[data_type]
        current_time = self.get_time_since_launch()

        end_index = 0
        for i in range(len(times)):
            if times[i] < current_time:
                end_index = i
            else:
                break

        return np.copy(times[:end_index+1]), np.copy(data[:end_index+1])

    def get_data(self, data_type: FlightDataType) -> float:
        if self.get_flight_state() == FlightState.STANDBY:
            return self._data[data_type][0]
        else:
            return np.interp(self.get_time_since_launch(), self._data[FlightDataType.TYPE_TIME], self._data[data_type])

    def get_clock(self) -> Clock:
        return self._clock

    def get_launch_time(self) -> Union[float, None]:
        return self._launch_time

    def get_drogue_deployment_time(self) -> Union[float, None]:
        return self._drogue_deployment_time

    def get_main_deployment_time(self) -> Union[float, None]:
        return self._main_deployment_time

    def _run_simulation(self):
        # Due to JPype limitations, the JVM cannot be restarted by the same process.
        # https://jpype.readthedocs.io/en/latest/install.html#known-bugs-limitations
        # To work around this, we spawn a new process each time we want to run a simulation.
        q = Queue()
        p = Process(target=_process_simulation, args=(
            self._ork_file,
            self._random_seed,
            self._drogue_deployment_time,
            self._main_deployment_time,
            self._drogue_component_name,
            self._main_component_name,
            q
        ))

        p.start()
        result = q.get()
        p.join()
        p.close()

        if isinstance(result, Exception):
            raise result

        data, events = result

        assert events[FlightEvent.IGNITION][0] == 0
        assert events[FlightEvent.LAUNCH][0] == 0
        assert abs(data[FlightDataType.TYPE_TIME][-1] - events[FlightEvent.GROUND_HIT][0]) < 0.1
        assert abs(data[FlightDataType.TYPE_TIME][-1] - events[FlightEvent.SIMULATION_END][0]) < 0.1
        return data, events

    def shutdown(self):
        pass # TODO: Ensure that process is closed


def _process_simulation(
        ork_file,
        seed,
        drogue_deployment_time,
        main_deployment_time,
        drogue_component_name,
        main_component_name,
        result_queue):
    try:
        with OpenRocketInstance(jar_path=OPEN_ROCKET_PATH) as instance:
            try:
                orh = Helper(instance)

                doc = orh.load_doc(ork_file)
                sim = doc.getSimulation(0)

                # Configure
                sim.getOptions().setRandomSeed(seed)
                opts = sim.getOptions()
                opts.setGeodeticComputation(orh.openrocket.util.GeodeticComputationStrategy.FLAT)

                # Setup drogue
                _setup_recovery_device(orh, opts, drogue_component_name, drogue_deployment_time)

                # Setup main
                _setup_recovery_device(orh, opts, main_component_name, main_deployment_time)

                orh.run_simulation(sim)
                data = orh.get_timeseries(sim, list(FlightDataType))

                events = orh.get_events(sim)

            except Exception as ex: # Must convert exception java string to regular string before leaving JVM
                result_queue.put(Exception(f"Error inside JVM: {ex}"))
                return

    except Exception:
        result_queue.put(Exception("Error starting OpenRocket"))
        return

    # JVM shut down on `while` statement exit
    result_queue.put((data, events))

def _setup_recovery_device(orh, opts, component_name, time):

    rocket = opts.getRocket()
    id = rocket.getDefaultConfiguration().getFlightConfigurationID()
    try:
        parachute = orh.get_component_named(rocket, component_name)
    except ValueError:
        if time is not None:
            raise
    else:
        configuration = parachute.getDeploymentConfiguration().get(id).clone()
        if time is None:
            configuration.setDeployEvent(orh.openrocket.rocketcomponent.DeploymentConfiguration.DeployEvent.NEVER)
        else:
            configuration.setDeployEvent(orh.openrocket.rocketcomponent.DeploymentConfiguration.DeployEvent.LAUNCH)
            configuration.setDeployDelay(time)

        parachute.getDeploymentConfiguration().set(id, configuration)
        parachute.getDeploymentConfiguration().setDefault(configuration)
