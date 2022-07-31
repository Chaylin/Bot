from configparser import ConfigParser
import pathlib
import os
import json
import re


class ConfigStuff:
    def __init__(self):
        self.config = ConfigParser()
        self.game_path = pathlib.Path(__file__).parent.absolute().joinpath("ConfigFiles\game.ini")
        self.farm_path = pathlib.Path(__file__).parent.absolute().joinpath("ConfigFiles\farm.ini")
        self.cache_path = pathlib.Path(__file__).parent.absolute().joinpath("Cache")

    def read_config(self, config, section, search):
        path = None
        if config == "game":
            path = self.game_path
        if config == "farm":
            path = self.farm_path
        self.config.read(path)
        result = self.config[section][search]
        return result

    def read_config_bool(self, config, section, search):
        path = None
        if config == "game":
            path = self.game_path
        if config == "farm":
            path = self.farm_path
        self.config.read(path)
        result = self.config.getboolean(section, search)
        return result

    def read_account_data(self):
        self.config.read(self.game_path)
        user = self.config["account"]["username"]
        pw = self.config["account"]["password"]
        world = self.config["account"]["world"]
        return user, pw, world

    def check_config_files(self):
        try:
            self.config.read(self.game_path)
            if not self.config.has_section("account"):
                return False
        except:
            raise
        return True

    def check_village(self, v_id):
        self.config.read(self.game_path)
        if self.config.has_section(f"village {v_id}"):
            return True
        else:
            return False

    @staticmethod
    def get_list(template):
        output_json = False
        buildorder_path = pathlib.Path(__file__).parent.absolute().joinpath(f"ConfigFiles\{template}.txt")
        if os.path.exists(buildorder_path):
            with open(buildorder_path, 'r') as f:
                if output_json:
                    return json.load(f)
                return f.read().strip().split()
        return None

        # Returns: list = ['wood:1', 'iron:1', .....]

    def check_cache(self, cache, v_id):
        path = self.cache_path.joinpath(f"{cache}\{v_id}.json")
        file = pathlib.Path(path)
        if file.is_file():
            return True
        else:
            return False

    def write_cache(self, cache, data):
        v_id = data["village"]["id"]
        path = self.cache_path.joinpath(f"{cache}\{v_id}.json")
        data_string = json.dumps(data, indent=2)
        with open(path, "w") as f:
            f.write(data_string)

    def get_id_from_map_folder(self):
        id_list = []
        folder = self.cache_path.joinpath("map")
        folder_list = os.listdir(folder)
        for ids in folder_list:
            i = re.sub("[^0-9]", "", ids)
            id_list.append(i)
        return id_list

    def delete_cache(self, cache):
        folder = self.cache_path.joinpath(cache)
        folder_list = os.listdir(folder)
        for x in folder_list:
            path = self.cache_path.joinpath(f"{cache}/{x}")
            os.remove(path)

    def get_cache(self, cache, v_id):
        path = self.cache_path.joinpath(f"{cache}/{v_id}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return None

    def set_cache(self, cache, v_id, entry):
        path = self.cache_path.joinpath(f"{cache}/{v_id}.json")
        if '_id' in entry.keys():
            entry.pop('_id')
        with open(path, "w") as f:
            return f.write(json.dumps(entry))


    def cache_grab(self, cache):
        output = {}
        path = self.cache_path.joinpath(cache)
        for existing in os.listdir(path):
            if not existing.endswith(".json"):
                continue
            t_path = self.cache_path.joinpath("Reports", existing)
            with open(t_path, "r") as f:
                output[existing.replace(".json", "")] = json.load(f)
        return output