from math import sqrt
import json

INSTANCE_ID_RANGE_START = 9_000_000
OBJECT_LIMIT = 512

def calculate_rotation(last, next):
    clockwise = (next - last) % 360
    counter_clockwise = (last - next) % 360

    if clockwise < counter_clockwise:
        return clockwise
    else:
        return -counter_clockwise

def distance_between_points(p1, p2):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    return sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)

class Demofile:
    def __init__(self, sample_rate, filepath="demofile.json"):
        self.filepath = filepath
        self.sample_rate = sample_rate

        self.last_save_time = None
        self.last_save_pos = None
        self.last_save_rot = None
        self.last_waypoint = None
        self.next_instance_id = INSTANCE_ID_RANGE_START

        self.platform_id = None
        self.player_actor_id = None

        self.data = dict()
        self.data["waypoints"] = list()
        self.data["actorRotates"] = list()
        self.data["platforms"] = list()
        self.data["playerActors"] = list()
        self.data["timers"] = list()
        self.data["addConnections"] = list()

    def object_count(self):
        return self.next_instance_id - INSTANCE_ID_RANGE_START

    def _next_id(self):
        id = self.next_instance_id
        self.next_instance_id += 1
        return id

    def process_sample(self, sample, force=False):
        (time, pos, rot) = sample

        # Calculate delta-time, the amount of time it took to reach this location
        delta_time = None
        if self.last_save_time is not None:
            delta_time = time - self.last_save_time

            # Skip faster than nyquist
            if delta_time < 1/(self.sample_rate*2):
                return

        # Calculate delta-distance, the space covered to reach this location
        delta_distance = None
        if self.last_save_pos is not None:
            delta_distance = distance_between_points(self.last_save_pos, pos)
            if delta_distance < 0.1:
                delta_distance = None

        # Calculate delta-rotation, the amount the player rotated while moving to this location
        actor_rotate_id = None
        delta_rot_deg = None
        if self.last_save_rot is not None:
            delta_rot_deg = calculate_rotation(self.last_save_rot, rot)
            if abs(delta_rot_deg) < 0.5:
                delta_rot_deg = None
                actor_rotate_id = None
            else:
                actor_rotate_id = self._next_id()

        if not force and self.last_waypoint and delta_rot_deg is None and delta_distance is None:
            return # The player stood still

        # Calculate how long the player spent at the previous location
        # and how fast they moved to get to this location

        if not self.last_waypoint:
            # The start of the waypoint chain
            speed = 30
            last_pause = None
        elif delta_distance is None:
            # The player stood still
            speed = None
            if delta_time:
                last_pause = delta_time
        else:
            # The player moved
            speed = delta_distance/delta_time
            last_pause = None

        pos = [pos[0], pos[1], pos[2]]
        waypoint_id = self._next_id()

        # If the player didn't move, set a pause at the last waypoint
        if last_pause and self.last_waypoint:
            last_waypoint = self.data["waypoints"][-1]
            assert last_waypoint["id"] == self.last_waypoint

            timer_id = self._next_id()
            self.data["timers"].append(
                {
                    "id": timer_id,
                    "time": last_pause,
                }
            )
            self.data["addConnections"].append(
                {
                    "senderId": self.last_waypoint,
                    "state": "ARRIVED",
                    "targetId": timer_id,
                    "message": "RESET_AND_START",
                }
            )
            self.data["addConnections"].append(
                {
                    "senderId": timer_id,
                    "state": "ZERO",
                    "targetId": waypoint_id,
                    "message": "ACTIVATE",
                }
            )

        # Create empty platform at first position
        if self.platform_id is None:
            self.platform_id = self._next_id()
            self.data["platforms"].append(
                {
                    "id": self.platform_id,
                    "position": pos,
                    "type": "Empty"
                }
            )

            # Follow the waypoint chain starting with the first waypoint
            self.data["addConnections"].append(
                {
                    "senderId": self.platform_id,
                    "state": "PLAY",
                    "targetId": waypoint_id,
                    "message": "FOLLOW",
                }
            )

        # Player actor which follows platform
        if self.player_actor_id is None:
            self.player_actor_id = self._next_id()
            self.data["playerActors"].append(
                {
                    "id": self.player_actor_id,
                    "position": pos,
                    "rotation": [0, 0, rot],
                }
            )
            self.data["addConnections"].append(
                {
                    "senderId": self.platform_id,
                    "state": "PLAY",
                    "targetId": self.player_actor_id,
                    "message": "ACTIVATE",
                }
            )

        # Create a new waypoint at the destination position
        self.data["waypoints"].append(
            {
                "id": waypoint_id,
                **({"active": False} if last_pause else {}),
                "position": pos,
                **({"speed": speed} if speed else {}),
            }
        )

        # Define the rotation across this period/distance
        if actor_rotate_id:
            self.data["actorRotates"].append(
                {
                    "id": actor_rotate_id,
                    "rotation": [0, 0, delta_rot_deg],
                    "timeScale": delta_time,
                    "updateActive": True,
                    "updateOnCreation": False,
                    "updateActors": False,
                }
            )

        if self.last_waypoint:
            # Chain previous waypoint into this one
            self.data["addConnections"].append(
                {
                    "senderId": self.last_waypoint,
                    "state": "ARRIVED",
                    "targetId": waypoint_id,
                    "message": "NEXT",
                }
            )

            # Apply rotation while approaching this waypoint
            if actor_rotate_id:
                self.data["addConnections"].append(
                    {
                        "senderId": self.last_waypoint,
                        "state": "ARRIVED",
                        "targetId": actor_rotate_id,
                        "message": "ACTION",
                    }
                )
                self.data["addConnections"].append(
                    {
                        "senderId": actor_rotate_id,
                        "state": "PLAY",
                        "targetId": self.player_actor_id,
                        "message": "PLAY",
                    }
                )

        self.last_waypoint = waypoint_id
        self.last_save_time = time

        if self.last_save_pos is None or delta_distance:
            self.last_save_pos = pos

        if self.last_save_rot is None or delta_rot_deg:
            self.last_save_rot = rot

        print(f"{time:.1f}: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}, {rot:.1f})")
        # if delta_rot_deg:
        #     print(f"    rot:  {delta_rot_deg:.1f} to reach {rot:.1f}")

        # if delta_distance:
        #     print(f"    dist: {delta_distance:.1f}")

        if self.object_count() > OBJECT_LIMIT:
            raise Exception("Object limit reached")


    def commit(self, final_sample):
        self.process_sample(final_sample, force=True)
        assert len(self.data["waypoints"]) > 1
        first_waypoint = self.data["waypoints"][0]["id"]
        last_waypoint = self.data["waypoints"][-1]["id"]

        # Connect the final waypoint back to the first
        connections = [
            {
                "senderId": last_waypoint,
                "state": "ARRIVED",
                "targetId": first_waypoint,
                "message": "NEXT",
            }
        ]

        # Reset all the pause locations
        for waypoint in self.data["waypoints"]:
            if waypoint.get("active") == False:
                connections.append(
                    {
                        "senderId": last_waypoint,
                        "state": "ARRIVED",
                        "targetId": waypoint["id"],
                        "message": "DEACTIVATE",
                    }
                )

        self.data["addConnections"].extend(connections)

        start_rot_deg = self.data["playerActors"][0]["rotation"][2]
        end_rot_deg = self.last_save_rot

        delta_rot_deg = calculate_rotation(end_rot_deg, start_rot_deg)

        actor_rotate_id = self._next_id()
        self.data["actorRotates"].append(
            {
                "id": actor_rotate_id,
                "rotation": [0, 0, delta_rot_deg],
                "timeScale": 0.1,
                "updateActive": True,
                "updateOnCreation": False,
                "updateActors": False
            }
        )
        self.data["addConnections"].append(
            {
                "senderId": last_waypoint,
                "state": "ARRIVED",
                "targetId": actor_rotate_id,
                "message": "ACTION",
            }
        )
        self.data["addConnections"].append(
            {
                "senderId": actor_rotate_id,
                "state": "PLAY",
                "targetId": self.player_actor_id,
                "message": "PLAY",
            }
        )

        with open(self.filepath, 'w') as file:
            file.write(json.dumps(self.data))

        print(f"Saved recording to '{self.filepath}' (Used {self.object_count()} objects)")
