import time
import math
from datetime import datetime
from datetime import timedelta


class AttackManager:
    vil_settings = None
    acc_settings = None

    v_id = None
    player = None
    world = None
    driver = None
    config = None
    extractor = None
    mongo = None
    next_time_farm = None
    custom_farmlist = False

    game_data = None
    targets = {}
    ignored = []
    village_id = None
    my_location = []
    farm_radius = 20
    units = {}
    FA_temp_kav = False
    FA_temp_inf = False
    list_villages = []

    def __init__(self, v_id=None, driver=None, config=None, extractor=None, game_data=None, mongo=None,):
        self.v_id = v_id
        self.driver = driver
        self.config = config
        self.extractor = extractor
        self.game_data = game_data
        self.mongo = mongo

    def farming(self, vil_settings, acc_settings):
        self.vil_settings = vil_settings
        self.acc_settings = acc_settings
        self.player = self.config.read_config("game", "account", "username")
        self.world = self.config.read_config("game", "account", "world")
        if not self.my_location:
            self.my_location = [
                self.game_data["village"]["x"],
                self.game_data["village"]["y"],
            ]
        self.farm_assist()

    def farm_assist(self):
        time_between_farm = int(self.acc_settings["timeout_farm"])
        self.driver.navigate_farmassist(self.v_id, self.world)

        self.units = self.driver.get_units_farmassist(self.game_data)
        source = self.driver.get_source()
        value = self.extractor.FA_value(source)
        value_a = value[0]
        value_b = value[1]
        hold_back = {
            'spear': 500,
            'sword': 0,
            'axe': 0,
            'archer': 0,
            'spy': 0,
            'light': 0,
            'marcher': 0,
            'heavy': 100,
        }

        time.sleep(0.5)

        source = self.driver.get_source()
        self.targets = self.extractor.farmassist_table(source)

        time.sleep(1)
        if self.units['light'] >= 15 or self.units['heavy'] >= 30 + hold_back['heavy']:
            self.driver.set_farmassist_temp_kav(value_a, value_b)
            self.FA_temp_kav = True
            self.FA_temp_inf = False
            slowest_unit_a = 10
            slowest_unit_b = 11
            time.sleep(1)
            print('Farming with Kavallarie')
            for tar in self.targets:
                if self.units['light'] < 15:
                    break
                target_entry = self.mongo.get_villages(self.targets[tar]['id'])
                if target_entry:
                    now = datetime.now()
                    distance = self.get_dist(self.my_location, target_entry["location"])
                    impact = datetime.timestamp(now + timedelta(minutes=slowest_unit_a * distance))
                    if self.targets[tar]['Beute'] == 'Volle Beute' and self.targets[tar]['Sieg'] == 'Völliger Sieg':
                        self.attack(target_entry, impact, distance, 'Volle Beute', 'a')
                        self.units['light'] -= 15
                        continue
                    if self.targets[tar]['Sieg'] == 'Verluste':
                        print(f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack yellow!")
                        continue
                    if self.targets[tar]['Sieg'] == 'Lost':
                        print(f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack red!")
                        continue
                    if target_entry["last attack"]:
                        passed = 0
                        for attack in target_entry["last attack"]:
                            diff = abs(impact - attack)
                            if diff > (time_between_farm * 60):
                                passed += 1
                        if passed == len(target_entry["last attack"]):
                            self.attack(target_entry, impact, distance, 'Normal Attack', 'a')
                            self.units['light'] -= 15
                        else:
                            print(
                                f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because timing between attacks")

                # Refresh
            self.driver.refresh()
            for tar in self.targets:
                if self.units['heavy'] < 30 + hold_back['heavy']:
                    break
                target_entry = self.mongo.get_villages(self.targets[tar]['id'])
                if target_entry:
                    now = datetime.now()
                    distance = self.get_dist(self.my_location, target_entry["location"])
                    impact = datetime.timestamp(now + timedelta(minutes=slowest_unit_b * distance))
                    if self.targets[tar]['Beute'] == 'Volle Beute' and self.targets[tar]['Sieg'] == 'Völliger Sieg':
                        self.attack(target_entry, impact, distance, 'Volle Beute', 'b')
                        self.units['heavy'] -= 30
                        continue
                    if self.targets[tar]['Sieg'] == 'Verluste':
                        print(
                            f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack yellow!")
                        continue
                    if self.targets[tar]['Sieg'] == 'Lost':
                        print(
                            f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack red!")
                        continue
                    if target_entry["last attack"]:
                        passed = 0
                        for attack in target_entry["last attack"]:
                            diff = abs(impact - attack)
                            if diff > (time_between_farm * 60):
                                passed += 1
                        if passed == len(target_entry["last attack"]):
                            self.attack(target_entry, impact, distance, 'Normal Attack', 'b')
                            self.units['heavy'] -= 30
                        else:
                            print(
                                f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because timing between attacks")

        # Inf
        time.sleep(1)
        if self.units['axe'] >= 100 or self.units['spear'] >= 50 + hold_back['spear']:
            self.driver.set_farmassist_temp_inf(value_a, value_b)
            self.FA_temp_kav = False
            self.FA_temp_inf = True
            slowest_unit_a = 18
            slowest_unit_b = 18
            time.sleep(1)
            print('Farming with Infanterie')
            for tar in self.targets:
                if self.units['spear'] < 50 + hold_back['spear']:
                    break
                target_entry = self.mongo.get_villages(self.targets[tar]['id'])
                if target_entry:
                    now = datetime.now()
                    distance = self.get_dist(self.my_location, target_entry["location"])
                    impact = datetime.timestamp(now + timedelta(minutes=slowest_unit_a * distance))
                    if self.targets[tar]['Beute'] == 'Volle Beute' and self.targets[tar]['Sieg'] == 'Völliger Sieg':
                        self.attack(target_entry, impact, distance, 'Volle Beute', 'a')
                        self.units['spear'] -= 50
                        continue
                    if self.targets[tar]['Sieg'] == 'Verluste':
                        print(
                            f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack yellow!")
                        continue
                    if self.targets[tar]['Sieg'] == 'Lost':
                        print(
                            f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack red!")
                        continue
                    if target_entry["last attack"]:
                        passed = 0
                        for attack in target_entry["last attack"]:
                            diff = abs(impact - attack)
                            if diff > (time_between_farm * 60):
                                passed += 1
                        if passed == len(target_entry["last attack"]):
                            self.attack(target_entry, impact, distance, 'Normal Attack', 'a')
                            self.units['spear'] -= 50
                        else:
                            print(
                                f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because timing between attacks")

            # Refresh
            self.driver.refresh()
            for tar in self.targets:
                if self.units['axe'] < 100:
                    break
                target_entry = self.mongo.get_villages(self.targets[tar]['id'])
                if target_entry:
                    now = datetime.now()
                    distance = self.get_dist(self.my_location, target_entry["location"])
                    impact = datetime.timestamp(now + timedelta(minutes=slowest_unit_b * distance))
                    if self.targets[tar]['Beute'] == 'Volle Beute' and self.targets[tar]['Sieg'] == 'Völliger Sieg':
                        self.attack(target_entry, impact, distance, 'Volle Beute', 'b')
                        self.units['axe'] -= 100
                        continue
                    if self.targets[tar]['Sieg'] == 'Verluste':
                        print(
                            f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack yellow!")
                        continue
                    if self.targets[tar]['Sieg'] == 'Lost':
                        print(
                            f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack red!")
                        continue
                    if target_entry["last attack"]:
                        passed = 0
                        for attack in target_entry["last attack"]:
                            diff = abs(impact - attack)
                            if diff > (time_between_farm * 60):
                                passed += 1
                        if passed == len(target_entry["last attack"]):
                            self.attack(target_entry, impact, distance, 'Normal Attack', 'b')
                            self.units['axe'] -= 100
                        else:
                            print(
                                f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because timing between attacks")

    def attack(self, target_entry, impact, distance, text, temp):
        print(
            f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Attacking [{temp}] [{text}]")
        self.driver.hit_template(target_entry["id"], temp)
        self.mongo.upload_farm_attack_villages(target_entry["id"], impact)

    def get_slowest_unit_a(self):
        slowest_unit_a = 22
        if self.acc_settings["FA_template_A"]["light"] > 0:
            slowest_unit_a = 10
        if self.acc_settings["FA_template_A"]["heavy"] > 0:
            slowest_unit_a = 11
        if self.acc_settings["FA_template_A"]["spear"] > 0 or \
                self.acc_settings["FA_template_A"]["axe"] > 0:
            slowest_unit_a = 18
        return slowest_unit_a

    def get_slowest_unit_b(self):
        slowest_unit_b = 22
        if self.acc_settings["FA_template_B"]["light"] > 0:
            slowest_unit_b = 10
        if self.acc_settings["FA_template_B"]["heavy"] > 0:
            slowest_unit_b = 11
        if self.acc_settings["FA_template_B"]["spear"] > 0 or \
                self.acc_settings["FA_template_B"]["axe"] > 0:
            slowest_unit_b = 18
        return slowest_unit_b


    def should_farm(self):
        if not self.next_time_farm:
            return True
        if self.next_time_farm < datetime.now():
            return True


    @staticmethod
    def get_dist(my_location, ext_loc):
        distance = math.sqrt(
            ((my_location[0] - ext_loc[0]) ** 2)
            + ((my_location[1] - ext_loc[1]) ** 2)
        )
        return distance