import pymongo
from datetime import datetime
from Game.config import ConfigStuff
import certifi
import dns.resolver


dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']


class Mongo:
    config = None
    world = None


    def __init__(self):
        ca = certifi.where()
        if not self.config:
            self.config = ConfigStuff()
        if not self.world:
            self.world = self.config.read_config('game', 'account', 'world')
        self.client = pymongo.MongoClient(
            "mongodb+srv://admin:admin@cluster0.kxi86.mongodb.net/Database?retryWrites=true&w=majority", tlsCAFILE=ca)
        self.db = self.client.tribalwars
        self.player = self.db[f'player{self.world}']
        self.own_villages = self.db[f'own_villages{self.world}']
        self.villages = self.db[f'villages{self.world}']


    def find_by_coords(self, x, y):
        query = {"location": [int(x), int(y)]}
        result = self.villages.find_one(query)
        return result


    def get_player(self, player):
        find = {"player": player}
        result = self.player.find(find)
        return result

    def get_all_player(self):
        player = []
        for x in self.player.find():
            player.append(x)
        return player

    def upload_player(self, command_id, data):
        result = self.player.find_one(command_id)
        if result:
            return
        else:
            self.player.insert_one(data)

    def synch_player(self, player, data, default_temp):
        query = {"player": player}
        result = self.player.find_one(query)
        if result:
            update = {"$set": data}
            self.player.update_one(query, update)
            result = self.player.find_one(query)
            return result
        else:
            data.update(default_temp)
            self.player.insert_one(data)
            return default_temp

    def synch_village(self, v_id, default_temp):
        data = {}
        query = {"id": v_id}
        result = self.own_villages.find_one(query)
        if result:
            structure = {
                "game_data": default_temp["game_data"],
            }
            update = {"$set": structure}
            self.own_villages.update_one(query, update)
            if result['buildorder'] != default_temp['buildorder']:
                update = {"$set": {'buildorder': default_temp['buildorder']}}
                self.own_villages.update_one(query, update)
            return result
        else:
            data.update(default_temp)
            self.own_villages.insert_one(data)
            return default_temp


    def delete_attack(self, command_id):
        query = {"command_id": command_id}
        self.player.delete_one(query)

    def response_attack(self, command_id, v_id, response):
        query = {"command_id": command_id}
        response.append(v_id)
        update = {"$set": {"response": response}}
        self.player.update_one(query, update)

    def get_villages(self, v_id):        # download_mongo_villages
        query = {'id': v_id}
        data = self.villages.find_one(query)
        return data

    def get_own_village(self, v_id):
        query = {'id': v_id}
        data = self.own_villages.find_one(query)
        return data

    def get_one_village(self):
        query = {"name": "Barbarendorf"}
        data = self.villages.find_one(query)
        return data

    def add_extra(self, v_id):
        village = {'id': v_id}
        structure = {}
        structure.update({"extra": 1})
        update = {"$set": structure}
        self.villages.update_one(village, update)

    def update_villages(self, v_id, report_type, data):  # update_mongo_villages
        village = {'id': v_id}
        structure = {}
        data_old = self.villages.find_one(village)
        if report_type == "scout" or report_type == "attack":
            if "buildings" in data.keys():
                structure.update({"buildings": data["buildings"]})
            if "resources" in data.keys():
                structure.update({"resources": data["resources"]})
            if "defence_units" in data.keys():
                structure.update({"units": data["defence_units"]})
            if "units_away" in data.keys():
                structure.update({"units_way": data["units_away"]})
            structure.update({"safe for scout": True})
            structure.update({"last extra": 1})
            no_units_in_vil = True
            no_units_away = True
            if "defence_units" in data.keys():
                if data["defence_units"]:
                    no_units_in_vil = False

            if "units_away" in data.keys():
                if data["units_away"]:
                    no_units_away = False


            if no_units_in_vil and no_units_away:
                structure.update({"safe": True})
            else:
                structure.update({"safe": False})
            if data_old:
                if data_old["last scout"]:
                    if "when" in data.keys():
                        if report_type == "scout":
                            if data_old["last scout"] < data["when"]:
                                structure.update({"last scout": data["when"]})
            update = {"$set": structure}
            self.villages.update_one(village, update)

    def upload_villages(self, data):           # upload_mongo_villages
        structure = {
            'id': data['id'],
            'coords': data['coords'],
            'last attack': [1],
            'last ram': 1
        }
        self.villages.insert_one(structure)

    def upload_spy_attack_villages(self, v_id, impact):
        village = {'id': v_id}
        update = {"$set": {
            "last scout": impact,
            }
            }
        result = self.villages.find_one(village)
        if result:
            self.villages.update_one(village, update)

    def upload_extra_attack_villages(self, v_id, impact):
        village = {'id': v_id}
        update = {"$set": {
            "last extra": impact,
        }
        }
        result = self.villages.find_one(village)
        if result:
            self.villages.update_one(village, update)

    def upload_farm_attack_villages(self, v_id, impact):
        village = {'id': v_id}
        result = self.villages.find_one(village)
        if result:
            now = datetime.timestamp(datetime.now())
            attacks = []
            if result["last attack"]:
                for i in result["last attack"]:
                    attacks.append(i)
            for i in attacks:
                if i < now:
                    attacks.remove(i)
            attacks.append(impact)
            update = {"$set": {
                "last attack": attacks,
            }
            }
            self.villages.update_one(village, update)

    def upload_ram_attack_villages(self, v_id, impact):
        village = {'id': v_id}
        update = {"$set": {
            "last ram": impact,
        }
        }
        result = self.villages.find_one(village)
        if result:
            self.villages.update_one(village, update)

    def upload_cata_attack_villages(self, v_id, impact):
        village = {'id': v_id}
        update = {"$set": {
            "last cata": impact,
        }
        }
        result = self.villages.find_one(village)
        if result:
            self.villages.update_one(village, update)