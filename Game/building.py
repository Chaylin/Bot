import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from datetime import timedelta
import re


class Building:
    vil_settings = None

    v_id = None
    world = None
    driver = None
    config = None
    extractor = None
    game_data = {}
    dict_buildings = {}
    next_time_build = None
    next_building = None

    def __init__(self, v_id=None, driver=None, config=None, extractor=None):
        self.v_id = v_id
        self.driver = driver
        self.config = config
        self.extractor = extractor

    def building(self, settings):
        self.vil_settings = settings
        self.world = self.config.read_config("game", "account", "world")
        if not self.should_build():
            return self.next_time_build
        print(f"Checking buildings for village: {self.v_id}")
        # Get the buildorder for specific village
        # Navigate to building screen and get building data and "next building"
        self.driver.navigate_build(self.world, self.v_id)
        source = self.driver.get_source()
        self.dict_buildings = self.extractor.building_data(source)
        self.game_data = self.extractor.game_state(source)
        queue_count = self.extractor.active_building_queue(source)
        list_buildings = self.get_buildings(self.dict_buildings)
        next_building = self.get_next_building(list_buildings, self.game_data["village"]["name"])
        # Maybe better build storage or farm or nothing because recruiting?
        checked_next_building = self.check_some_stuff(self.game_data,
                                                      self.dict_buildings,
                                                      next_building,
                                                      queue_count)
        self.driver.build(checked_next_building)
        if int(queue_count) <= 1:
            if checked_next_building is None:
                return
            else:
                return self.should_build()
        # Check queue, don't build before time running out
        queue_time_remaining = self.driver.building_queue_time()
        if queue_time_remaining <= datetime.now():  # build again if < 1 min
            return self.should_build()
        self.next_time_build = queue_time_remaining
        return queue_time_remaining

    def should_build(self):
        if not self.next_time_build:
            return True
        if self.next_time_build < datetime.now():
            return True

    def build(self, building):
        if building is None:
            return
        x = building.split(":")
        link = f"main_buildlink_{x[0]}_{x[1]}"
        try:
            btn_build = self.driver.find_element(By.ID, link)
            print(f"Building {x[0]} level {x[1]}")
            href = btn_build.get_attribute("href")
            self.driver.get(href)
        except NoSuchElementException:
            return
        except Exception as e:
            if 'element click intercepted' in str(e):
                return
            else:
                raise

    def building_queue_time(self):
        try:
            queue_table = self.driver.find_element(By.ID, "buildqueue").get_attribute("innerText")
        except NoSuchElementException:
            return datetime.now()

        source = queue_table
        start_sep = "\t"
        list_time = []
        sum_time = timedelta()
        tmp = source.split(start_sep)
        for parts in tmp:
            x = re.search('[a-zA-Z%]+', parts)  # a-zA-Z
            if x is None:
                y = re.search('[0-9]+', parts)
                if y is not None:
                    list_time.append(parts)
        y = 0
        for x in list_time:
            y = y + 1
        if y >= 2:
            list_time.pop()  # Delete the last element from list
        for i in list_time:
            (h, m, s) = i.split(':')
            d = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
            sum_time += d
        print(f"Building queue lasts for {sum_time}")
        # If queue time low, stay in build screen and wait for it
        if sum_time < timedelta(hours=0, minutes=2, seconds=0):
            time.sleep(10)  # Countdown !!!
            return datetime.now()
        sum_time = sum_time + datetime.now()
        return sum_time

    def check_some_stuff(self, game_data, building_data, next_building, queue_count):
        if not next_building:
            return
        building = next_building.split(":")
        cost_wood = building_data[building[0]]["wood"]
        cost_stone = building_data[building[0]]["stone"]
        cost_iron = building_data[building[0]]["iron"]
        cost_storage = max(cost_iron, cost_stone, cost_wood)
        cost_pop = building_data[building[0]]["pop"]
        if not "storage" == building[0]:
            if cost_storage > game_data["village"]["storage_max"]:
                next_lvl_storage = building_data["storage"]["level_next"]
                print(f"Next building is {building[0]} level {building[1]} \n"
                      f"but building storage level {next_lvl_storage} instead because costs are too high")
                self.check_some_stuff(game_data, building_data, f"storage:{next_lvl_storage}", queue_count)
        if not "farm" == building[0]:
            if cost_pop > (game_data["village"]["pop_max"] - game_data["village"]["pop"]):
                next_lvl_farm = building_data["farm"]["level_next"]
                print(f"Next building is {building[0]} level {building[1]} \n"
                      f"but building farm level {next_lvl_farm} instead because not enough pop")
                self.check_some_stuff(game_data, building_data, f"farm:{next_lvl_farm}", queue_count)
        if cost_wood > game_data["village"]["wood"]:
            print(
                f"Not enough wood for {building[0]} level {building[1]} | {cost_wood} >>> {game_data['village']['wood']} |")
            return None
        if cost_stone > game_data["village"]["stone"]:
            print(
                f"Not enough stone for {building[0]} level {building[1]} | {cost_stone} >>> {game_data['village']['stone']} |")
            return None
        if cost_iron > game_data["village"]["iron"]:
            print(
                f"Not enough iron for {building[0]} level {building[1]} | {cost_iron} >>> {game_data['village']['iron']} |")
            return None
        if cost_pop > (game_data["village"]["pop_max"] - game_data["village"]["pop"]):
            print(
                f"Not enough pop for {building[0]} level {building[1]} | {cost_pop} >>> {game_data['village']['pop']} |")
            return None
        premium_queue = game_data["features"]["Premium"]["active"]
        if premium_queue:
            max_queue = 5
        else:
            max_queue = 2
        if int(queue_count) >= int(max_queue):
            print(f"Already {queue_count} buildings queued, building nothing")
            return None
        return next_building

    def get_next_building(self, list_buildings, village_name):
        next_building = None
        # for x in self.vil_settings["buildorder"]:
        for x in self.config.get_list('buildorder'):
            for y in list_buildings:
                if str(x) == str(y):
                    next_building = x
                    break
            else:
                continue
            break

        if next_building is not None:
            x = next_building.split(":")
            print(f"Next building for {village_name} is {x[0]} level {x[1]}")
        if next_building is None:
            print("No more buildings to build , buildorder is finished")
        return next_building

    @staticmethod
    def get_buildings(data):  # dict from extractor to list like buildorder
        main, barracks, stable, smith, place = 0, 0, 0, 0, 0
        market, wood, stone, iron, farm = 0, 0, 0, 0, 0
        storage, wall, statue, hide, church, watchtower = 0, 0, 0, 0, 0, 0

        main = int(data["main"]["level_next"])
        try:
            barracks = int(data["barracks"]["level_next"])
        except KeyError:
            pass
        try:
            stable = int(data["stable"]["level_next"])
        except KeyError:
            pass
        try:
            smith = int(data["smith"]["level_next"])
        except KeyError:
            pass
        place = int(data["place"]["level_next"])
        try:
            market = int(data["market"]["level_next"])
        except KeyError:
            pass
        wood = int(data["wood"]["level_next"])
        stone = int(data["stone"]["level_next"])
        iron = int(data["iron"]["level_next"])
        farm = int(data["farm"]["level_next"])
        storage = int(data["storage"]["level_next"])
        try:
            wall = int(data["wall"]["level_next"])
        except KeyError:
            pass
        try:
            statue = int(data["statue"]["level_next"])
        except KeyError:
            pass
        try:
            hide = int(data["hide"]["level_next"])
        except KeyError:
            pass
        try:
            church = int(data["church"]["level_next"])
        except KeyError:
            pass
        try:
            watchtower = int(data["watchtower"]["level_next"])
        except KeyError:
            pass

        list_buildings = [
            f"main:{main}",
            f"barracks:{barracks}",
            f"stable:{stable}",
            f"smith:{smith}",
            f"place:{place}",
            f"statue:{statue}",
            f"market:{market}",
            f"wood:{wood}",
            f"stone:{stone}",
            f"iron:{iron}",
            f"farm:{farm}",
            f"storage:{storage}",
            f"wall:{wall}",
            f"hide:{hide}",
            f"church:{church}",
            f"watchtower:{watchtower}",
        ]
        return list_buildings
