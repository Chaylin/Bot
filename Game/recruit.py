from datetime import datetime


class Recruit:
    v_id = None
    world = None
    driver = None
    config = None
    extractor = None
    console = None

    units = []
    next_time_recruit = None

    def __init__(self, v_id=None, driver=None, config=None, extractor=None, console=None):
        self.v_id = v_id
        self.driver = driver
        self.config = config
        self.extractor = extractor
        self.console = console

    def recruiting(self):
        self.world = self.config.read_config("game", "account", "world")
        if not self.should_recruit():
            return self.next_time_recruit
        return self.next_time_recruit

    def should_recruit(self):
        if not self.next_time_recruit:
            return True
        if self.next_time_recruit < datetime.now():
            return True