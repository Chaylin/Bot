from Game.attack import AttackManager
from Game.building import Building
from Game.gather import Gather
from Game.recruit import Recruit

from datetime import datetime
from datetime import timedelta
import time


class Village:
    player = None
    world = None
    extractor = None
    config = None
    driver = None
    mongo = None

    building = None
    gathering = None
    farming = None
    recruiting = None

    next_time_build = None
    next_time_gather = None
    next_time_farm = None
    next_time_recruit = None

    vil_settings = None
    acc_settings = None
    game_data = None

    def __init__(self,
                 v_id=None,
                 driver=None,
                 config=None,
                 extractor=None,
                 mongo=None,
                 ):
        self.v_id = v_id
        self.driver = driver
        self.config = config
        self.extractor = extractor
        self.mongo = mongo


    def get_started(self):
        self.player = self.config.read_config("game", "account", "username")
        self.world = self.config.read_config("game", "account", "world")
        self.driver.navigate_overview(self.world, self.v_id)
        source = self.driver.get_source()
        self.game_data = self.extractor.game_state(source)


        self.synch_account()
        self.vil_settings = self.synch_village(self.v_id)



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
        if not self.farming:
            self.farming = AttackManager(
                v_id=self.v_id,
                driver=self.driver,
                config=self.config,
                extractor=self.extractor,
                mongo=self.mongo,
                game_data=self.game_data,
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

    def synch_account(self):
        # Synch Account Data
        data = {
            "player": self.player,
            "status": 'Online',
            "points": int(self.game_data["player"]["points"]),
            "villages": int(self.game_data["player"]["villages"]),
            #"apm": round(self.apm),
        }
        player = "Vorlage Acc"
        template = self.mongo.get_player(player)

        default_temp = {
            "build": template[0]["build"],
            "recruit": template[0]["recruit"],
            "farm": template[0]["farm"],
            "gather": template[0]["gather"],
            "sleep": template[0]["sleep"],
            "apm_cap": template[0]["apm_cap"],
            "night": template[0]["night"],
            "timeout_farm": template[0]["timeout_farm"],
            "timeout_scout": template[0]["timeout_scout"],
            "timeout_ram": template[0]["timeout_ram"],
            "FA_template_A": template[0]["FA_template_A"],
            "FA_template_B": template[0]["FA_template_B"],
        }
        self.acc_settings = self.mongo.synch_player(self.player, data, default_temp)

    def synch_village(self, vil):
        # Synch Village Data

        template_buildorder = self.config.get_list("buildorder")
        temp_id = 9999
        template = self.mongo.get_own_village(temp_id)

        default_temp = {
            "id": self.v_id,
            "game_data": self.game_data,
            "build": template["build"],
            "recruit": template["recruit"],
            "farm": template["farm"],
            "gather": template["gather"],
            "buildorder": template_buildorder,
            "farmlist": [],
            "crush_wall": template["crush_wall"],
            "crush_building": template["crush_building"],
            "gather_units": template["gather_units"],
            "hold_back_gather": template["hold_back_gather"],
            "hold_back_farm": template["hold_back_farm"],
        }
        result = self.mongo.synch_village(self.v_id, default_temp)
        return result


    @staticmethod
    def find_between(s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""
