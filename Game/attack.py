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
        self.driver.check_captcha()
        self.units = self.driver.get_units_farmassist(self.game_data)
        source = self.driver.get_source()
        value = self.extractor.FA_value(source)
        value_a = value[0]
        value_b = value[1]
        hold_back = self.vil_settings['hold_back_farm']

        time.sleep(0.5)

        source = self.driver.get_source()
        self.targets = self.extractor.farmassist_table(source)

        time.sleep(1)

        light = self.acc_settings['farmassist_light']
        axe = self.acc_settings['farmassist_axe']
        marcher = self.acc_settings['farmassist_marcher']
        heavy = self.acc_settings['farmassist_heavy']

        if self.units['light'] >= light or self.units['heavy'] >= heavy + hold_back['heavy']:
            self.driver.set_farmassist_temp_kav(value_a, value_b, light, heavy, self.game_data['units'])
            self.FA_temp_kav = True
            self.FA_temp_inf = False
            slowest_unit_a = 10
            slowest_unit_b = 11
            time.sleep(1)
            print('Farming with Kavallarie')
            for tar in self.targets:
                if self.units['light'] < light:
                    break
                target_entry = self.mongo.get_villages(self.targets[tar]['id'])
                if not target_entry:
                    self.mongo.upload_villages(self.targets[tar])
                    print(f'New Village found: {self.targets[tar]["id"]}')
                    target_entry = self.mongo.get_villages(self.targets[tar]['id'])
                now = datetime.now()
                distance = self.get_dist(self.my_location, self.targets[tar]['coords'])
                impact = datetime.timestamp(now + timedelta(minutes=slowest_unit_a * distance))
                if self.targets[tar]['Beute'] == 'Volle Beute' and self.targets[tar]['Sieg'] == 'Völliger Sieg':
                    self.attack(target_entry, impact, distance, 'Volle Beute', 'a')
                    self.units['light'] -= light
                    continue
                if self.targets[tar]['Sieg'] == 'Verluste':
                    print(f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack yellow!")
                    continue
                if self.targets[tar]['Sieg'] == 'Lost':
                    print(f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack red!")
                    continue
                if self.targets[tar]['Sieg'] == 'Erspäht':
                    if self.targets[tar]['Wall'] > 0:
                        print(f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because wall lvl {self.targets[tar]['Wall']}!")
                        continue
                if target_entry["last attack"]:
                    passed = 0
                    for attack in target_entry["last attack"]:
                        diff = abs(impact - attack)
                        if diff > (time_between_farm * 60):
                            passed += 1
                    if passed == len(target_entry["last attack"]):
                        self.attack(target_entry, impact, distance, 'Normal Attack', 'a')
                        self.units['light'] -= light
                    else:
                        print(
                            f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because timing between attacks")

            # Refresh
            self.driver.refresh()
            for tar in self.targets:
                if self.units['heavy'] < heavy + hold_back['heavy']:
                    break
                target_entry = self.mongo.get_villages(self.targets[tar]['id'])
                if not target_entry:
                    self.mongo.upload_villages(self.targets[tar])
                    print(f'New Village found: {self.targets[tar]["id"]}')
                    target_entry = self.mongo.get_villages(self.targets[tar]['id'])
                now = datetime.now()
                distance = self.get_dist(self.my_location, self.targets[tar]['coords'])
                impact = datetime.timestamp(now + timedelta(minutes=slowest_unit_b * distance))
                if self.targets[tar]['Beute'] == 'Volle Beute' and self.targets[tar]['Sieg'] == 'Völliger Sieg':
                    self.attack(target_entry, impact, distance, 'Volle Beute', 'b')
                    self.units['heavy'] -= heavy
                    continue
                if self.targets[tar]['Sieg'] == 'Verluste':
                    print(
                        f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack yellow!")
                    continue
                if self.targets[tar]['Sieg'] == 'Lost':
                    print(
                        f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack red!")
                    continue
                if self.targets[tar]['Sieg'] == 'Erspäht':
                    if self.targets[tar]['Wall'] > 0:
                        print(f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because wall lvl {self.targets[tar]['Wall']}!")
                        continue
                if target_entry["last attack"]:
                    passed = 0
                    for attack in target_entry["last attack"]:
                        diff = abs(impact - attack)
                        if diff > (time_between_farm * 60):
                            passed += 1
                    if passed == len(target_entry["last attack"]):
                        self.attack(target_entry, impact, distance, 'Normal Attack', 'b')
                        self.units['heavy'] -= heavy
                    else:
                        print(
                            f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because timing between attacks")

        # Inf
        time.sleep(1)
        #
        self.driver.check_captcha()

        if self.units['axe'] >= axe + hold_back['axe'] or self.units['marcher'] >= marcher + hold_back['marcher']:
            self.driver.set_farmassist_temp_inf(value_a, value_b, axe, marcher, self.game_data['units'])
            self.FA_temp_kav = False
            self.FA_temp_inf = True
            slowest_unit_a = 10
            slowest_unit_b = 18
            time.sleep(1)
            for tar in self.targets:
                if self.units['marcher'] < marcher + hold_back['marcher']:
                    break
                target_entry = self.mongo.get_villages(self.targets[tar]['id'])
                if not target_entry:
                    self.mongo.upload_villages(self.targets[tar])
                    print(f'New Village found: {self.targets[tar]["id"]}')
                    target_entry = self.mongo.get_villages(self.targets[tar]['id'])
                now = datetime.now()
                distance = self.get_dist(self.my_location, self.targets[tar]['coords'])
                impact = datetime.timestamp(now + timedelta(minutes=slowest_unit_a * distance))
                if self.targets[tar]['Beute'] == 'Volle Beute' and self.targets[tar]['Sieg'] == 'Völliger Sieg':
                    self.attack(target_entry, impact, distance, 'Volle Beute', 'a')
                    self.units['marcher'] -= marcher
                    continue
                if self.targets[tar]['Sieg'] == 'Verluste':
                    print(
                        f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack yellow!")
                    continue
                if self.targets[tar]['Sieg'] == 'Lost':
                    print(
                        f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack red!")
                    continue
                if self.targets[tar]['Sieg'] == 'Erspäht':
                    if self.targets[tar]['Wall'] > 0:
                        print(f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because wall lvl {self.targets[tar]['Wall']}!")
                        continue
                if target_entry["last attack"]:
                    passed = 0
                    for attack in target_entry["last attack"]:
                        diff = abs(impact - attack)
                        if diff > (time_between_farm * 60):
                            passed += 1
                    if passed == len(target_entry["last attack"]):
                        self.attack(target_entry, impact, distance, 'Normal Attack', 'a')
                        self.units['marcher'] -= marcher
                    else:
                        print(
                            f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because timing between attacks")

            # Refresh
            self.driver.refresh()
            for tar in self.targets:
                if self.units['axe'] < axe:
                    break
                target_entry = self.mongo.get_villages(self.targets[tar]['id'])
                if not target_entry:
                    self.mongo.upload_villages(self.targets[tar])
                    print(f'New Village found: {self.targets[tar]["id"]}')
                    target_entry = self.mongo.get_villages(self.targets[tar]['id'])
                now = datetime.now()
                distance = self.get_dist(self.my_location, self.targets[tar]['coords'])
                impact = datetime.timestamp(now + timedelta(minutes=slowest_unit_b * distance))
                if self.targets[tar]['Beute'] == 'Volle Beute' and self.targets[tar]['Sieg'] == 'Völliger Sieg':
                    self.attack(target_entry, impact, distance, 'Volle Beute', 'b')
                    self.units['axe'] -= axe
                    continue
                if self.targets[tar]['Sieg'] == 'Verluste':
                    print(
                        f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack yellow!")
                    continue
                if self.targets[tar]['Sieg'] == 'Lost':
                    print(
                        f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because last attack red!")
                    continue
                if self.targets[tar]['Sieg'] == 'Erspäht':
                    if self.targets[tar]['Wall'] > 0:
                        print(f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because wall lvl {self.targets[tar]['Wall']}!")
                        continue
                if target_entry["last attack"]:
                    passed = 0
                    for attack in target_entry["last attack"]:
                        diff = abs(impact - attack)
                        if diff > (time_between_farm * 60):
                            passed += 1
                    if passed == len(target_entry["last attack"]):
                        self.attack(target_entry, impact, distance, 'Normal Attack', 'b')
                        self.units['axe'] -= axe
                    else:
                        print(
                            f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Not attacking because timing between attacks")

    def attack(self, target_entry, impact, distance, text, temp):
        print(
            f"Village [{target_entry['id']}] Distance: [{round(distance, 1)}] --> Attacking [{temp}] [{text}]")
        self.driver.hit_template(target_entry["id"], temp)
        self.mongo.upload_farm_attack_villages(target_entry["id"], impact)


    def should_farm(self):
        if not self.next_time_farm:
            return True
        if self.next_time_farm < datetime.now():
            return True


    @staticmethod
    def get_dist(my_location, ext_loc):
        distance = math.sqrt(
            ((my_location[0] - int(ext_loc[0])) ** 2)
            + ((my_location[1] - int(ext_loc[1])) ** 2)
        )
        return distance