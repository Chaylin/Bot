import re
from datetime import datetime
from datetime import timedelta


class Defence:
    driver = None
    extractor = None
    config = None
    mongo = None

    player = None
    incomings = {}
    inc_struct = {}
    world = None
    game_data = None

    clear_village = {}

    def __init__(self,
                 extractor=None,
                 config=None,
                 mongo=None,
                 driver=None, ):
        self.driver = driver
        self.extractor = extractor
        self.config = config
        self.mongo = mongo

    def run(self):
        self.world = self.config.read_config("game", "account", "world")
        self.player = self.config.read_config("game", "account", "username")
        attack_count = self.get_attacks()
        self.delete_old_attacks()
        # if self.incomings:
        #    self.cry_for_help()
        return self.clear_village, attack_count

    def get_attacks(self):
        # self.driver.navigate_overview(self.world, self.v_id)
        source = self.driver.get_source()
        self.game_data = self.extractor.game_state(source)
        if int(self.game_data["player"]["incomings"]) > 0:
            self.driver.navigate_attack_screen(self.world)
            self.driver.rename_attacks()
            source = self.driver.get_source()
            self.incomings = self.extractor.attack_form(source)
            return int(self.game_data["player"]["incomings"])
        else:
            return 0

    def cry_for_help(self):
        for part in self.incomings:
            tmp = re.sub("[^0-9:]", "", self.incomings[part]["impact"])
            time_ = datetime.strptime(tmp, '%H:%M:%S')
            time_obj = datetime.time(time_)
            arrive_in = None
            if "heute" in self.incomings[part]["impact"]:
                arrive_in = datetime.combine(datetime.today(), time_obj)
            if "morgen" in self.incomings[part]["impact"]:
                arrive_in = datetime.combine(datetime.today() + timedelta(days=1), time_obj)
            structure = {
                "player": self.player,
                "command_id": self.incomings[part]["command_id"],
                "defender_id": self.incomings[part]["defender"],
                "attacker_id": self.incomings[part]["attacker"],
                "under attack": True,
                "location": self.incomings[part]["defender_location"],
                "slowest unit": self.incomings[part]["attack_type"],
                "impact": arrive_in,
                "response": [],
            }
            if self.incomings[part]["attack_type"] != "Späh":
                self.clear_village.update({self.incomings[part]["defender"]: arrive_in})
            self.mongo.upload_player(self.incomings[part]["command_id"], structure)

    def delete_old_attacks(self):
        command_ids_mongo = []
        command_ids_inc = []
        attack_list = self.mongo.get_player(self.player)
        if attack_list:
            for attack in attack_list:
                command_ids_mongo.append(attack["command_id"])
        if self.incomings:
            for part in self.incomings:
                command_ids_inc.append(self.incomings[part]["command_id"])
        for ids in command_ids_mongo:
            if ids not in command_ids_inc:
                self.mongo.delete_attack(ids)
