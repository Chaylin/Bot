import re
import json


class Extractor:

    @staticmethod
    def get_vils_from_fa(res):
        first = '('
        last = ')'
        tmp = re.split('\t', res)
        list_vil = []

        for t in tmp:
            result = re.search(f'{first}\d\d\d[|]+\d\d\d{last}', t)
            if result:
                list_vil.append(result.group(1))
        return list_vil

    @staticmethod
    def village_data(res):
        if type(res) != str:
            res = res.text
        grabber = re.search(r'var village = (.+);', res)
        if grabber:
            data = grabber.group(1)

            return json.loads(data, strict=False)

    @staticmethod
    def game_state(res):
        if type(res) != str:
            res = res.text
        grabber = re.search(r'TribalWars\.updateGameData\((.+?)\);', res)
        if grabber:
            data = grabber.group(1)
            return json.loads(data, strict=False)

    @staticmethod
    def building_data(res):
        if type(res) != str:
            res = res.text
        dre = re.search(r'(?s)BuildingMain.buildings = (\{.+?\});', res)
        if dre:
            return json.loads(dre.group(1), strict=False)

        return None

    @staticmethod
    def get_quests(res):
        if type(res) != str:
            res = res.text
        get_quests = re.search(r'Quests.setQuestData\((\{.+?\})\);', res)
        if get_quests:
            result = json.loads(get_quests.group(1), strict=False)
            for quest in result:
                data = result[quest]
                if data['goals_completed'] == data['goals_total']:
                    return quest
        return None

    @staticmethod
    def get_quest_rewards(res):
        if type(res) != str:
            res = res.text
        get_rewards = re.search(r'RewardSystem\.setRewards\((\[\{.+?\}\]),', res)
        rewards = []
        if get_rewards:
            result = json.loads(get_rewards.group(1), strict=False)
            for reward in result:
                if reward['status'] == "unlocked":
                    rewards.append(reward)
        # Return all off them
        return rewards

    @staticmethod
    def map_data(res):
        if type(res) != str:
            res = res.text
        data = re.search(r'(?s)TWMap.sectorPrefech = (\[(.+?)\]);', res)
        if data:
            result = json.loads(data.group(1), strict=False)
            return result

    @staticmethod
    def smith_data(res):
        if type(res) != str:
            res = res.text
        data = re.search(r'(?s)BuildingSmith.techs = (\{.+?\});', res)
        if data:
            result = json.loads(data.group(1), strict=False)
            return result
        return None

    @staticmethod
    def premium_data(res):
        if type(res) != str:
            res = res.text
        data = re.search(r'(?s)PremiumExchange.receiveData\((.+?)\);', res)
        if data:
            result = json.loads(data.group(1), strict=False)
            return result
        return None

    @staticmethod
    def recruit_data(res):
        if type(res) != str:
            res = res.text
        data = re.search(r'(?s)unit_managers.units = (\{.+?\});', res)
        if data:
            raw = data.group(1)
            quote_keys_regex = r'([\{\s,])(\w+)(:)'
            processed = re.sub(quote_keys_regex, r'\1"\2"\3', raw)
            result = json.loads(processed, strict=False)
            return result

    @staticmethod
    def units_in_village(res):
        if type(res) != str:
            res = res.text
        data = re.findall(r'(?s)<tr class="all_unit">.+?<a href="#" class="unit_link" data-unit="(\w+)".+?(\d+)</strong>', res)
        return data

    @staticmethod
    def own_units(res):
        if type(res) != str:
            res = res.text
        data = re.findall(r'(?s)<tr class="home_unit hide_toggle">.+?<a href="#" class="unit_link" data-unit="(\w+)".+?(\d+)</strong>', res)
        return data

    @staticmethod
    def support_units(res):
        if type(res) != str:
            res = res.text
        data = re.findall(r'(?s)<tr class="support_unit hide_toggle">.+?<a href="#" class="unit_link" data-unit="(\w+)".+?(\d+)</strong>', res)
        return data

    @staticmethod
    def active_building_queue(res):
        if type(res) != str:
            res = res.text
        builder = re.search('(?s)<table id="build_queue"(.+?)</table>', res)
        if not builder:
            return 0

        return builder.group(1).count('<a class="btn btn-cancel"')

    @staticmethod
    def active_recruit_queue(res):
        if type(res) != str:
            res = res.text
        builder = re.findall(r'(?s)TrainOverview\.cancelOrder\((\d+)\)', res)
        return builder

    @staticmethod
    def village_ids_from_overview(res):
        if type(res) != str:
            res = res.text
        villages = re.findall(r'<span class="quickedit-vn" data-id="(\d+)"', res)
        return list(set(villages))

    @staticmethod
    def units_in_total(res):
        if type(res) != str:
            res = res.text
        # hide units from other villages
        res = re.sub(r'(?s)<span class="village_anchor.+?</tr>', '', res)
        data = re.findall(r'(?s)class=\Wunit-item unit-item-([a-z]+)\W.+?(\d+)</td>', res)
        return data

    @staticmethod
    def attack_form(res):
        if type(res) != str:
            res = res.text
        data = re.findall(r'(?s)<input.+?name="(.+?)".+?value="(.*?)"', res)
        return data

    @staticmethod
    def attack_duration(res):
        if type(res) != str:
            res = res.text
        data = re.search(r'<span class="relative_time" data-duration="(\d+)"', res)
        if data:
            return int(data.group(1))
        return 0

    @staticmethod
    def report_table(res):
        if type(res) != str:
            res = res.text
        data = re.findall(r'(?s)class="report-link" data-id="(\d+)"', res)
        return data

    @staticmethod
    def FA_value(res):
        if type(res) != str:
            res = res.text
        tmp = re.findall(r'(?s)<h3>Farm-Assistent</h3>.+?<form id="farm_units">', res)
        value = re.findall(r'(?s)name="spear(.+?)"', tmp[0])
        return value

    @staticmethod
    def farmassist_table(res):
        if type(res) != str:
            res = res.text
        tmp = re.findall(r'(?s)<table id="plunder_list" style="width:100%;">.+?<div id="plunder_list_nav" style="width:100%;">', res)
        text_fa = re.findall(r'(?s)Alle Berichte für dieses Dorf löschen(.+?)onclick="return Accountmanager.farm.sendUnits', tmp[0])
        village_id = re.findall(r'(?s)<tr id="village_(\d+)" class="report_', tmp[0])


        first = '('
        last = ')'
        coords = re.findall(f'{first}\d\d\d[|]+\d\d\d{last}', tmp[0])

        sieg = []
        wall = []
        beute = []
        for i in text_fa:
            if "Völliger Sieg" in i:
                sieg.append('Völliger Sieg')
                wall.append('?')
            if "Verluste" in i:
                sieg.append('Verluste')
                wall.append('?')
            if "Erspäht" in i:
                sieg.append('Erspäht')
                wall.append(int(re.findall(r'(?s)<td style="text-align: center;">(\d+)</td>\n\n', i)[0]))
            if "Besiegt, aber Gebäude beschädigt" in i:
                sieg.append('Besiegt')
                wall.append('?')
            if "Besiegt" in i:
                sieg.append('Besiegt')
                wall.append('?')
        for i in text_fa:
            if "Volle Beute" in i:
                beute.append('Volle Beute')
            if not "Volle Beute" in i:
                beute.append('Teilweise Beute')

        targets = {}
        for i in range(len(village_id)):
            structure = {i+1: {
                'id': village_id[i],
                'Sieg': sieg[i],
                'Beute': beute[i],
                'coords': [coords[i].split('|')[0], coords[i].split('|')[1]],
                'Wall': wall[i]
            }}
            targets.update(structure)

        return targets

    @staticmethod
    def attack_form(res):
        if type(res) != str:
            res = res.text
        tmp = re.findall(r'(?s)<form id="incomings_form".+?</form>', res)
        command_id = re.findall(r'(?s)name="id_(\d+)" type="checkbox">', tmp[0])
        attack_type = re.findall(f'(?s)<span class="quickedit-label">\n(.+?)</span>\n', tmp[0])
        # defender = re.findall(r'(?s)<a href="/game.php?village=.+?&amp;screen=overview">', tmp[0])
        defender = re.findall(r'(?s)&amp;screen=overview">(.+?)</a>', tmp[0])
        # attacker = re.findall(r'(?s)<a href="/game.php?village=.+?&amp;screen=info_village&amp;id=(.+?)">', tmp[0])
        attacker = re.findall(r'(?s)&amp;screen=info_village&amp;id=(.+?)</a>', tmp[0])
        vil_defender = re.findall(r'(?s)&amp;screen=overview">(.+?)</a>', tmp[0])
        impact = re.findall(f'</td>\n\t<td>\n\t\t\t\t\t(.+?):<span class="grey small">', tmp[0])

        incomings = {}
        for i in range(len(command_id)):
            first = "("
            last = "|"
            start = vil_defender[i].index(first) + len(first)
            end = vil_defender[i].index(last, start)
            x = vil_defender[i][start:end]
            first = "|"
            last = ")"
            start = vil_defender[i].index(first) + len(first)
            end = vil_defender[i].index(last, start)
            y = vil_defender[i][start:end]
            defender_location = [x, y]
            structure = {f"attack {i}": {
                "command_id": command_id[i],
                "attack_type": attack_type[i].strip(),
                "defender": defender[i],
                "attacker": attacker[i],
                "defender_location": defender_location,
                "impact": impact[i],
            }}
            incomings.update(structure)
        return incomings

    @staticmethod
    def find_between(s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""