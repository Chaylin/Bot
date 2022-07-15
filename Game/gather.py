from datetime import datetime


class Gather:
    vil_settings = None

    v_id = None
    world = None
    driver = None
    config = None
    extractor = None
    game_data = None

    units = {}
    next_time_gather = None

    def __init__(self, v_id=None, driver=None, config=None, extractor=None, game_data=None):
        self.v_id = v_id
        self.driver = driver
        self.config = config
        self.extractor = extractor
        self.game_data = game_data

    def gathering(self, settings):
        self.vil_settings = settings

        self.world = self.config.read_config("game", "account", "world")
        if not self.should_gather():
            return self.next_time_gather

        self.driver.navigate_scavenge(self.world, self.v_id)
        source = self.driver.get_source()
        village_data = self.extractor.village_data(source)
        self.units.update(village_data["unit_counts_home"])
        troops = 0
        if self.vil_settings["gather_units"]["spear"]:
            troops += int(self.units["spear"])
        if self.vil_settings["gather_units"]["sword"]:
            troops += int(self.units["sword"])
        if self.vil_settings["gather_units"]["axe"]:
            troops += int(self.units["axe"])
        if "archer" in self.game_data["units"]:
            if self.vil_settings["gather_units"]["archer"]:
                troops += int(self.units["archer"])
        if self.vil_settings["gather_units"]["light"]:
            troops += int(self.units["light"])
        if "marcher" in self.game_data["units"]:
            if self.vil_settings["gather_units"]["marcher"]:
                troops += int(self.units["marcher"])
        if self.vil_settings["gather_units"]["heavy"]:
            troops += int(self.units["heavy"])
        if troops < 120:
            return self.next_time_gather
        if not self.can_gather(village_data):
            gather_time_remaining = self.driver.get_gather_time()
            self.next_time_gather = gather_time_remaining
            return gather_time_remaining
        gather_time_remaining = self.gather(village_data)
        return gather_time_remaining

    def should_gather(self):
        if not self.next_time_gather:
            return True
        if self.next_time_gather < datetime.now():
            return True

    def gather(self, village_data):
        r1 = None
        r2 = None
        r3 = None
        r4 = None

        if not village_data["options"]["1"]["is_locked"]:
            r1 = 1
            r2 = 0
            r3 = 0
            r4 = 0
            if not village_data["options"]["2"]["is_locked"]:
                r1 = 0.715
                r2 = 0.285
                r3 = 0
                r4 = 0
                if not village_data["options"]["3"]["is_locked"]:
                    r1 = 0.625
                    r2 = 0.25
                    r3 = 0.125
                    r4 = 0
                    if not village_data["options"]["4"]["is_locked"]:
                        r1 = 0.5767
                        r2 = 0.23
                        r3 = 0.1155
                        r4 = 0.077

        if not village_data["options"]["1"]["is_locked"]:
            if not r1 == 0:
                self.driver.send_gather(village_data, float(r1), self.vil_settings["hold_back_gather"], self.vil_settings["gather_units"], self.game_data)
        if not village_data["options"]["2"]["is_locked"]:
            if not r2 == 0:
                self.driver.send_gather(village_data, float(r2), self.vil_settings["hold_back_gather"], self.vil_settings["gather_units"], self.game_data)
        if not village_data["options"]["3"]["is_locked"]:
            if not r3 == 0:
                self.driver.send_gather(village_data, float(r3), self.vil_settings["hold_back_gather"], self.vil_settings["gather_units"], self.game_data)
        if not village_data["options"]["4"]["is_locked"]:
            if not r4 == 0:
                self.driver.send_gather(village_data, float(r4), self.vil_settings["hold_back_gather"], self.vil_settings["gather_units"], self.game_data)

        gather_time_remaining = self.driver.get_gather_time()

        return gather_time_remaining

    @staticmethod
    def can_gather(village_data):
        if village_data["options"]["1"]["scavenging_squad"] is not None:
            return False
        if village_data["options"]["2"]["scavenging_squad"] is not None:
            return False
        if village_data["options"]["3"]["scavenging_squad"] is not None:
            return False
        if village_data["options"]["4"]["scavenging_squad"] is not None:
            return False

        if village_data["options"]["1"]["is_locked"]:
            if village_data["options"]["2"]["is_locked"]:
                if village_data["options"]["3"]["is_locked"]:
                    if village_data["options"]["4"]["is_locked"]:
                        return False
        return True
