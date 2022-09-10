import datetime
from datetime import datetime
from datetime import timedelta
import time
import pathlib
import re
import math
import random
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options



class Driver:
    driver = None
    first_run = True
    actions = 0
    FA_temp_kav = False
    FA_temp_inf = False



    def __init__(self):
        self.ext_path = pathlib.Path(__file__).parent.absolute().joinpath("AntiCaptcha")
        self.options = Options()
        self.options.add_argument(f'--load-extension={self.ext_path}')
        self.driver_path = pathlib.Path(__file__).parent.absolute().joinpath("Driver/chromedriver.exe")
        self.driver = webdriver.Chrome(self.driver_path, chrome_options=self.options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(30)


    def check_captcha(self):
        source = self.get_source()
        if 'data-bot-protect="forced"' in source:
            print('Bot-Captcha active')
            time.sleep(60)

    def refresh(self):
        self.actions += 1
        self.driver.refresh()


    @staticmethod
    def find_between(s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""

    def login(self, user, pw):
        input_user = self.driver.find_element(By.ID, "user")
        input_user.send_keys(user)
        input_pw = self.driver.find_element(By.ID, "password")
        input_pw.send_keys(pw)
        input_pw.submit()



        WebDriverWait(self.driver, 120).until(
            EC.presence_of_element_located((By.CLASS_NAME, "world-select"))
         )

    def build(self, building):
        if building is None:
            return
        x = building.split(":")
        link = f"main_buildlink_{x[0]}_{x[1]}"
        try:
            btn_build = self.driver.find_element(By.ID, link)
            href = btn_build.get_attribute("href")
            self.driver.get(href)
            self.actions += 1
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
        # If queue time low, stay in build screen and wait for it
        if sum_time < timedelta(hours=0, minutes=2, seconds=0):
            return datetime.now()
        sum_time = sum_time + datetime.now()
        return sum_time

    def get_coords_from_target(self):
        time.sleep(1)
        s = self.driver.find_elements(By.CLASS_NAME, "village-name")[0].get_attribute("innerText")
        return s

    def attack(self,
               spear=0,
               sword=0,
               axe=0,
               archer=0,
               spy=0,
               light=0,
               heavy=0,
               marcher=0,
               ram=0,
               cata=0,
               knight=0,
               snob=0,
               attack=False
               ):
        if spear > 0:
            input_spear = self.driver.find_element(By.ID, "unit_input_spear")
            input_spear.send_keys(spear)
        if sword > 0:
            input_sword = self.driver.find_element(By.ID, "unit_input_sword")
            input_sword.send_keys(sword)
        if axe > 0:
            input_axe = self.driver.find_element(By.ID, "unit_input_axe")
            input_axe.send_keys(axe)
        if archer > 0:
            input_archer = self.driver.find_element(By.ID, "unit_input_archer")
            input_archer.send_keys(archer)
        if spy > 0:
            input_spy = self.driver.find_element(By.ID, "unit_input_spy")
            input_spy.send_keys(spy)
        if light > 0:
            input_light = self.driver.find_element(By.ID, "unit_input_light")
            input_light.send_keys(light)
        if heavy > 0:
            input_heavy = self.driver.find_element(By.ID, "unit_input_heavy")
            input_heavy.send_keys(heavy)
        if marcher > 0:
            input_marcher = self.driver.find_element(By.ID, "unit_input_marcher")
            input_marcher.send_keys(marcher)
        if ram > 0:
            input_ram = self.driver.find_element(By.ID, "unit_input_ram")
            input_ram.send_keys(ram)
        if cata > 0:
            input_cata = self.driver.find_element(By.ID, "unit_input_catapult")
            input_cata.send_keys(cata)
        if knight > 0:
            input_knight = self.driver.find_element(By.ID, "unit_input_knight")
            input_knight.send_keys(knight)
        if snob > 0:
            input_snob = self.driver.find_element(By.ID, "unit_input_snob")
            input_snob.send_keys(snob)

        time.sleep(random.randint(1, 2))

        btn_attack = self.driver.find_element(By.ID, "target_attack")
        btn_support = self.driver.find_element(By.ID, "target_support")
        if attack:
            btn_attack.click()
            self.actions += 1
        else:
            btn_support.click()
            self.actions += 1
        time.sleep(random.randint(1, 2))
        try:
            btn_confirm = self.driver.find_element(By.ID, "troop_confirm_submit")
            btn_confirm.click()
            self.actions += 1
            return True
        except:
            print("Not enough units")
            return False

    def switch_village(self):

        try:
            btn = self.driver.find_element(By.CLASS_NAME, "arrowRight")
            btn.click()
            self.actions += 1
        except NoSuchElementException:
            return

    def get_source(self):
        source = self.driver.page_source
        return source

    def get_innerText_by_ID(self, value):
        result = self.driver.find_element(By.ID, value).get_attribute("innerText")
        return result

    def navigate_farmassist(self, v_id, world):
        url = f"https://de{world}.die-staemme.de/game.php?screen=am_farm&village={v_id}"
        self.driver.get(url)
        self.actions += 1

    def navigate_mass_gathering(self, v_id, world, page):
        url = f"https://de{world}.die-staemme.de/game.php?village={v_id}&screen=place&mode=scavenge_mass&page={page}"
        self.driver.get(url)
        self.actions += 1

    def navigate_login(self):
        url = "https://www.die-staemme.de/"
        self.driver.get(url)
        self.actions += 1

    def navigate_overview_troops(self, world):
        url = f"https://de{world}.die-staemme.de/game.php?village=&screen=overview_villages&mode=units"
        self.driver.get(url)
        self.actions += 1

    def navigate_overview(self, world, v_id):
        url = f"https://de{world}.die-staemme.de/game.php?village={v_id}&screen=overview"
        self.driver.get(url)
        self.actions += 1

    def navigate_scavenge(self, world, v_id):
        url = f"https://de{world}.die-staemme.de/game.php?village={v_id}&screen=place&mode=scavenge"
        self.driver.get(url)
        self.actions += 1

    def navigate_place(self, world, v_id):
        url = f"https://de{world}.die-staemme.de/game.php?village={v_id}&screen=place"
        self.driver.get(url)
        self.actions += 1

    def navigate_overview_vil(self, world):
        url = f"https://de{world}.die-staemme.de/game.php?screen=welcome&intro&oscreen=overview_villages"
        self.driver.get(url)
        self.actions += 1

    def navigate_play(self, world):
        url = f"https://www.die-staemme.de/page/play/de{world}"
        self.driver.get(url)
        self.actions += 1

    def navigate_build(self, world, v_id):
        url = f"https://de{world}.die-staemme.de/game.php?village={v_id}&screen=main"
        self.driver.get(url)
        self.actions += 1

    def navigate_train(self, world, v_id):
        url = f"https://de{world}.die-staemme.de/game.php?village={v_id}&screen=train"
        self.driver.get(url)
        self.actions += 1

    def navigate_quest(self):
        try:
            btn_quest = self.driver.find_element(By.ID, "new_quest")
            btn_quest.click()
            self.actions += 1
        except NoSuchElementException:
            return

    def navigate_attack_screen(self, world):
        url = f"https://de{world}.die-staemme.de/game.php?village=&screen=overview_villages&mode=incomings&subtype=attacks"
        self.driver.get(url)
        self.actions += 1

    def navigate_map(self, world, v_id, x, y):
        url = f"https://de{world}.die-staemme.de/game.php?village={v_id}&screen=map#{x};{y}"
        self.driver.get(url)
        self.actions += 1

    def navigate_attack(self, world, v_id, t_id):
        url = f"https://de{world}.die-staemme.de/game.php?village={v_id}&screen=place&target={t_id}"
        self.driver.get(url)
        self.actions += 1

    def navigate(self, url):
        self.driver.get(url)
        self.actions += 1

    def get_url(self):
        return self.driver.current_url

    def complete_quests(self):
        self.driver.refresh()
        self.actions += 1
        btn_quest = self.driver.find_element(By.ID, "new_quest")
        btn_quest.click()
        btn_reward = self.driver.find_element(By.ID, "reward-system-badge")
        self.driver.execute_script("arguments[0].scrollIntoView();", btn_reward)
        try:
            btn_reward.click()
            self.actions += 1
        except ElementNotInteractableException or NoSuchElementException:
            return
        s = btn_reward.get_attribute("innerText")
        quest_count = re.sub("[^0-9]", "", s)
        time.sleep(2)
        x = 0
        while x < int(quest_count):
            element = self.driver.find_element(By.LINK_TEXT, "Abholen")
            element.click()
            time.sleep(random.randint(1, 2))
            x += 1
        self.driver.refresh()
        self.actions += 1

    def mass_gathering(self, v_id, world, village_count):
        page_count = math.ceil(village_count / 50)
        i = 0
        while True:
            # Input Spear
            input_spear = self.driver.find_element(By.NAME, 'spear')
            print('Gathering all villages with 500 spear 4times (all) ')
            input_spear.send_keys(500)
            time.sleep(random.randint(1, 2))

            # Check all columns
            self.driver.execute_script("document.getElementsByClassName('select-all-col')[4].click()")
            time.sleep(random.randint(1, 2))

            # Send Button
            self.driver.execute_script("document.getElementsByClassName('btn btn-default btn-send')[0].click()")
            time.sleep(random.randint(1, 2))

            # Switch Page
            i += 1
            if i == page_count:
                print('break')
                break
            self.navigate_mass_gathering(v_id, world, i)

    def get_gather_time(self):
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        gather_time = []
        gather_time.clear()
        elements = self.driver.find_elements(By.CLASS_NAME, "return-countdown")
        for element in elements:
            (h, m, s) = element.get_attribute("innerText").split(":")
            d = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
            gather_time.append(d)
        if gather_time:
            max_time = max(gather_time)
            time_result = datetime.now() + max_time
            return time_result
        else:
            return None

    def send_gather(self, village_data, value, hold_back, gather_units, game_data):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        spear = village_data["unit_counts_home"]["spear"]
        sword = village_data["unit_counts_home"]["sword"]
        axe = village_data["unit_counts_home"]["axe"]
        heavy = village_data["unit_counts_home"]["heavy"]
        light = village_data["unit_counts_home"]["light"]
        if "archer" in game_data["units"]:
            archer = village_data["unit_counts_home"]["archer"]
        else:
            archer = 0
        if "marcher" in game_data["units"]:
            marcher = village_data["unit_counts_home"]["marcher"]
        else:
            marcher = 0



        if gather_units["spear"]:
            if int(spear) > (10 + int(hold_back["spear"])):
                input_spear = self.driver.find_element(By.NAME, "spear")
                input_spear.send_keys(self.round_down(float(spear - int(hold_back["spear"])) * value))
        if gather_units["sword"]:
            if int(sword) > (10 + int(hold_back["sword"])):
                input_sword = self.driver.find_element(By.NAME, "sword")
                input_sword.send_keys(self.round_down(float(sword - int(hold_back["sword"])) * value))
        if gather_units["axe"]:
            if int(axe) > (10 + int(hold_back["axe"])):
                input_axe = self.driver.find_element(By.NAME, "axe")
                input_axe.send_keys(self.round_down(float(axe - int(hold_back["axe"])) * value))
        if gather_units["archer"]:
            if int(archer) > (10 + int(hold_back["archer"])):
                input_archer = self.driver.find_element(By.NAME, "archer")
                input_archer.send_keys(self.round_down(float(archer - int(hold_back["archer"])) * value))
        if gather_units["light"]:
            if int(archer) > (10 + int(hold_back["light"])):
                input_light = self.driver.find_element(By.NAME, "light")
                input_light.send_keys(self.round_down(float(light - int(hold_back["light"])) * value))
        if gather_units["marcher"]:
            if int(marcher) > (10 + int(hold_back["marcher"])):
                input_marcher = self.driver.find_element(By.NAME, "marcher")
                input_marcher.send_keys(self.round_down(float(marcher - int(hold_back["marcher"])) * value))
        if gather_units["heavy"]:
            if int(heavy) > (10 + int(hold_back["heavy"])):
                input_heavy = self.driver.find_element(By.NAME, "heavy")
                input_heavy.send_keys(self.round_down(float(heavy - int(hold_back["heavy"])) * value))

        btn_send = self.driver.find_elements(By.LINK_TEXT, "Start")
        btn_send[0].click()
        self.actions += 1
        time.sleep(3)

    def get_FA_pages(self):
        pages = len(self.driver.find_elements(By.CLASS_NAME, "paged-nav-item"))
        return int(pages / 2)

    def get_FA_IDs(self, source):
        pass

    def set_farmassist_temp_kav(self, value_a, value_b, light, heavy, units):
        if self.FA_temp_kav:
            return
        # Change template A
        self.driver.find_element(By.NAME, f"spear{value_a}").clear()
        self.driver.find_element(By.NAME, f"spear{value_a}").send_keys(0)
        self.driver.find_element(By.NAME, f"sword{value_a}").clear()
        self.driver.find_element(By.NAME, f"sword{value_a}").send_keys(0)
        self.driver.find_element(By.NAME, f"axe{value_a}").clear()
        self.driver.find_element(By.NAME, f"axe{value_a}").send_keys(0)
        self.driver.find_element(By.NAME, f"spy{value_a}").clear()
        self.driver.find_element(By.NAME, f"spy{value_a}").send_keys(0)
        self.driver.find_element(By.NAME, f"light{value_a}").clear()
        self.driver.find_element(By.NAME, f"light{value_a}").send_keys(light)
        self.driver.find_element(By.NAME, f"heavy{value_a}").clear()
        self.driver.find_element(By.NAME, f"heavy{value_a}").send_keys(0)
        if 'archer' in units:
            self.driver.find_element(By.NAME, f"archer{value_a}").clear()
            self.driver.find_element(By.NAME, f"archer{value_a}").send_keys(0)
        if 'marcher' in units:
            self.driver.find_element(By.NAME, f"marcher{value_a}").clear()
            self.driver.find_element(By.NAME, f"marcher{value_a}").send_keys(0)


        # Change template B
        self.driver.find_element(By.NAME, f"spear{value_b}").clear()
        self.driver.find_element(By.NAME, f"spear{value_b}").send_keys(0)
        self.driver.find_element(By.NAME, f"sword{value_b}").clear()
        self.driver.find_element(By.NAME, f"sword{value_b}").send_keys(0)
        self.driver.find_element(By.NAME, f"axe{value_b}").clear()
        self.driver.find_element(By.NAME, f"axe{value_b}").send_keys(0)
        self.driver.find_element(By.NAME, f"spy{value_b}").clear()
        self.driver.find_element(By.NAME, f"spy{value_b}").send_keys(0)
        self.driver.find_element(By.NAME, f"light{value_b}").clear()
        self.driver.find_element(By.NAME, f"light{value_b}").send_keys(0)
        self.driver.find_element(By.NAME, f"heavy{value_b}").clear()
        self.driver.find_element(By.NAME, f"heavy{value_b}").send_keys(heavy)
        if 'archer' in units:
            self.driver.find_element(By.NAME, f"archer{value_b}").clear()
            self.driver.find_element(By.NAME, f"archer{value_b}").send_keys(0)
        if 'marcher' in units:
            self.driver.find_element(By.NAME, f"marcher{value_b}").clear()
            self.driver.find_element(By.NAME, f"marcher{value_b}").send_keys(0)

        time.sleep(1)
        self.driver.execute_script("document.getElementsByClassName('btn')[0].click()")
        self.actions += 1
        self.FA_temp_kav = True
        self.FA_temp_inf = False

    def set_farmassist_temp_inf(self, value_a, value_b, axe, marcher, units):
        if self.FA_temp_inf:
            return
        # Change template A
        self.driver.find_element(By.NAME, f"spear{value_a}").clear()
        self.driver.find_element(By.NAME, f"spear{value_a}").send_keys(0)
        self.driver.find_element(By.NAME, f"sword{value_a}").clear()
        self.driver.find_element(By.NAME, f"sword{value_a}").send_keys(0)
        self.driver.find_element(By.NAME, f"axe{value_a}").clear()
        self.driver.find_element(By.NAME, f"axe{value_a}").send_keys(0)
        self.driver.find_element(By.NAME, f"spy{value_a}").clear()
        self.driver.find_element(By.NAME, f"spy{value_a}").send_keys(0)
        self.driver.find_element(By.NAME, f"light{value_a}").clear()
        self.driver.find_element(By.NAME, f"light{value_a}").send_keys(0)
        self.driver.find_element(By.NAME, f"heavy{value_a}").clear()
        self.driver.find_element(By.NAME, f"heavy{value_a}").send_keys(0)
        if 'archer' in units:
            self.driver.find_element(By.NAME, f"archer{value_a}").clear()
            self.driver.find_element(By.NAME, f"archer{value_a}").send_keys(0)
        if 'marcher' in units:
            self.driver.find_element(By.NAME, f"marcher{value_a}").clear()
            self.driver.find_element(By.NAME, f"marcher{value_a}").send_keys(marcher)

        # Change template B
        self.driver.find_element(By.NAME, f"spear{value_b}").clear()
        self.driver.find_element(By.NAME, f"spear{value_b}").send_keys(0)
        self.driver.find_element(By.NAME, f"sword{value_b}").clear()
        self.driver.find_element(By.NAME, f"sword{value_b}").send_keys(0)
        self.driver.find_element(By.NAME, f"axe{value_b}").clear()
        self.driver.find_element(By.NAME, f"axe{value_b}").send_keys(axe)
        self.driver.find_element(By.NAME, f"spy{value_b}").clear()
        self.driver.find_element(By.NAME, f"spy{value_b}").send_keys(0)
        self.driver.find_element(By.NAME, f"light{value_b}").clear()
        self.driver.find_element(By.NAME, f"light{value_b}").send_keys(0)
        self.driver.find_element(By.NAME, f"heavy{value_b}").clear()
        self.driver.find_element(By.NAME, f"heavy{value_b}").send_keys(0)
        if 'archer' in units:
            self.driver.find_element(By.NAME, f"archer{value_b}").clear()
            self.driver.find_element(By.NAME, f"archer{value_b}").send_keys(0)
        if 'marcher' in units:
            self.driver.find_element(By.NAME, f"marcher{value_b}").clear()
            self.driver.find_element(By.NAME, f"marcher{value_b}").send_keys(0)

        time.sleep(1)
        self.driver.execute_script("document.getElementsByClassName('btn')[0].click()")
        self.actions += 1
        self.FA_temp_kav = False
        self.FA_temp_inf = True

    def set_farmassist_checks(self):
        if not self.first_run:
            return
        # Set C Checkbox
        self.driver.execute_script("document.getElementsByName('spear')[0].checked = false")
        self.driver.execute_script("document.getElementsByName('sword')[0].checked = false")
        self.driver.execute_script("document.getElementsByName('axe')[0].checked = false")
        self.driver.execute_script("document.getElementsByName('light')[0].checked = true")
        self.driver.execute_script("document.getElementsByName('heavy')[0].checked = false")

        # Set Filters
        self.driver.execute_script("document.getElementById('all_village_checkbox').checked = false")
        self.driver.execute_script("document.getElementById('attacked_checkbox').checked = true")
        self.driver.execute_script("document.getElementById('full_losses_checkbox').checked = false")
        self.driver.execute_script("document.getElementById('partial_losses_checkbox').checked = true")
        self.driver.execute_script("document.getElementById('full_hauls_checkbox').checked = false")
        self.actions += 1


    def get_units_farmassist(self, game_data):
        # Get units
        units = {}
        spear = self.driver.find_element(By.ID, "spear").get_attribute("innerText")
        sword = self.driver.find_element(By.ID, "sword").get_attribute("innerText")
        if 'archer' in game_data['units']:
            archer = self.driver.find_element(By.ID, "archer").get_attribute("innerText")
        else:
            archer = 0
        axe = self.driver.find_element(By.ID, "axe").get_attribute("innerText")
        spy = self.driver.find_element(By.ID, "spy").get_attribute("innerText")
        light = self.driver.find_element(By.ID, "light").get_attribute("innerText")
        if 'marcher' in game_data['units']:
            marcher = self.driver.find_element(By.ID, "marcher").get_attribute("innerText")
        else:
            marcher = 0
        heavy = self.driver.find_element(By.ID, "heavy").get_attribute("innerText")

        structure = {
            "spear": int(spear),
            "sword": int(sword),
            "archer": int(archer),
            "axe": int(axe),
            "spy": int(spy),
            "light": int(light),
            "marcher": int(marcher),
            "heavy": int(heavy),
        }
        units.update(structure)
        return units

    def hit_template(self, v_id, temp):
        time.sleep(0.2)
        script = f"document.getElementsByClassName('farm_village_{v_id} farm_icon farm_icon_{temp}')[0].click()"
        try:
            self.driver.execute_script(script)
            self.actions += 1
        except:
            pass


    @staticmethod
    def round_down(n, decimals=0):
        multiplier = 10 ** decimals
        return int(math.floor(n * multiplier) / multiplier)

    def open_box(self):
        btn = self.driver.find_element(By.LINK_TEXT, "Öffnen")
        btn.click()

    @staticmethod
    def daily_bonus():
        return False
        # if EC.presence_of_element_located((By.ID, "daily_bonus_content")):
            # return True