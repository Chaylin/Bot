import random
import threading
from Game.driver import Driver
from Game.mongo import Mongo
from Game.extractor import Extractor
from Game.village import Village
from Game.config import ConfigStuff
from Game.gather import Gather
import Game.discord

import time
from datetime import datetime
from datetime import timedelta


thread = threading.Thread(target=Game.discord.run)
thread.start()


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
    gathering = None
    start_time_gather = None
    defence = None
    attack_count = 0
    message = None
    reporter = None


    def start(self):
        self.login()
        self.get_villages()
        self.infinity_loop()

    def infinity_loop(self):

        try:
            self.cycle()

        except Exception:
            raise
            '''self.driver.check_captcha()
            self.driver.actions = 0
            self.apm = 0
            now = datetime.now()
            self.start_sec = datetime.timestamp(now)
            self.restart = True

        finally:
            self.restart = True
            self.infinity_loop()'''

    def cycle(self):
        if not self.start_sec:
            now = datetime.now()
            self.start_sec = datetime.timestamp(now)
        while True:
            start_time = time.time()
            for vil in self.villages:
                if self.current_vil and self.restart:
                    if not self.current_vil == vil.game_data['village']['id']:
                        continue

                self.attackManager()
                vil.get_started()
                print(f"********************************************************\n"
                      f"VILLAGE: [{vil.game_data['village']['name']}]        ID:[{vil.game_data['village']['id']}] \n"
                      f"********************************************************")
                self.driver.check_captcha()
                self.current_vil = vil.game_data['village']['id']
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
                        time.sleep(pausing_random)

                # ######################

                if vil.acc_settings["build"]:
                    vil.build()


                if vil.acc_settings["gather"]:
                    if int(vil.game_data["player"]["villages"]) > 50:
                        if not self.gathering:
                            self.gathering = Gather(
                                v_id=vil.game_data['village']['id'],
                                driver=self.driver,
                                config=self.config,
                                extractor=self.extractor,
                                game_data=vil.game_data,
                            )
                        if not self.start_time_gather:
                            self.start_time_gather = datetime.timestamp(datetime.now())
                            self.gathering.mass_gathering()


                        if int((datetime.timestamp(datetime.now()) - self.start_time_gather)) > 3600:
                            self.start_time_gather = datetime.timestamp(datetime.now())
                            self.gathering.mass_gathering()
                        else:
                            time_remaining = 3600 - int((datetime.timestamp(datetime.now()) - self.start_time_gather))
                            print(f'Next Mass Scavenge in {round(time_remaining / 60)} minutes')
                    else:
                        pass
                        vil.gather()

                if vil.acc_settings["farm"]:
                    vil.farm()
                if vil.acc_settings["recruit"]:
                    vil.recruit()

            stop_time = time.time()
            time_cycle = stop_time - start_time


            if time_cycle < 300:
                time.sleep(300)



    def login(self):
        if not self.config:
            self.config = ConfigStuff()
        if not self.driver:
            self.driver = Driver()
        if not self.extractor:
            self.extractor = Extractor()
        if not self.mongo:
            self.mongo = Mongo()

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
        print(f'{len(village_ids)} villages found!')

    def attackManager(self):

        pass


b = Bot()
b.start()
