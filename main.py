import httpx
import os
from dotenv import load_dotenv, set_key
import platform
from textual import on
from textual.containers import Vertical, Horizontal, Center, Grid
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Label, Button, Static, TabbedContent, TabPane, ContentSwitcher, Switch, DataTable
from textual.binding import Binding
from textual import work
import pyfiglet
import asyncio
from urchin import UrchinClient, UrchinError
import hypixel
from hypixel import HypixelException, PlayerNotFound
import datetime
from time import sleep
import threading
import queue


load_dotenv()


# wrapper for settings
class Settings:
    def __init__(self):
        self.init_env()
        self.hypixel_key = os.getenv("HYPIXEL_API_KEY", default="")
        self.urchin_key = os.getenv("URCHIN_API_KEY", default="")
        self.blacklist_key = os.getenv("BLACKLIST_API_KEY", default="")
        self.urchin_toggled = os.getenv("URCHIN_TOGGLED", default="True").strip().lower() == "true"
        self.blacklist_toggled = os.getenv("BLACKLIST_TOGGLED", default="True").strip().lower() == "true"
        self.game_path = os.getenv("GAME_PATH", default="")
        self.completed_setup = os.getenv("COMPLETED_SETUP", default="False").strip().lower() == "true"
        self.sort_by = os.getenv("SORT_BY", default="star")


    def init_env(self):
        pass


    def set_hypixel_key(self, key):
        self.hypixel_key = key
        os.environ["HYPIXEL_API_KEY"] = key
        set_key(".env", "HYPIXEL_API_KEY", key)


    def set_urchin_key(self, key):
        self.urchin_key = key
        os.environ["URCHIN_API_KEY"] = key
        set_key(".env", "URCHIN_API_KEY", key)


    def set_blacklist_key(self, key):
        self.blacklist_key = key
        os.environ["BLACKLIST_API_KEY"] = key
        set_key(".env", "BLACKLIST_API_KEY", key)


    def set_urchin_toggled(self, key):
        self.urchin_toggled = key
        os.environ["URCHIN_TOGGLED"] = str(key)
        set_key(".env", "URCHIN_TOGGLED", str(key))


    def set_blacklist_toggled(self, key):
        key = str(key)
        self.blacklist_toggled = key
        os.environ["BLACKLIST_TOGGLED"] = str(key)
        set_key(".env", "BLACKLIST_TOGGLED", str(key))


    def set_game_path(self, key):
        self.game_path = key
        os.environ["GAME_PATH"] = key
        set_key(".env", "GAME_PATH", key)


    def set_completed_setup(self, key):
        self.game_path = key
        os.environ["COMPLETED_SETUP"] = str(key)
        set_key(".env", "COMPLETED_SETUP", str(key))


    def set_sort_by(self, key):
        self.sort_by = key
        os.environ["SORT_BY"] = str(key)
        set_key(".env", "SORT_BY", str(key))



class PlayerDataTable(DataTable):
    BINDINGS = [
        Binding("enter", "expand", "Expand"),
        Binding("s", "search", "Search"),
        Binding("r", "refresh", "Refresh"),
        Binding("t", "tag", "Tag")
    ]

    def expand(self):
        pass

    def search(self):
        pass

    def refresh_list(self):
        pass

    def tag(self):
        pass



# wrapper for all tui stuff
class UI(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = Settings()
        self.stats = Stats()
        self.stream = ChatStream()


    CSS = """
        #start-art {
            width: auto;
            height: auto;
            text-style: bold;
            color: aqua;
        }
        #intro-screen {
            width: 100%;
            height: auto;
            align-horizontal: center;
        }
        .input-stack {
            height: auto;
            margin: 1 2;
        }
        .label {
            width: 20;
            height: 3;
            margin-right: 2;
            content-align: left middle;
        }
        """

    
    def on_mount(self):
        self.title = "Antisniper"
        self.sub_title = "Overlay"

        table = self.query_one("#table", DataTable)
        for col in ["tag", "star", "username", "fkdr", "finals", "wins", "winstreak", "first login", "note"]:
            table.add_column(col, key=col)
        self.start_stream()


    def compose(self):
        intro_text = pyfiglet.figlet_format("Welcome to Antisniper!", font="big")

        yield Header(show_clock=True)
        yield Footer()
        with TabbedContent(initial="setup" if self.settings.completed_setup is False else "overlay", id="nav"):
            with TabPane("Setup", id="setup"):
                with Vertical(id="intro-screen"):
                    with Center():
                        yield Static("[b][aqua]" + intro_text + "[/b][/aqua]", id="start-art")
                    with Center():
                        yield Button("start setup", variant="primary", flat=True, id="setup-button")
            with TabPane("Settings", id="settings"):
                with Horizontal():
                    with Vertical():
                        yield Input(placeholder="hypixel api key", value=self.settings.hypixel_key if self.settings.hypixel_key is not None else "", id="hypixel-key", classes="input-stack")
                        yield Input(placeholder="urchin api key", value=self.settings.urchin_key if self.settings.urchin_key is not None else "", id="urchin-key", classes="input-stack")
                        yield Input(placeholder="blacklist api key", value=self.settings.blacklist_key if self.settings.blacklist_key is not None else "", id="blacklist-key", classes="input-stack")
                    with Vertical():
                        yield Input(placeholder="game logs path", value=self.settings.game_path if self.settings.game_path is not None else "", id="game-path", classes="input-stack")
                        with Horizontal(classes="input-stack"):
                            yield Static("Urchin tags", classes="label")
                            yield Switch(value=self.settings.urchin_toggled if self.settings.urchin_toggled is not None else True, id="urchin-toggle")
                        with Horizontal(classes="input-stack"):
                            yield Static("Blacklist tags", classes="label")
                            yield Switch(value=self.settings.blacklist_toggled if self.settings.blacklist_toggled is not None else True, id="blacklist-toggle")
            with TabPane("Overlay", id="overlay"):
                yield PlayerDataTable(id="table")
            with TabPane("Tag", id="tag"):
                yield Static("tag")
            with TabPane("Info", id="info"):
                yield Static("info")


    @on(Button.Pressed, "#setup-button")
    def setup_button(self):
        self.query_one("#nav", TabbedContent).active = "settings"


    @on(Input.Submitted, "#hypixel-key")
    def update_hypixel_key(self):
        value = self.query_one("#hypixel-key", Input).value.strip()
        if not value:
            self.notify("Key can't be empty", title="Error", severity="error")
            return
        self.settings.set_hypixel_key(value)
        self.notify("Hypixel API key saved", title="Success")


    @on(Input.Submitted, "#urchin-key")
    def update_urchin_key(self):
        value = self.query_one("#urchin-key", Input).value.strip()
        if not value:
            self.notify("Key can't be empty", title="Error", severity="error")
            return
        self.settings.set_urchin_key(value)
        self.notify("Urchin API key saved", title="Success")


    @on(Input.Submitted, "#blacklist-key")
    def update_blacklist_key(self):
        value = self.query_one("#blacklist-key", Input).value.strip()
        if not value:
            self.notify("Key can't be empty", title="Error", severity="error")
            return
        self.settings.set_blacklist_key(value)
        self.notify("Blacklist API key saved", title="Success")


    @on(Input.Submitted, "#game-path")
    def update_game_path(self):
        value = self.query_one("#game-path", Input).value.strip()
        if not value:
            self.notify("Key can't be empty", title="Error", severity="error")
            return
        self.settings.set_game_path(value)
        self.notify("Game path saved", title="Success")


    @on(Switch.Changed, "#urchin-toggle")
    def toggle_urchin(self, event):
        self.settings.set_urchin_toggled(event.value)
        self.notify(f"Toggled urchin {"off" if event.value is False else "on"}", title="Success")


    @on(Switch.Changed, "#blacklist-toggle")
    def toggle_blacklist(self, event):
        self.settings.set_blacklist_toggled(event.value)
        self.notify(f"Toggled blacklist {"off" if event.value is False else "on"}", title="Success")


    @on(DataTable.HeaderSelected, "#table")
    def sort_table(self, event: DataTable.HeaderSelected):
        event.data_table.sort(event.column_key)
        self.settings.set_sort_by(event.column_key.value)


    def start_stream(self):
        self.stream_thread = threading.Thread(
            target=self.stream.wrapper,
            daemon=True
        )
        self.stream_thread.start()
        self.set_interval(0.1, self.watch)


    async def watch(self):
        if not self.stream.queue.empty():
            line = self.stream.queue.get_nowait()
            # /who
            # [02:07:43] [Client thread/INFO]: [CHAT] ONLINE: Darkqz, korokoro2022, TehMonchiooooo, AkanekoYT, cleaarly, ilias_toji, shlawg, finals2006
            if "ONLINE: " in line:
                players = [x.strip() for x in line.split(": ")[-1].split(", ")]
                table = self.query_one("#table")
                table.clear()
                # "tag", "star", "username", "fkdr", "finals", "wins", "winstreak", "first login", "note"

                data = await self.stats.batch_fetch_stats(players)
                for d in data:
                    if type(d) is str:
                        table.add_row("nick", None, d)
                        continue
                    tag = d["blacklist_tags"] if d["blacklist_tags"] != "" else d["urchin_tags"] if (type(d["urchin_tags"] != UrchinError) and d["urchin_tags"] != "") else None
                    reason = d["blacklist_reason"] if (d["blacklist_reason"]) != "" else d["urchin_reason"] if (type(d["urchin_reason"]) != UrchinError and d["urchin_reason"] != "") else None
                    table.add_row(
                            tag, 
                            d["star"], 
                            d["player"], 
                            d["fkdr"], 
                            d["fkills"], 
                            d["wins"], 
                            d["winstreak"],
                            d["first_login"],
                            reason
                        )
                    table.sort(self.settings.sort_by)

                
            # start of game
            if "Protect your bed and destroy the enemy beds." in line:
                pass
            # end of game
            if "Bed Wars XP" in line:
                pass
            # json for server and mode {"server":"mini115BJ","gametype":"BEDWARS","mode":"BEDWARS_EIGHT_ONE","map":"Ambush"}
            if '{"server":' in line:
                pass



class BlacklistClient:
    def __init__(self, api_key):
        self.api_key = api_key

    async def fetch_player_tag(self, player: str) -> list[str, str]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://blacklist.xander.cool/query/{player}")
            if response.json():
                return response.json()["tag"], response.json()["notes"]
            return "", ""
        

    async def batch_fetch_tags(self, players: list[str]):
        pass



class Stats:
    def __init__(self):
        self.data = {}
        self.cache = {}
        self.settings = Settings()
        self.hypixel_client = hypixel.Client(self.settings.hypixel_key)
        self.urchin_client = UrchinClient(api_key=self.settings.urchin_key) if (self.settings.urchin_key != None and self.settings.urchin_toggled) else None
        self.blacklist_client = BlacklistClient(api_key=self.settings.blacklist_key) if (self.settings.blacklist_key != None and self.settings.blacklist_toggled) else None

    async def fetch_stats(self, player: str):
        async with hypixel.Client(self.settings.hypixel_key) as h_client, UrchinClient(api_key=self.settings.urchin_key) as u_client:
            tasks = [h_client.player(player)]
            if self.settings.urchin_key != "" and self.settings.urchin_toggled:
                tasks.append(u_client.get_tags(player))
            # if self.settings.blacklist_key != "" and self.settings.blacklist_toggled:
            if self.settings.blacklist_toggled:
                tasks.append(self.blacklist_client.fetch_player_tag(player))

            
            response = await asyncio.gather(*tasks, return_exceptions=True)
            if type(response[0]) is PlayerNotFound or type(response[0]) is TimeoutError:
                return player
            info = {
                "player": player,
                "uuid": response[0].uuid,
                "urchin_tags": response[1][0].tag_type if self.settings.urchin_toggled and self.settings.urchin_key != "" and (type(response[1]) != UrchinError and len(response[1]) > 0) else "",
                "urchin_reason": response[1][0].reason if self.settings.urchin_toggled and self.settings.urchin_key != "" and (type(response[1]) != UrchinError and len(response[1]) > 0) else "",
                "blacklist_tags": response[-1][0] if self.settings.blacklist_toggled else "",
                "blacklist_reason": response[-1][1] if self.settings.blacklist_toggled else "",
                "rank": response[0].rank,
                "first_login": response[0].first_login.strftime("%m/%Y"),
                "star": response[0].bedwars.level,
                "fkdr": response[0].bedwars.fkdr,
                "wlr": response[0].bedwars.wlr,
                "bblr": response[0].bedwars.bblr,
                "fkills": response[0].bedwars.final_kills,
                "beds": response[0].bedwars.beds_broken,
                "wins": response[0].bedwars.wins,
                "winstreak": response[0].bedwars.winstreak,
            }
            return info


    async def batch_fetch_stats(self, players: list[str]):
        tasks = [self.fetch_stats(p) for p in players]
        response = await asyncio.gather(*tasks, return_exceptions=True)
        return response


class ChatStream:
    def __init__(self):
        self.settings = Settings()
        self.queue = queue.Queue()


    def stream(self):
        path = os.path.join(self.settings.game_path, "latest.log")
        f = open(path, 'r', errors="replace", encoding="utf-8")
        f.seek(0, os.SEEK_END)
        try:
            while True:
                line = f.readline()
                if line:
                    yield line
                    continue
                try:
                    if not os.path.samestat(os.fstat(f.fileno()), os.stat(path)):
                        new = open(path, 'r', errors="replace", encoding="utf-8")
                        f.close()
                        f = new
                        continue
                except FileNotFoundError:
                    pass
                sleep(0.1)
        finally:
            f.close()


    def wrapper(self):
        for line in self.stream():
            self.queue.put(line)



class Game:
    def __init__(self, players, mode, map):
        pass


if __name__ == "__main__":
    UI().run()
    # stats = Stats()
    # r = asyncio.run(stats.batch_fetch_stats(["shlawg", "h119", "leyt"]))
    # print(r)