import time
from datetime import datetime
from datetime import timedelta
from datetime import date


class AttackManager:
    vil_settings = None
    acc_settings = None
    logs = {}

    v_id = None
    player = None
    world = None
    driver = None
    config = None
    extractor = None
    mongo = None
    map = None
    units = None
    next_time_farm = None
    custom_farmlist = False

    game_data = None
    targets = {}
    ignored = []
    village_id = None
    my_location = []
    farm_radius = 20
    total_spear = None
    total_sword = None
    total_axe = None
    total_archer = None
    total_spy = None
    total_light = None
    total_marcher = None
    total_heavy = None
    total_ram = None
    total_cata = None
    total_knight = None
    list_villages = []

    def __init__(self, v_id=None, driver=None, config=None, extractor=None, game_data=None, map=None, mongo=None,
                 units=None):
        self.v_id = v_id
        self.driver = driver
        self.config = config
        self.extractor = extractor
        self.game_data = game_data
        self.map = map
        self.mongo = mongo
        self.units = units

    def farming(self, vil_settings, acc_settings):
        self.vil_settings = vil_settings
        self.acc_settings = acc_settings
        self.logs = self.config.get_cache("Logs", date.today())
        self.player = self.config.read_config("game", "account", "username")

        self.world = self.config.read_config("game", "account", "world")
        if not self.my_location:
            self.my_location = [
                self.game_data["village"]["x"],
                self.game_data["village"]["y"],
            ]
        self.farm_assist()

    def farm_assist(self):

        get_h = time.localtime().tm_hour
        if get_h in range(0, 7):
            night = int(self.acc_settings["night"])
            print(f"[Night Mode] active --> Sending x{night} times farm units")
        else:
            night = 1
            print(f"[Day Mode] active --> Sending normal values")

        tmp_dict_a = {}
        for x, y in self.acc_settings["FA_template_A"].items():
            tmp_dict_a.update({x: (y * night)})
        self.acc_settings.update({"FA_template_A": tmp_dict_a})
        tmp_dict_b = {}
        for x, y in self.acc_settings["FA_template_B"].items():
            tmp_dict_b.update({x: (y * night)})
        self.acc_settings.update({"FA_template_B": tmp_dict_b})

        time_between_farm = int(self.acc_settings["timeout_farm"])
        time_between_scout = int(self.acc_settings["timeout_scout"])
        time_between_ram = int(self.acc_settings["timeout_ram"])

        self.driver.navigate_farmassist(self.v_id, self.world)

        farm_units = self.driver.get_units_farmassist()
        self.total_spear = int(farm_units["spear"])
        self.total_sword = int(farm_units["sword"])
        self.total_axe = int(farm_units["axe"])
        if "archer" in self.game_data["units"]:
            self.total_archer = int(farm_units["archer"])
        else:
            self.total_archer = 0
        self.total_spy = int(farm_units["spear"])
        self.total_light = int(farm_units["light"])
        if "marcher" in self.game_data["units"]:
            self.total_marcher = int(farm_units["marcher"])
        else:
            self.total_marcher = 0
        self.total_heavy = int(farm_units["heavy"])
        self.total_ram = int(self.units["ram"])
        self.total_cata = int(self.units["catapult"])


        # value_a, value_b = self.get_FA_IDs(source)
        value_a = self.config.read_config("game", "account", "value_a")
        value_b = self.config.read_config("game", "account", "value_b")

        self.driver.set_farmassist_checks()

        time.sleep(1)
        text_table = self.driver.get_innerText_by_ID("plunder_list")

        # self.get_targets()

        self.list_villages = self.vil_settings["farmlist"]
        if not self.list_villages:
            print("Custom farm list is empty, farming FarmAssist list")
            self.list_villages = self.extractor.get_vils_from_fa(text_table)
            self.custom_farmlist = False
        else:
            self.custom_farmlist = True

        targets_count = len(self.list_villages)
        print(f"{targets_count} Targets")
        if targets_count == 0:
            return

        if farm_units:
            # Crushing Wall
            start_time = time.time()
            if self.vil_settings["crush_wall"]:
                if self.total_ram >= 5 and self.total_axe >= 10 and self.total_spy >= 1:
                    for tar in self.list_villages:
                        coords = tar.split("|")
                        target_entry = self.mongo.find_by_coords(coords[0], coords[1])
                        if target_entry:
                            location_text = f'{coords[0]}|{coords[1]}'
                            if location_text in text_table:
                                distance = self.map.get_dist(self.my_location, target_entry["location"])
                                last_scout = target_entry["last scout"]
                                if target_entry["safe"]:
                                    now = datetime.now()
                                    if "wall" in target_entry["buildings"].keys():
                                        wall = int(target_entry["buildings"]["wall"])
                                        if wall > 0:
                                            last_ram = target_entry["last ram"]
                                            if last_ram < datetime.timestamp(now - timedelta(minutes=time_between_ram)):
                                                if last_scout < datetime.timestamp(
                                                        now - timedelta(minutes=time_between_scout)):
                                                    print(
                                                        f"Village [{target_entry['id']}] ({location_text}) Distance: [{round(distance, 2)}] --> Scouting again before crushing wall")
                                                    continue
                                                impact = datetime.timestamp(now + timedelta(minutes=30 * distance))
                                                ram_count = 5
                                                axe_count = 10
                                                spy_count = 1
                                                if wall == 1:
                                                    ram_count = 10
                                                    axe_count = 20
                                                    spy_count = 1
                                                if wall == 2:
                                                    ram_count = 15
                                                    axe_count = 25
                                                    spy_count = 1
                                                if wall == 3:
                                                    ram_count = 20
                                                    axe_count = 30
                                                    spy_count = 1
                                                if wall > 3:
                                                    ram_count = 30
                                                    axe_count = 50
                                                    spy_count = 1
                                                if self.total_ram >= ram_count and self.total_axe >= axe_count and self.total_spy >= spy_count:
                                                    print(
                                                        f"Crushing wall of village [{target_entry['id']}] Distance: [{round(distance, 2)}] sending {ram_count} rams and {axe_count} axe")
                                                    self.driver.navigate_attack(self.world, self.v_id,
                                                                                target_entry['id'])
                                                    self.logs[self.player]['count_ram_attacks'] += 1
                                                    self.logs[str(self.v_id)]['count_ram_attacks'] += 1
                                                    if not self.driver.attack(ram=ram_count,
                                                                              axe=axe_count,
                                                                              spy=spy_count,
                                                                              attack=True,
                                                                              ):
                                                        self.driver.navigate_farmassist(self.v_id, self.world)
                                                        farm_units = self.driver.get_units_farmassist()
                                                        self.total_spy = int(farm_units["spear"])
                                                        self.total_light = int(farm_units["light"])
                                                        self.total_axe = int(farm_units["axe"])
                                                        self.total_spear = int(farm_units["spear"])
                                                        self.total_spy = int(farm_units["spy"])
                                                        self.mongo.upload_ram_attack_villages(
                                                            target_entry["id"], impact)
                                                        break
                                                    self.total_ram -= ram_count
                                                    self.total_axe -= axe_count
                                                    self.total_spy -= spy_count
                                                    self.mongo.upload_ram_attack_villages(target_entry["id"],
                                                                                          impact)
            self.logs[str(self.v_id)]['time_ram_attacks'] += time.time() - start_time
            # Crushing Buildings
            start_time = time.time()
            if self.vil_settings["crush_building"]:
                if self.total_cata >= 25 and self.total_ram >= 5 and self.total_axe >= 15 and self.total_spy >= 1:
                    for tar in self.list_villages:
                        coords = tar.split("|")
                        target_entry = self.mongo.find_by_coords(coords[0], coords[1])
                        if target_entry:
                            location_text = f'{coords[0]}|{coords[1]}'
                            if location_text in text_table:
                                distance = self.map.get_dist(self.my_location, target_entry["location"])
                                last_scout = target_entry["last scout"]
                                if target_entry["safe"]:
                                    now = datetime.now()
                                    if int(target_entry["points"]) > 1800:
                                        if "main" in target_entry["buildings"].keys():
                                            main = int(target_entry["buildings"]["main"])
                                            if main >= 1:
                                                last_ram = target_entry["last ram"]
                                                if last_ram < datetime.timestamp(
                                                        now - timedelta(minutes=time_between_ram)):
                                                    if last_scout < datetime.timestamp(
                                                            now - timedelta(minutes=time_between_scout)):
                                                        print(
                                                            f"Village [{target_entry['id']}] ({location_text}) Distance: [{round(distance, 2)}] --> Scouting again before crushing building")
                                                        continue
                                                    impact = datetime.timestamp(
                                                        now + timedelta(minutes=30 * distance))
                                                    ram_count = 5
                                                    axe_count = 15
                                                    spy_count = 1
                                                    cata_count = 25
                                                    if self.total_ram >= ram_count and self.total_cata >= cata_count and self.total_axe >= axe_count and self.total_spy >= spy_count:
                                                        print(
                                                            f"Crushing main of village [{target_entry['id']}] Distance: [{round(distance, 2)}] sending {ram_count} rams {cata_count} cata and {axe_count} axe")
                                                        self.driver.navigate_attack(self.world, self.v_id,
                                                                                    target_entry['id'])
                                                        self.logs[self.player]['count_cata_attacks'] += 1
                                                        self.logs[str(self.v_id)]['count_cata_attacks'] += 1
                                                        if not self.driver.attack(ram=ram_count,
                                                                                  cata=cata_count,
                                                                                  axe=axe_count,
                                                                                  spy=spy_count,
                                                                                  attack=True,
                                                                                  ):
                                                            self.driver.navigate_farmassist(self.v_id, self.world)
                                                            farm_units = self.driver.get_units_farmassist()
                                                            self.total_spy = int(farm_units["spear"])
                                                            self.total_light = int(farm_units["light"])
                                                            self.total_axe = int(farm_units["axe"])
                                                            self.total_spear = int(farm_units["spear"])
                                                            self.total_spy = int(farm_units["spy"])
                                                            self.mongo.upload_ram_attack_villages(
                                                                target_entry["id"], impact)
                                                            break
                                                        self.total_ram -= ram_count
                                                        self.total_cata -= cata_count
                                                        self.total_axe -= axe_count
                                                        self.total_spy -= spy_count
                                                        self.mongo.upload_ram_attack_villages(target_entry["id"],
                                                                                              impact)
            current_url = self.driver.get_url()
            if not "am_farm" in current_url:
                self.driver.navigate_farmassist(self.v_id, self.world)
            self.logs[str(self.v_id)]['time_cata_attacks'] += time.time() - start_time
            # Scouting
            start_time = time.time()
            pages = self.driver.get_FA_pages()
            i = 0
            while i < pages or i == 2:
                text_table = self.driver.get_innerText_by_ID("plunder_list")
                if self.total_spy < 1:
                    break
                if self.total_spy > 0:
                    for tar in self.list_villages:
                        coords = tar.split("|")
                        target_entry = self.mongo.find_by_coords(coords[0], coords[1])
                        if target_entry:
                            location_text = f'{coords[0]}|{coords[1]}'
                            if location_text in text_table:
                                distance = self.map.get_dist(self.my_location, target_entry["location"])
                                last_scout = target_entry["last scout"]
                                if target_entry["safe"]:
                                    now = datetime.now()
                                    impact = datetime.timestamp(now + timedelta(minutes=9 * distance))
                                    time_diff = impact - last_scout
                                    if time_diff > (time_between_scout * 60):
                                        print(
                                            f"Village [{target_entry['id']}] ({location_text}) Distance: [{round(distance, 2)}] --> Scouting ( 1 spy )")
                                        self.driver.navigate_attack(self.world, self.v_id,
                                                                    target_entry['id'])
                                        self.logs[self.player]['count_scout_attacks'] += 1
                                        self.logs[str(self.v_id)]['count_scout_attacks'] += 1
                                        if not self.driver.attack(spy=1, attack=True):
                                            self.driver.navigate_farmassist(self.v_id, self.world)
                                            farm_units = self.driver.get_units_farmassist()
                                            self.total_spy = int(farm_units["spear"])
                                            self.mongo.upload_spy_attack_villages(target_entry["id"], impact)
                                            break
                                        self.total_spy -= 1
                                        self.mongo.upload_spy_attack_villages(target_entry["id"], impact)
                i += 1
                if not self.custom_farmlist:
                    break
                if i < pages:
                    url = f"https://de{self.world}.die-staemme.de/game.php?village={self.v_id}&screen=am_farm&order=distance&dir=asc&Farm_page={i}"
                    self.driver.navigate(url)
                    print("Check next page")

            self.driver.navigate_farmassist(self.v_id, self.world)
            self.logs[str(self.v_id)]['time_scout_attacks'] += time.time() - start_time
            # Attacking with A / B
            start_time = time.time()
            pages = self.driver.get_FA_pages()
            i = 0
            while i < pages or i == 2:
                text_table = self.driver.get_innerText_by_ID("plunder_list")
                self.driver.set_farmassist_farm(value_a, value_b, self.acc_settings)
                for tar in self.list_villages:
                    coords = tar.split("|")
                    target_entry = self.mongo.find_by_coords(coords[0], coords[1])
                    if target_entry:
                        location_text = f'{coords[0]}|{coords[1]}'
                        if location_text in text_table:
                            distance = self.map.get_dist(self.my_location, target_entry["location"])
                            last_scout = target_entry["last scout"]
                            if target_entry["safe"]:
                                if "wall" in target_entry["buildings"].keys():
                                    wall = int(target_entry["buildings"]["wall"])
                                    if wall > 1:
                                        print(
                                            f"Village [{target_entry['id']}] ({location_text}) Distance: [{round(distance, 2)}] --> Not attacking because wall lvl {wall}")
                                        continue
                                now = datetime.now()
                                if last_scout < datetime.timestamp(
                                        now - timedelta(minutes=time_between_scout * night)):
                                    print(
                                        f"Village [{target_entry['id']}] ({location_text}) Distance: [{round(distance, 2)}] --> Scouting again before attacking")
                                    continue
                                # Farming A
                                slowest_unit = 22
                                if self.acc_settings["FA_template_A"]["light"] > 0:
                                    slowest_unit = 10
                                if self.acc_settings["FA_template_A"]["heavy"] > 0:
                                    slowest_unit = 11
                                if self.acc_settings["FA_template_A"]["spear"] > 0 or \
                                        self.acc_settings["FA_template_A"]["axe"] > 0:
                                    slowest_unit = 18
                                if self.acc_settings["FA_template_A"]["sword"] > 0:
                                    slowest_unit = 22
                                impact = datetime.timestamp(now + timedelta(minutes=slowest_unit * distance))
                                if target_entry["last attack"]:
                                    passed = 0
                                    for attack in target_entry["last attack"]:
                                        diff = abs(impact - attack)
                                        if diff > (time_between_farm * 60 * night):
                                            passed += 1
                                    if passed == len(target_entry["last attack"]):
                                        if int(self.acc_settings["FA_template_A"]["spear"]) > 0:
                                            if self.total_spear < (self.acc_settings["FA_template_B"]["spear"] + int(
                                                    self.vil_settings["hold_back_gather"]["spear"])):
                                                print("Not enough units ; break")
                                                break
                                        if int(self.acc_settings["FA_template_A"]["sword"]) > 0:
                                            if self.total_sword < (self.acc_settings["FA_template_B"]["sword"] + int(
                                                    self.vil_settings["hold_back_gather"]["sword"])):
                                                print("Not enough units ; break")
                                                break
                                        if int(self.acc_settings["FA_template_A"]["axe"]) > 0:
                                            if self.total_axe < (self.acc_settings["FA_template_B"]["axe"] + int(
                                                    self.vil_settings["hold_back_gather"]["axe"])):
                                                print("Not enough units ; break")
                                                break
                                        if int(self.acc_settings["FA_template_A"]["archer"]) > 0:
                                            if self.total_archer < (self.acc_settings["FA_template_B"]["archer"] + int(
                                                    self.vil_settings["hold_back_gather"]["archer"])):
                                                print("Not enough units ; break")
                                                break
                                        '''if int(self.acc_settings["FA_template_A"]["spy"]) > 0:
                                            if self.total_spy < (self.acc_settings["FA_template_B"]["spy"] + int(self.vil_settings["hold_back_gather"]["spy"])):
                                                print("Not enough units ; break")
                                                break'''
                                        if int(self.acc_settings["FA_template_A"]["light"]) > 0:
                                            if self.total_light < (self.acc_settings["FA_template_B"]["light"] + int(
                                                    self.vil_settings["hold_back_gather"]["light"])):
                                                print("Not enough units ; break")
                                                break
                                        if int(self.acc_settings["FA_template_A"]["marcher"]) > 0:
                                            if self.total_marcher < (
                                                    self.acc_settings["FA_template_B"]["marcher"] + int(
                                                    self.vil_settings["hold_back_gather"]["marcher"])):
                                                print("Not enough units ; break")
                                                break
                                        if int(self.acc_settings["FA_template_A"]["heavy"]) > 0:
                                            if self.total_heavy < (self.acc_settings["FA_template_B"]["heavy"] + int(
                                                    self.vil_settings["hold_back_gather"]["heavy"])):
                                                print("Not enough units ; break")
                                                break

                                        print(
                                            f"Village [{target_entry['id']}] ({location_text}) Distance: [{round(distance, 2)}] --> Attacking [A]")

                                        self.logs[str(self.v_id)]['count_farm_attacks'] += 1
                                        self.logs[self.player]['count_farm_attacks'] += 1
                                        self.driver.hit_template(target_entry["id"], "a")
                                        self.total_spear -= self.acc_settings["FA_template_A"]["spear"]
                                        self.total_sword -= self.acc_settings["FA_template_A"]["sword"]
                                        self.total_axe -= self.acc_settings["FA_template_A"]["axe"]
                                        self.total_archer -= self.acc_settings["FA_template_A"]["archer"]
                                        self.total_spy -= self.acc_settings["FA_template_A"]["spy"]
                                        self.total_light -= self.acc_settings["FA_template_A"]["light"]
                                        self.total_marcher -= self.acc_settings["FA_template_A"]["marcher"]
                                        self.total_heavy -= self.acc_settings["FA_template_A"]["heavy"]
                                        time.sleep(0.25)
                                        self.mongo.upload_farm_attack_villages(target_entry["id"], impact)

                                    else:
                                        print(
                                            f"Village [{target_entry['id']}] ({location_text}) Distance: [{round(distance, 2)}] --> Not attacking because timing between attacks")
                                # --------------------
                # Refresh
                self.driver.refresh()
                for tar in self.list_villages:
                    coords = tar.split("|")
                    target_entry = self.mongo.find_by_coords(coords[0], coords[1])
                    if target_entry:
                        location_text = f'{coords[0]}|{coords[1]}'
                        if location_text in text_table:
                            distance = self.map.get_dist(self.my_location, target_entry["location"])
                            last_scout = target_entry["last scout"]
                            if target_entry["safe"]:
                                if "wall" in target_entry["buildings"].keys():
                                    wall = int(target_entry["buildings"]["wall"])
                                    if wall > 1:
                                        print(
                                            f"Village [{target_entry['id']}] ({location_text}) Distance: [{round(distance, 2)}] --> Not attacking because wall lvl {wall}")
                                        continue
                                now = datetime.now()
                                if last_scout < datetime.timestamp(
                                        now - timedelta(minutes=time_between_scout * night)):
                                    print(
                                        f"Village [{target_entry['id']}] ({location_text}) Distance: [{round(distance, 2)}] --> Scouting again before attacking")
                                    continue
                                # Farming B
                                slowest_unit = 22
                                if self.acc_settings["FA_template_B"]["light"] > 0:
                                    slowest_unit = 10
                                if self.acc_settings["FA_template_B"]["heavy"] > 0:
                                    slowest_unit = 11
                                if self.acc_settings["FA_template_B"]["spear"] > 0 or \
                                        self.acc_settings["FA_template_B"]["axe"] > 0:
                                    slowest_unit = 18
                                if self.acc_settings["FA_template_B"]["sword"] > 0:
                                    slowest_unit = 22
                                impact = datetime.timestamp(now + timedelta(minutes=slowest_unit * distance))
                                if target_entry["last attack"]:
                                    passed = 0
                                    for attack in target_entry["last attack"]:
                                        diff = abs(impact - attack)
                                        if diff > (time_between_farm * 60 * night):
                                            passed += 1
                                    if passed == len(target_entry["last attack"]):
                                        if int(self.acc_settings["FA_template_B"]["spear"]) > 0:
                                            if self.total_spear < (self.acc_settings["FA_template_B"]["spear"] + int(
                                                    self.vil_settings["hold_back_gather"]["spear"])):
                                                print("Not enough units ; break")
                                                break
                                        if int(self.acc_settings["FA_template_B"]["sword"]) > 0:
                                            if self.total_sword < (self.acc_settings["FA_template_B"]["sword"] + int(
                                                    self.vil_settings["hold_back_gather"]["sword"])):
                                                print("Not enough units ; break")
                                                break
                                        if int(self.acc_settings["FA_template_B"]["axe"]) > 0:
                                            if self.total_axe < (self.acc_settings["FA_template_B"]["axe"] + int(
                                                    self.vil_settings["hold_back_gather"]["axe"])):
                                                print("Not enough units ; break")
                                                break
                                        if int(self.acc_settings["FA_template_B"]["archer"]) > 0:
                                            if self.total_archer < (self.acc_settings["FA_template_B"]["archer"] + int(
                                                    self.vil_settings["hold_back_gather"]["archer"])):
                                                print("Not enough units ; break")
                                                break
                                        '''if int(self.acc_settings["FA_template_B"]["spy"]) > 0:
                                            if self.total_spy < (self.acc_settings["FA_template_B"]["spy"] + int(self.vil_settings["hold_back_gather"]["spy"])):
                                                print("Not enough units ; break")
                                                break'''
                                        if int(self.acc_settings["FA_template_B"]["light"]) > 0:
                                            if self.total_light < (self.acc_settings["FA_template_B"]["light"] + int(
                                                    self.vil_settings["hold_back_gather"]["light"])):
                                                print("Not enough units ; break")
                                                break
                                        if int(self.acc_settings["FA_template_B"]["marcher"]) > 0:
                                            if self.total_marcher < (
                                                    self.acc_settings["FA_template_B"]["marcher"] + int(
                                                    self.vil_settings["hold_back_gather"]["marcher"])):
                                                print("Not enough units ; break")
                                                break
                                        if int(self.acc_settings["FA_template_B"]["heavy"]) > 0:
                                            if self.total_heavy < (self.acc_settings["FA_template_B"]["heavy"] + int(
                                                    self.vil_settings["hold_back_gather"]["heavy"])):
                                                print("Not enough units ; break")
                                                break

                                        print(
                                            f"Village [{target_entry['id']}] ({location_text}) Distance: [{round(distance, 2)}] --> Attacking [B]")
                                        self.logs[str(self.v_id)]['count_farm_attacks'] += 1
                                        self.logs[self.player]['count_farm_attacks'] += 1
                                        self.driver.hit_template(target_entry["id"], "b")
                                        self.total_spear -= self.acc_settings["FA_template_B"]["spear"]
                                        self.total_sword -= self.acc_settings["FA_template_B"]["sword"]
                                        self.total_axe -= self.acc_settings["FA_template_B"]["axe"]
                                        self.total_archer -= self.acc_settings["FA_template_B"]["archer"]
                                        self.total_spy -= self.acc_settings["FA_template_B"]["spy"]
                                        self.total_light -= self.acc_settings["FA_template_B"]["light"]
                                        self.total_marcher -= self.acc_settings["FA_template_B"]["marcher"]
                                        self.total_heavy -= self.acc_settings["FA_template_B"]["heavy"]
                                        time.sleep(0.25)
                                        self.mongo.upload_farm_attack_villages(target_entry["id"], impact)

                                    else:
                                        print(
                                            f"Village [{target_entry['id']}] ({location_text}) Distance: [{round(distance, 2)}] --> Not attacking because timing between attacks")
                                # --------------------
                i += 1
                if not self.custom_farmlist:
                    break
                if i < pages:
                    url = f"https://de{self.world}.die-staemme.de/game.php?village={self.v_id}&screen=am_farm&order=distance&dir=asc&Farm_page={i}"
                    self.driver.navigate(url)
                    print("Check next page")

            self.logs[str(self.v_id)]['time_scout_attacks'] += time.time() - start_time
            # Extra Attacks
            if self.total_light >= 150:
                for tar in self.list_villages:
                    coords = tar.split("|")
                    target_entry = self.mongo.find_by_coords(coords[0], coords[1])
                    if target_entry:
                        location_text = f'{coords[0]}|{coords[1]}'
                        if location_text in text_table:
                            distance = self.map.get_dist(self.my_location, target_entry["location"])
                            last_scout = target_entry["last scout"]
                            # if not target_entry["last extra"]:
                            #    continue
                            last_extra = target_entry["last extra"]
                            if target_entry["safe"]:
                                if "wood" in target_entry["resources"].keys() and \
                                        "stone" in target_entry["resources"].keys() and \
                                        "iron" in target_entry["resources"].keys():
                                    wood = int(target_entry["resources"]["wood"])
                                    stone = int(target_entry["resources"]["stone"])
                                    iron = int(target_entry["resources"]["iron"])
                                    res_all = wood + stone + iron
                                    if res_all > 15000:
                                        if distance < 10:
                                            now = datetime.now()
                                            diff_time = datetime.timestamp(now) - last_scout
                                            if diff_time < 3600:  # 60 minutes
                                                diff_time = datetime.timestamp(now) - last_extra
                                                if diff_time < 3600:  # 60 minutes
                                                    light_count = round(res_all / 80 * 0.8)

                                                    impact = datetime.timestamp(
                                                        now + timedelta(minutes=10 * distance))
                                                    if self.total_light >= light_count:
                                                        print(
                                                            f"Village [{target_entry['id']}] ({location_text}) Distance: [{round(distance, 2)}] --> EXTRA ATTACK because \n"
                                                            f"      [{wood} wood] [{stone} stone] [{iron} iron]")
                                                        self.driver.navigate_attack(self.world, self.v_id,
                                                                                    target_entry['id'])
                                                        if not self.driver.attack(light=light_count,
                                                                                  attack=True,
                                                                                  ):
                                                            self.driver.navigate_farmassist(self.v_id, self.world)
                                                            farm_units = self.driver.get_units_farmassist()
                                                            self.total_spy = int(farm_units["spear"])
                                                            self.total_light = int(farm_units["light"])
                                                            self.total_spy = int(farm_units["spy"])
                                                            self.mongo.upload_ram_attack_villages(
                                                                target_entry["id"], impact)
                                                            break
                                                        self.total_light -= light_count
                                                        self.mongo.upload_extra_attack_villages(target_entry["id"],
                                                                                                impact)

        self.config.set_cache("Logs", date.today(), self.logs)

    def should_farm(self):
        if not self.next_time_farm:
            return True
        if self.next_time_farm < datetime.now():
            return True

    def get_targets(self):
        output = []
        for vid in self.map.villages:
            village = self.map.villages[vid]
            if village["owner"] != "0":
                if vid not in self.ignored:
                    self.ignored.append(vid)
                continue
            if village["owner"] != "0":
                get_h = time.localtime().tm_hour
                if get_h in range(0, 8) or get_h == 23:
                    continue
            distance = self.map.get_dist(self.map.my_location, village["location"])
            if distance > self.farm_radius:
                if vid not in self.ignored:
                    self.ignored.append(vid)
                continue
            if vid in self.ignored:
                print("Village: %s removed from Ignore-list" % vid)
                self.ignored.remove(vid)

            output.append([village, distance])
        # print(f"Targets: {len(output)}")
        # print(f"Ignored targets: {len(self.ignored)}")
        self.targets = sorted(output, key=lambda x: x[1])
