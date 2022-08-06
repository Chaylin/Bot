import math
import time
from datetime import date


class Map:
    v_id = None
    world = None
    driver = None
    config = None
    extractor = None
    mongo = None
    logs = {}
    player = None

    map = None
    map_data = []
    villages = {}
    my_location = None
    map_pos = {}
    coords_x = None
    coords_y = None

    last_fetch = 0
    fetch_delay = 8

    def __init__(self, v_id=None, driver=None, config=None, extractor=None, mongo=None, coords_x=None, coords_y=None, world=None):
        self.v_id = v_id
        self.driver = driver
        self.config = config
        self.extractor = extractor
        self.mongo = mongo
        self.coords_x = coords_x
        self.coords_y = coords_y
        self.world = world

    def get_map(self):
        return
        if self.last_fetch + (self.fetch_delay * 3600) > time.time():
            return
        self.player = self.config.read_config("game", "account", "username")
        start_time = time.time()
        self.logs = self.config.get_cache("Logs", date.today())
        self.driver.navigate_map(
            self.world,
            self.v_id,
            self.coords_x,
            self.coords_y,
        )
        time.sleep(3)
        print("Get map data...")
        self.last_fetch = time.time()
        res = self.driver.get_source()
        game_state = self.extractor.game_state(res)
        self.map_data = self.extractor.map_data(res)
        if self.map_data:
            for tile in self.map_data:
                data = tile["data"]
                x = int(data["x"])
                y = int(data["y"])
                vdata = data["villages"]
                # Fix broken parsing
                if type(vdata) is dict:
                    cdata = [{}] * 20
                    for k, v in vdata.items():
                        if type(v) is not dict:
                            cdata[int(k)] = {0: item[0:] for item in v}
                        else:
                            cdata[int(k)] = v
                    vdata = cdata
                for lon, val in enumerate(vdata):
                    if not val:
                        continue
                    # Force dict type to iterate properly
                    if type(val) != dict:
                        val = {i: val[i] for i in range(0, len(val))}

                    for lat, entry in val.items():
                        if not lat:
                            continue
                        coords = [x + int(lon), y + int(lat)]
                        if entry[0] == str(self.v_id):
                            self.my_location = coords

                        self.build_cache_entry(location=coords, entry=entry)
                if not self.my_location:
                    self.my_location = [
                        game_state["village"]["x"],
                        game_state["village"]["y"],
                    ]
        if not self.map_data or not self.villages:
            return self.get_map_old(game_state=game_state)
        self.logs[self.player]['count_scan_map'] += 1
        self.logs[self.player]['time_scan_map'] += time.time() - start_time
        self.config.set_cache("Logs", date.today(), self.logs)
        return True


    def get_map_old(self, game_state):
        if self.map_data:
            for tile in self.map_data:
                data = tile["data"]
                x = int(data["x"])
                y = int(data["y"])
                vdata = data["villages"]
                for lon, lon_val in enumerate(vdata):
                    try:
                        for lat in vdata[lon]:
                            coords = [x + int(lon), y + int(lat)]
                            entry = vdata[lon][lat]
                            if entry[0] == str(self.v_id):
                                self.my_location = coords

                            self.build_cache_entry(location=coords, entry=entry)
                    except:
                        raise
            if not self.my_location:
                self.my_location = [
                    game_state["village"]["x"],
                    game_state["village"]["y"],
                ]
        if not self.map_data or not self.villages:
            print(f"Error: {self.v_id}")
            return False
        return True

    def build_cache_entry(self, location, entry):
        vid = entry[0]
        name = entry[2]
        points = int(entry[3].replace(".", ""))
        player = entry[4]
        bonus = entry[6]
        clan = entry[11]
        structure = {
            "id": vid,
            "name": name,
            "location": location,
            "bonus": bonus,
            "points": points,
            "safe": True,
            "safe for scout": True,
            "last scout": 1654323639,
            "last attack": [1],
            "last ram": 1,
            "last extra": 1,
            "tribe": clan,
            "owner": player,
            "buildings": {},
            "units": {},
            "units_away": {},
            "resources": {},
        }
        self.map_pos[vid] = location
        cached = self.in_cache(vid)
        if not cached:
            self.config.set_cache(cache="map", v_id=vid, entry=structure)
        if cached and cached != structure:
            self.config.set_cache(cache="map", v_id=vid, entry=structure)
        self.villages[vid] = structure
        self.mongo.upload_villages(vid, structure)

    def in_cache(self, vid):
        entry = self.config.get_cache(cache="map", v_id=vid)
        return entry

    @staticmethod
    def get_dist(my_location, ext_loc):
        distance = math.sqrt(
            ((my_location[0] - ext_loc[0]) ** 2)
            + ((my_location[1] - ext_loc[1]) ** 2)
        )
        return distance