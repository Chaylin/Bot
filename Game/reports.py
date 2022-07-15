import json
import re
import time

from Game.extractor import Extractor
from datetime import datetime


class ReportManager:
    driver = None
    config = None
    mongo = None
    v_id = None
    world = None
    game_state = None
    last_reports = {}

    def __init__(self, driver=None, v_id=None, config=None, mongo=None):
        self.driver = driver
        self.v_id = v_id
        self.config = config
        self.mongo = mongo

    def has_resources_left(self, vid):
        possible_reports = []
        for repid in self.last_reports:
            entry = self.last_reports[repid]
            if vid == entry["dest"] and entry["extra"].get("when", None):
                possible_reports.append(entry)
        if len(possible_reports) == 0:
            return False, {}

        def highest_when(attack):
            return datetime.fromtimestamp(int(attack["extra"]["when"]))

        entry = max(possible_reports, key=highest_when)
        if entry["extra"].get("resources", None):
            return True, entry["extra"]["resources"]
        return False, {}

    def safe_to_engage(self, vid):
        for repid in self.last_reports:
            entry = self.last_reports[repid]
            if vid == entry["dest"]:
                if entry["type"] == "attack" and entry["losses"] == {}:
                    return 1
                if (
                        entry["type"] == "scout"
                        and entry["losses"] == {}
                        and (
                        entry["extra"]["defence_units"] == {}
                        or entry["extra"]["defence_units"]
                        == entry["extra"]["defence_losses"]
                )
                ):
                    return 1

                if entry["losses"] != {}:
                    print(f'units sent: {entry["extra"]["units_sent"]}')
                    print(f'units lost: {entry["losses"]}')

                for sent_type in entry["extra"]["units_sent"]:
                    amount = entry["extra"]["units_sent"][sent_type]
                    if sent_type in entry["losses"]:
                        if amount == entry["losses"][sent_type]:
                            return 0  # Lost all units!
                        elif entry["losses"][sent_type] <= 1:
                            # Allow losing 1 unit (luck depended on)
                            return 1  # Lost 'just' one unit

                if entry["losses"] != {}:
                    return 0  # Disengage if anything was lost!
        return -1

    def read(self, page=0, full_run=False):
        self.world = self.config.read_config("game", "account", "world")
        if len(self.last_reports) == 0:
            print("first run")
            self.last_reports = self.config.cache_grab("Reports")
            print("Reports %d" % len(self.last_reports))
        url = f"https://de{self.world}.die-staemme.de/game.php?village={self.v_id}&screen=report&mode=attack&from={page * 12}"
        self.driver.navigate(url)
        self.driver.filter_dot_blue()
        result = self.driver.get_source()
        self.game_state = Extractor.game_state(result)
        new = 0

        ids = Extractor.report_table(result)
        for report_id in ids:
            if report_id in self.last_reports:
                continue
            new += 1
            url = f"https://de{self.world}.die-staemme.de/game.php?village={self.v_id}&screen=report&mode=all&group_id=0&view={report_id}"
            self.driver.navigate(url)
            time.sleep(2)
            data = self.driver.get_source()
            get_type = re.search(r'class="report_(\w+)', data)
            if get_type:
                report_type = get_type.group(1)
                if report_type == "ReportAttack":
                    self.attack_report(data, report_id)
                    continue

                else:
                    res = self.put(report_id, report_type=report_type)
                    self.last_reports[report_id] = res
        if new == 12 or full_run and page < 20:
            page += 1
            print(
                "%d new reports added, also check page %d" % (new, page)
            )
            return self.read(page, full_run=full_run)

    def re_unit(self, inp):
        output = {}
        for row in inp:
            k, v = row
            if int(v) > 0:
                output[k] = int(v)
        return output

    def re_building(self, inp):
        output = {}
        for row in inp:
            k = row["id"]
            v = row["level"]
            if int(v) > 0:
                output[k] = int(v)
        return output

    def attack_report(self, report, report_id):
        from_village = None
        to_village = None
        extra = {}
        losses = {}
        attacked = re.search(r'(\d{2}\.\d{2}\.\d{2} \d{2}\:\d{2}\:\d{2})<span class=\"small grey\">', report)
        if attacked:
            extra["when"] = int(datetime.strptime(attacked.group(1), "%d.%m.%y %H:%M:%S").timestamp())

        attacker = re.search(r'(?s)(<table id="attack_info_att".+?</table>)', report)
        if attacker:
            attacker_data = re.search(
                r'data-player="(\d+)" data-id="(\d+)"', attacker.group(1)
            )
            if attacker_data:
                from_player = attacker_data.group(1)
                from_village = attacker_data.group(2)
                units = re.search(
                    r'(?s)<table id="attack_info_att_units"(.+?)</table>',
                    attacker.group(1),
                )
                if units:
                    sent_units = re.findall("(?s)<tr>(.+?)</tr>", units.group(1))
                    extra["units_sent"] = self.re_unit(
                        Extractor.units_in_total(sent_units[0])
                    )
                    if len(sent_units) == 2:
                        extra["units_losses"] = self.re_unit(
                            Extractor.units_in_total(sent_units[1])
                        )
                        if from_player == self.game_state["player"]["id"]:
                            losses = extra["units_losses"]

        defender = re.search(r'(?s)(<table id="attack_info_def".+?</table>)', report)
        if defender:
            defender_data = re.search(
                r'data-player="(\d+)" data-id="(\d+)"', defender.group(1)
            )
            if defender_data:
                to_player = defender_data.group(1)
                to_village = defender_data.group(2)
                units = re.search(
                    r'(?s)<table id="attack_info_def_units"(.+?)</table>',
                    defender.group(1),
                )
                if units:
                    def_units = re.findall("(?s)<tr>(.+?)</tr>", units.group(1))
                    extra["defence_units"] = self.re_unit(
                        Extractor.units_in_total(def_units[0])
                    )
                    if len(def_units) == 2:
                        extra["defence_losses"] = self.re_unit(
                            Extractor.units_in_total(def_units[1])
                        )
                        if to_player == self.game_state["player"]["id"]:
                            losses = extra["defence_losses"]
        results = re.search(r'(?s)(<table id="attack_results".+?</table>)', report)
        report = report.replace('<span class="grey">.</span>', "")
        if results:
            loot = {}
            for loot_entry in re.findall(
                    r'<span class="icon header (wood|stone|iron)".+?</span>(\d+)', report
            ):
                loot[loot_entry[0]] = loot_entry[1]
            extra["loot"] = loot
            # print("attack report %s -> %s" % (from_village, to_village))

        scout_results = re.search(
            r'(?s)(<table id="attack_spy_resources".+?</table>)', report
        )
        if scout_results:
            # print("scout report %s -> %s" % (from_village, to_village))
            scout_buildings = re.search(
                r'(?s)<input id="attack_spy_building_data" type="hidden" value="(.+?)"',
                report,
            )
            if scout_buildings:
                raw = scout_buildings.group(1).replace("&quot;", '"')
                extra["buildings"] = self.re_building(json.loads(raw))
            found_res = {}
            for loot_entry in re.findall(
                    r'<span class="icon header (wood|stone|iron)".+?</span>(\d+)', scout_results.group(1)
            ):
                found_res[loot_entry[0]] = loot_entry[1]
            extra["resources"] = found_res
            units_away = re.search(
                r'(?s)(<table id="attack_spy_away".+?</table>)', report
            )
            if units_away:
                data_away = self.re_unit(Extractor.units_in_total(units_away.group(1)))
                extra["units_away"] = data_away

        attack_type = "scout" if scout_results and not results else "attack"
        res = self.put(
            report_id, attack_type, from_village, to_village, data=extra, losses=losses
        )
        self.last_reports[report_id] = res
        return True

    def put(
            self,
            report_id,
            report_type,
            origin_village=None,
            dest_village=None,
            losses={},
            data={},
    ):
        output = {
            "type": report_type,
            "origin": origin_village,
            "dest": dest_village,
            "losses": losses,
            "extra": data,
        }
        self.config.set_cache("Reports", report_id, output)
        self.mongo.update_villages(dest_village, report_type, data)
        print(f"add report data to map data [{report_type}] [{str(report_id)}]")
        return output
