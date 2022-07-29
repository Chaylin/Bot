import random

from Game.driver import Driver
from Game.mongo import Mongo
from Game.map import Map
from Game.extractor import Extractor
from Game.village import Village
from Game.config import ConfigStuff
from Game.defence import Defence
from Game.reports import ReportManager
from Game.discord import Discord

import time
from datetime import datetime


class Bot:
    id_list = []
    world = None
    game_data = {}
    villages = []
    clear_village = {}

    acc_settings = {}
    logs = {'date': None}
    start_sec = None
    apm = 0
    current_vil = None
    restart = False

    driver = None
    config = None
    extractor = None
    mongo = None
    map = None
    defence = None
    attack_count = 0
    message = None
    reporter = None
    discord = None

    def start(self):
        self.login()
        self.get_villages()
        self.infinity_loop()

    def infinity_loop(self):

        try:
            self.cycle()

        except:

            if self.driver.check_bot_captcha():
                print("!!! Bot-Captcha active !!!")
                time.sleep(10)
                if self.driver.check_bot_captcha():
                    start_time = time.time()
                    player = self.config.read_config("game", "account", "username")
                    update = {"status": 'Alert'}
                    self.mongo.synch_player(player, update, None)
                    self.discord.send_message(f" Player[{player}] Bot-Captcha active !")
                    breakpoint()
                    self.logs[f'{player}']['time_bot-captcha'] += time.time() - start_time
                    # Reset APM values
                    self.driver.actions = 0
                    self.apm = 0
                    now = datetime.now()
                    self.start_sec = datetime.timestamp(now)
                    self.restart = True

        finally:
            player = self.config.read_config("game", "account", "username")
            update = {"status": 'Offline'}
            self.mongo.synch_player(player, update, None)
            self.restart = True
            self.infinity_loop()

    def cycle(self):
        if not self.start_sec:
            now = datetime.now()
            self.start_sec = datetime.timestamp(now)
        while True:
            player = self.config.read_config("game", "account", "username")
            self.mongo.create_daily_log(player)

            start_time = time.time()
            self.read_reports()
            elf.logs[f'{player}']['time_reports'] += time.time() - start_time

            for vil in self.villages:
                if self.current_vil and self.restart:
                    if not self.current_vil == vil.v_id:
                        continue
                print(f"********************************************************\n"
                      f"VILLAGE: [{vil.v_name}]             ID:[{vil.v_id}] \n"
                      f"********************************************************")
                self.create_log_vil(vil.v_id)

                self.current_vil = vil.v_id
                self.restart = False
                self.synch_account()
                vil_settings = self.synch_village(vil)
                vil.synch_data(vil_settings, self.acc_settings)

                # Pausing if APM to high
                now = datetime.now()
                time_running_sec = datetime.timestamp(now) - self.start_sec
                self.apm = self.driver.actions / time_running_sec * 60

                print(f"{round(self.apm)} actions per minute")

                pausing = int(self.acc_settings["sleep"])
                pausing_random = pausing + random.randint(1, 5)
                if time_running_sec > 120:
                    if self.apm > int(self.acc_settings["apm_cap"]):
                        start_time = time.time()
                        print(f"Pausing {pausing_random} seconds ... \n"
                              f"because {round(self.apm)} actions per minute, apm_cap = [{self.acc_settings['apm_cap']}]")
                        time.sleep(pausing_random)
                        self.logs[f'{player}']['time_apm_cap'] += time.time() - start_time
                # ######################

                if self.acc_settings["build"]:
                    start_time = time.time()
                    vil.build()
                    self.logs[f'{vil.v_id}']['time_build'] += time.time() - start_time
                    self.logs[f'{player}']['time_build'] += time.time() - start_time
                if self.acc_settings["gather"]:
                    start_time = time.time()
                    vil.gather()
                    self.logs[f'{vil.v_id}']['time_gather'] += time.time() - start_time
                    self.logs[f'{player}']['time_gather'] += time.time() - start_time
                if self.acc_settings["farm"]:
                    start_time = time.time()
                    vil.farm()
                    self.logs[f'{vil.v_id}']['time_farm'] += time.time() - start_time
                    self.logs[f'{player}']['time_farm'] += time.time() - start_time
                if self.acc_settings["recruit"]:
                    start_time = time.time()
                    vil.recruit()
                    self.logs[f'{vil.v_id}']['time_recruit'] += time.time() - start_time
                    self.logs[f'{player}']['time_recruit'] += time.time() - start_time

                self.mongo.synch_log(self.logs, player)

    def create_log_vil(self, v_id):  # create default in mongo and define only the keys in 'run' where  to track
        if v_id in self.logs.keys():
            return
        default_log_vil = {
            'time_vil': 0,
            'time_build': 0,
            'time_gather': 0,
            'time_farm': 0,
            'time_recruit': 0,
            'time_farm_attacks': 0,
            'time_scout_attacks': 0,
            'time_ram_attacks': 0,
            'time_cata_attacks': 0,
            'count_farm_attacks': 0,
            'count_scout_attacks': 0,
            'count_ram_attacks': 0,
            'count_cata_attacks': 0,
            'count_gather_send': 0,
            'count_buildings_build': 0,
            'count_units_recruit': 0,
        }
        self.logs.update({f'{v_id}': default_log_vil})

    def synch_account(self):
        # Synch Account Data
        data = {
            "player": self.config.read_config("game", "account", "username"),
            "status": 'Online',
            "points": int(self.game_data["player"]["points"]),
            "villages": int(self.game_data["player"]["villages"]),
            "apm": round(self.apm),
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
            "timeout_farm": template[0]["timeout_farm"],
            "timeout_scout": template[0]["timeout_scout"],
            "timeout_ram": template[0]["timeout_ram"],
            "FA_template_A": template[0]["FA_template_A"],
            "FA_template_B": template[0]["FA_template_B"],
        }
        self.acc_settings = self.mongo.synch_player(self.config.read_config("game", "account", "username"), data,
                                                    default_temp)

    def synch_village(self, vil):
        # Synch Village Data

        template_buildorder = self.config.get_list("buildorder")
        temp_id = 9999
        template = self.mongo.get_own_village(temp_id)

        default_temp = {
            "id": vil.v_id,
            "game_data": vil.game_data,
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
        result = self.mongo.synch_village(vil.v_id, default_temp)
        return result

    def read_reports(self):
        if not self.reporter:
            self.reporter = ReportManager(
                driver=self.driver, v_id=self.id_list[0], config=self.config, mongo=self.mongo,
            )
        self.reporter.read(full_run=False)

    def login(self):
        if not self.config:
            self.config = ConfigStuff()
        if not self.driver:
            self.driver = Driver(
                driver_path=self.config.read_config("game", "account", "driver_path")
            )
        if not self.extractor:
            self.extractor = Extractor()
        if not self.mongo:
            self.mongo = Mongo()
        if not self.discord:
            self.discord = Discord()

        self.driver.navigate_login()
        user, pw, self.world = self.config.read_account_data()
        self.driver.login(user, pw)
        self.driver.navigate_play(self.world)
        time.sleep(2)
        self.driver.navigate_overview_vil(self.world)

    def get_villages(self):
        self.id_list = []
        source = self.driver.get_source()
        self.game_data = self.extractor.game_state(source)
        v_count = int(self.game_data["player"]["villages"])
        if int(v_count) > 1:
            for ids in range(0, v_count):
                source = self.driver.get_source()
                self.game_data = self.extractor.game_state(source)
                v_id = self.game_data["village"]["id"]
                self.driver.switch_village()
                self.id_list.append(v_id)
                if not self.map:
                    self.map = Map(
                        v_id=v_id,
                        driver=self.driver,
                        config=self.config,
                        extractor=self.extractor,
                        mongo=self.mongo,
                        coords_x=self.game_data["village"]["x"],
                        coords_y=self.game_data["village"]["y"],
                        world=self.world,
                    )
                self.villages.append(Village(
                    v_id=v_id,
                    driver=self.driver,
                    game_data=self.game_data,
                    config=self.config,
                    extractor=self.extractor,
                    mongo=self.mongo,
                    map=self.map,
                ))
        else:
            v_id = self.game_data["village"]["id"]
            self.id_list.append(v_id)
            if not self.map:
                self.map = Map(
                    v_id=v_id,
                    driver=self.driver,
                    config=self.config,
                    extractor=self.extractor,
                    mongo=self.mongo,
                    coords_x=self.game_data["village"]["x"],
                    coords_y=self.game_data["village"]["y"],
                    world=self.world,
                )
            self.villages.append(Village(
                v_id=v_id,
                driver=self.driver,
                game_data=self.game_data,
                config=self.config,
                extractor=self.extractor,
                mongo=self.mongo,
                map=self.map
            ))

    def manage_defence(self):
        if not self.defence:
            self.defence = Defence(
                driver=self.driver,
                extractor=self.extractor,
                config=self.config,
                mongo=self.mongo,
            )
        self.clear_village, self.attack_count = self.defence.run()


b = Bot()
b.start()
