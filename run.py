import random

from Game.driver import Driver
from Game.mongo import Mongo
from Game.extractor import Extractor
from Game.village import Village
from Game.config import ConfigStuff
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

                    player = self.config.read_config("game", "account", "username")
                    update = {"status": 'Alert'}
                    self.mongo.synch_player(player, update, None)
                    self.discord.send_message(f" Player[{player}] Bot-Captcha active !")
                    breakpoint()

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
            for vil in self.villages:
                vil.get_started()
                if self.current_vil and self.restart:
                    if not self.current_vil == vil.game_data['village']['id']:
                        continue
                print(f"********************************************************\n"
                      f"VILLAGE: [{vil.game_data['village']['name']}]        ID:[{vil.game_data['village']['id']}] \n"
                      f"********************************************************")

                self.current_vil = vil.v_id
                self.restart = False


                # Pausing if APM to high
                now = datetime.now()
                time_running_sec = datetime.timestamp(now) - self.start_sec
                self.apm = self.driver.actions / time_running_sec * 60

                print(f"{round(self.apm)} actions per minute")

                pausing = int(vil.acc_settings["sleep"])
                pausing_random = pausing + random.randint(1, 5)
                if time_running_sec > 120:
                    if self.apm > int(vil.acc_settings["apm_cap"]):
                        print(f"Pausing {pausing_random} seconds ... \n"
                              f"because {round(self.apm)} actions per minute, apm_cap = [{vil.acc_settings['apm_cap']}]")

                # ######################

                if vil.acc_settings["build"]:
                    vil.build()
                if vil.acc_settings["gather"]:
                    vil.gather()
                if vil.acc_settings["farm"]:
                    vil.farm()
                if vil.acc_settings["recruit"]:
                    vil.recruit()


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
        self.driver.navigate_overview_troops(self.world)
        source = self.driver.get_source()
        village_ids = self.extractor.village_ids_from_overview(source)
        for ids in village_ids:
            self.villages.append(Village(
                v_id=ids,
                driver=self.driver,
                config=self.config,
                extractor=self.extractor,
                mongo=self.mongo,
            ))


b = Bot()
b.start()
