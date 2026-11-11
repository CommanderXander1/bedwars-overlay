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
from urchin import UrchinClient
import hypixel
from hypixel import HypixelException
import datetime
from time import sleep
import threading
import queue


load_dotenv()


# wrapper for settings
class Settings:
    def __init__(self):
        self.hypixel_key = os.getenv("HYPIXEL_API_KEY", default="")
        self.urchin_key = os.getenv("URCHIN_API_KEY", default="")
        self.blacklist_key = os.getenv("BLACKLIST_API_KEY", default="")
        self.urchin_toggled = os.getenv("URCHIN_TOGGLED", default=True).strip().lower() == "true"
        self.blacklist_toggled = os.getenv("BLACKLIST_TOGGLED", default=True).strip().lower() == "true"
        self.game_path = os.getenv("GAME_PATH", default="")
        self.completed_setup = os.getenv("COMPLETED_SETUP", default=False).strip().lower() == "true"


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
        table.add_columns("star", "username", "fkdr", "finals", "wins", "winstreak")
        self.watch()


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


    @work(exclusive=True, thread=True)
    async def watch(self):
        while True:
            for line in await self.stream.stream():
                # /who
                # [02:07:43] [Client thread/INFO]: [CHAT] ONLINE: Darkqz, korokoro2022, TehMonchiooooo, AkanekoYT, cleaarly, ilias_toji, shlawg, finals2006
                if "ONLINE: " in line:
                    pass
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
            info = {
                "player": player,
                "uuid": response[0].uuid,
                "urchin_tags": response[1][0].tag_type if self.settings.urchin_toggled and self.settings.urchin_key != "" and len(response[1]) > 0 else "",
                "urchin_reason": response[1][0].reason if self.settings.urchin_toggled and self.settings.urchin_key != "" and len(response[1]) > 0 else "",
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


    async def stream(self):
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
                await asyncio.sleep(0.1)
        finally:
            f.close()


class Game:
    def __init__(self, players, mode, map):
        pass


if __name__ == "__main__":
    UI().run()
    # cs = ChatStream()
    # asyncio.run(cs.watch())
