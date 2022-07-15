from Game.attack import AttackManager
from Game.building import Building
from Game.gather import Gather
from Game.recruit import Recruit

from datetime import datetime
from datetime import timedelta
import time


class Village:
    vil_settings = None
    acc_settings = None

    v_id = None
    v_name = None
    location = []
    world = None
    units = {}
    total_units = {}
    list_buildorder = []
    dict_buildings = {}
    game_data = {}
    extractor = None
    config = None
    driver = None
    map = None
    reporter = None
    mongo = None

    building = None
    gathering = None
    farming = None
    recruiting = None
    defence = None
    next_time_build = None
    next_time_gather = None
    next_time_farm = None
    next_time_recruit = None

    def __init__(self, v_id=None,
                 driver=None,
                 game_data=None,
                 config=None,
                 extractor=None,
                 mongo=None,
                 map=None
                 ):
        self.v_id = v_id
        self.driver = driver
        self.config = config
        self.extractor = extractor
        self.game_data = game_data
        self.units = {}
        self.total_units = {}
        self.mongo = mongo
        self.map = map
        self.next_time_build = None
        self.next_time_gather = None
        self.next_time_recruit = None
        self.next_time_farm = None
        self.clear_village = []
        self.v_name = game_data["village"]["display_name"]
        self.world = self.config.read_config("game", "account", "world")
        self.location = [
            game_data["village"]["x"],
            game_data["village"]["y"],
        ]

    def synch_data(self, vil_settings, acc_settings):
        self.vil_settings = vil_settings
        self.acc_settings = acc_settings

    def attack_ds_ultimate(self):
        attack_list = self.config.get_list("DS_Ultimate_Import")
        # own ID & target ID & slowest unit & impact & attack type &
        for attacks in attack_list:
            entry = attacks.split("&")
            if int(entry[0]) == self.v_id:
                print(f"There is a attack listed for [{self.v_name}] \n"
                      f"Checking range and coords")
                # target_entry = self.mongo.get_villages(x[1])
                self.driver.navigate_attack(self.world, self.v_id, entry[1])
                target_tmp = self.driver.get_coords_from_target()
                print(target_tmp)
                x = int(self.find_between(target_tmp, '(', '|'))
                y = int(self.find_between(target_tmp, '|', ')'))
                coords = [
                    x,
                    y,
                ]
                distance = self.map.get_dist(self.location, coords)
                unit_table = {
                    "ram": 30,
                    "spear": 18,
                    "axe": 18,
                    "catapult": 30,
                    "snob": 30,
                    "light": 10,
                    "spy": 9,
                    "sword": 22,
                    "heavy": 11,
                }
                running_time = distance * unit_table[entry[2]] * 60
                send_time = int(entry[3]) - running_time
                types = {
                    "8": "Attack",
                    "11": "Conquer",
                    "14": "Fake",
                    "45": "WallCrush",
                }

                print(f"Own ID:         {entry[0]} \n"
                      f"Target ID:      {entry[1]} \n"
                      f"Target Coords:  {coords} \n"
                      f"Distance:       {distance} \n"
                      f"Slowest Unit:   {entry[2]} \n"
                      f"Running Time:   {time.strftime('%H:%M:%S', time.gmtime(running_time))} seconds \n"
                      f"Send_Time:      {datetime.fromtimestamp(send_time)} \n"
                      f"Impact:         {datetime.fromtimestamp(entry[3])} \n"
                      f"Attack Type:    {types[entry[4]]} \n")

                now = datetime.timestamp(datetime.now())
                diff_time = send_time - now
                if diff_time < 300:
                    print(f"{diff_time} seconds lasts for attacking [{entry[1]}]")
                    self.driver.navigate_attack(self.world, self.v_id, entry[1])
                    self.driver.attack_ds_ultimate(types[entry[4]])

    def build(self):
        if not bool(self.vil_settings["build"]):
            self.next_time_build = "Building is set to false"
            return
        if not self.building:
            self.building = Building(
                v_id=self.v_id,
                driver=self.driver,
                config=self.config,
                extractor=self.extractor,
            )
        self.next_time_build = self.building.building(self.vil_settings)

    def gather(self):
        if not bool(self.vil_settings["gather"]):
            self.next_time_gather = "Gathering is set to false"
            return
        if not self.gathering:
            self.gathering = Gather(
                v_id=self.v_id,
                driver=self.driver,
                config=self.config,
                extractor=self.extractor,
                game_data=self.game_data,
            )
        self.next_time_gather = self.gathering.gathering(self.vil_settings)

    def farm(self):
        if not bool(self.vil_settings["farm"]):
            self.next_time_farm = "Farming is set to false"
            return
        self.map.get_map()
        self.update_units()
        if not self.farming:
            self.farming = AttackManager(
                v_id=self.v_id,
                driver=self.driver,
                config=self.config,
                extractor=self.extractor,
                game_data=self.game_data,
                map=self.map,
                mongo=self.mongo,
                units=self.units
            )
        self.farming.farming(self.vil_settings, self.acc_settings)

    def recruit(self):
        if not bool(self.vil_settings["recruit"]):
            self.next_time_recruit = "Recruiting is set to false"
            return
        if not self.recruiting:
            self.recruiting = Recruit(
                v_id=self.v_id,
                driver=self.driver,
                config=self.config,
                extractor=self.extractor,
            )
        self.next_time_recruit = self.recruiting.recruiting()

    def secure_units(self):
        if self.clear_village:
            for impact in self.clear_village:
                now = datetime.now()
                if impact < now + timedelta(minutes=3):
                    while impact < now + timedelta(minutes=1):
                        timediff = impact - (now + timedelta(minutes=1))
                        print(timediff)
                        time.sleep(3)
                        now = datetime.now()
                    self.update_units()
                    # fragile units:
                    axe = int(self.units["axe"])
                    lkav = int(self.units["light"])
                    spy = int(self.units["spy"])
                    marcher = int(self.units["marcher"])
                    snob = int(self.units["snob"])
                    ram = int(self.units["ram"])
                    cata = int(self.units["catapult"])
                    any_vil = self.mongo.get_one_village()
                    self.driver.navigate_attack(self.world, self.v_id, any_vil["id"])
                    self.driver.attack(axe=axe,
                                       lkav=lkav,
                                       spy=spy,
                                       marcher=marcher,
                                       snob=snob,
                                       ram=ram,
                                       cata=cata,
                                       attack=False
                                       )
                    now = datetime.now()
                    while impact < now:
                        time.sleep(3)
                        now = datetime.now()
                    self.driver.cancel_safeattack(any_vil["id"])

    def response_player(self):
        attack_list = self.mongo.get_all_player()
        if attack_list:
            for attack in attack_list:
                if self.v_id != attack["defender_id"]:
                    if self.v_id not in attack["response"]:
                        if attack["slowest unit"] == "Späh":
                            self.support_player(
                                attack["defender_id"],
                                attack["slowest unit"],
                                attack["location"],
                                attack["impact"],
                            )
                            self.mongo.response_attack(attack["command_id"], self.v_id, attack["response"])

                        # Don't support != "Späh" at the moment

    def support_player(self, player_id, slowest_unit, location, impact):
        ext_location = [
            int(location[0]),
            int(location[1]),
        ]
        distance = self.map.get_dist(self.location, ext_location)
        if slowest_unit == "Späh":
            run_time = datetime.now() + (distance * timedelta(minutes=9))
            if run_time < impact:
                self.update_units()
                if int(self.units["spy"]) > 5:
                    print(self.units["spy"])
                    spy = round(int(self.units["spy"]) / 2)
                    self.driver.navigate_attack(self.world, self.v_id, player_id)
                    print(f"Sending {spy} spy from {self.v_id} to {player_id} ")
                    self.driver.attack(spy=spy, attack=False)
        if slowest_unit != "Späh":
            self.update_units()
            spear, sword, archer, heavy, knight = 0, 0, 0, 0, 0
            if int(self.units["spear"]) >= 10:
                spear = round(int(self.units["spear"]) / 4)
            if int(self.units["sword"]) >= 10:
                sword = round(int(self.units["sword"]) / 4)
            if int(self.units["archer"]) >= 10:
                archer = round(int(self.units["archer"]) / 4)
            if int(self.units["heavy"]) >= 10:
                heavy = round(int(self.units["heavy"]) / 4)
            if int(self.units["knight"]) > 0:
                knight = 1
            running = 100
            if heavy > 0:
                running = 11
            if archer > 0:
                running = 18
            if spear > 0:
                running = 18
            if sword > 0:
                running = 22
            if knight > 0:
                running = 10
            run_time = datetime.now() + (distance * timedelta(minutes=running))
            if run_time < impact:
                self.driver.navigate_attack(self.world, self.v_id, player_id)
                print(f"Sending: \n"
                      f"{spear} spear \n"
                      f"{sword} sword \n"
                      f"{archer} archer \n"
                      f"{heavy} heavy \n"
                      f"{knight} knight\n"
                      f" from {self.v_id} to {player_id} ")
                self.driver.attack(spear=spear, sword=sword, archer=archer, heavy=heavy, knight=knight, attack=False)

    def update_units(self):
        self.driver.navigate_overview(self.world, self.v_id)
        time.sleep(3)
        source = self.driver.get_source()
        # Own units
        for u in self.extractor.own_units(source):
            k, v = u
            self.units[k] = v
        if not "spear" in self.units:
            self.units.update({"spear": 0})
        if not "sword" in self.units:
            self.units.update({"sword": 0})
        if not "axe" in self.units:
            self.units.update({"axe": 0})
        if not "spy" in self.units:
            self.units.update({"spy": 0})
        if not "light" in self.units:
            self.units.update({"light": 0})
        if not "heavy" in self.units:
            self.units.update({"heavy": 0})
        if not "marcher" in self.units:
            self.units.update({"marcher": 0})
        if not "ram" in self.units:
            self.units.update({"ram": 0})
        if not "catapult" in self.units:
            self.units.update({"catapult": 0})
        if not "snob" in self.units:
            self.units.update({"snob": 0})
        if not "knight" in self.units:
            self.units.update({"knight": 0})
        # Total units in village ( Own + support )
        for u in self.extractor.units_in_village(source):
            k, v = u
            self.total_units[k] = v

        if not "spear" in self.total_units:
            self.total_units.update({"spear": 0})
        if not "sword" in self.total_units:
            self.total_units.update({"sword": 0})
        if not "axe" in self.total_units:
            self.total_units.update({"axe": 0})
        if not "spy" in self.total_units:
            self.total_units.update({"spy": 0})
        if not "light" in self.total_units:
            self.total_units.update({"light": 0})
        if not "heavy" in self.total_units:
            self.total_units.update({"heavy": 0})
        if not "marcher" in self.total_units:
            self.total_units.update({"marcher": 0})
        if not "ram" in self.total_units:
            self.total_units.update({"ram": 0})
        if not "catapult" in self.total_units:
            self.total_units.update({"catapult": 0})
        if not "snob" in self.total_units:
            self.total_units.update({"snob": 0})
        if not "knight" in self.total_units:
            self.total_units.update({"knight": 0})

    @staticmethod
    def find_between(s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""
