import httpx
import os
import json
import platform
from textual import on
from textual.containers import Vertical, Horizontal, Center, Grid
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Label, Button, Static, TabbedContent, TabPane, ContentSwitcher, Switch, DataTable
from textual.screen import ModalScreen
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


# wrapper for settings
class Settings:
    def __init__(self):
        self.file_path = os.path.join(os.getcwd(), "settings.json")
        self.init_settings_file()
        self.settings = self.get_settings()


    def init_settings_file(self):
        if not os.path.isfile(self.file_path):
            template = {
                "api": {
                    "hypixel": "",
                    "urchin": "",
                    "blacklist": ""
                },
                "path": "",
                "urchin": False,
                "blacklist": False,
                "setup_complete": False,
                "sort_by": "star"
            }

            with open(self.file_path, "w+") as f:
                json.dump(template, f, indent=4)


    def get_settings(self):
        with open(self.file_path, "r") as f:
            return json.load(f)


    def save_settings(self):
        with open(self.file_path, "w") as f:
            json.dump(self.settings, f, indent=4)



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


class PlayerModal(ModalScreen):
    def __init__(self, row, stats):
        super().__init__()
        self.row = row
        self.stats = stats


    BINDINGS = [
        Binding("escape", "dismiss", "Exit"),
        Binding("t", "tag", "Update tag")
    ]

    CSS = """
    PlayerModal {
        align: center middle;
    }

    #screen {
        width: 80%;
        height: 80%;
        background: $panel;
    }

    #title {
        text-style: bold;
        color: aqua;
        margin: 1 2 0 2;
    }

    #tag {
        background: $boost;
        margin: 0 2 0 2;
        width: auto;
        padding: 0 1 0 1;
    }

    #stats {
        padding: 0 1 0 1;
        width: 90%;
        height: 90%;
        background: $surface;
        align: center middle;
    }
    """

    def compose(self):
        data = self.stats.cache[self.row[2]]
        yield Footer()
        with Vertical(id="screen"):
            yield Static(pyfiglet.figlet_format(self.row[2], font="pagga"), id="title")
            yield Static(f"[bold][red]{self.row[0]}[/red][/bold]" if self.row[0] is not None else "no tag", id="tag")

            with Horizontal(id="stats"):
                with Vertical():
                    yield Static(f"UUID: {data["uuid"]}")
                    yield Static(f"Rank: {data["rank"]}")
                    yield Static(f"First login: {data["first_login"]}")
                    yield Static(f"Level: {data["level"]}")
                with Vertical():
                    yield Static(f"Urchin tag: {data["urchin_tags"]}")
                    yield Static(f"Urchin notes: {data["urchin_reason"]}")
                    yield Static(f"Blacklist tag: {data["blacklist_tags"]}")
                    yield Static(f"Blacklist notes: {data["blacklist_reason"]}")
                with Vertical():
                    yield Static(f"Star: {data["star"]}")
                    yield Static(f"Wins: {data["wins"]}")
                    yield Static(f"Final kills: {data["fkills"]}")
                    yield Static(f"Beds: {data["beds"]}")
                with Vertical():
                    yield Static(f"FKDR: {data["fkdr"]}")
                    yield Static(f"WLR: {data["wlr"]}")
                    yield Static(f"BBLR: {data["bblr"]}")
                    yield Static(f"Finals per star: {round(data["fkills"]/data["star"], 2)}")
                    yield Static(f"Winstreak: {data["winstreak"]}")

        



# wrapper for all tui stuff
class UI(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = Settings()
        self.stats = Stats(self.settings)
        self.stream = ChatStream(self.settings)


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
            table.add_column(col.strip(), key=col.strip())
        self.start_stream()
        self.test_data()


    def compose(self):
        intro_text = pyfiglet.figlet_format("Welcome to Antisniper!", font="big")

        yield Header(show_clock=True)
        yield Footer()
        with TabbedContent(initial="setup" if self.settings.settings["setup_complete"] is False else "overlay", id="nav"):
            with TabPane("Setup", id="setup"):
                with Vertical(id="intro-screen"):
                    with Center():
                        yield Static("[b][aqua]" + intro_text + "[/b][/aqua]", id="start-art")
                    with Center():
                        yield Button("start setup", variant="primary", flat=True, id="setup-button")
            with TabPane("Settings", id="settings"):
                with Horizontal():
                    with Vertical():
                        yield Input(placeholder="hypixel api key", value=self.settings.settings["api"]["hypixel"], id="hypixel-key", classes="input-stack")
                        yield Input(placeholder="urchin api key", value=self.settings.settings["api"]["hypixel"], id="urchin-key", classes="input-stack")
                        yield Input(placeholder="blacklist api key", value=self.settings.settings["api"]["blacklist"], id="blacklist-key", classes="input-stack")
                    with Vertical():
                        yield Input(placeholder="game logs path", value=self.settings.settings["path"], id="game-path", classes="input-stack")
                        with Horizontal(classes="input-stack"):
                            yield Static("Urchin tags", classes="label")
                            yield Switch(value=self.settings.settings["urchin"], id="urchin-toggle")
                        with Horizontal(classes="input-stack"):
                            yield Static("Blacklist tags", classes="label")
                            yield Switch(value=self.settings.settings["blacklist"], id="blacklist-toggle")
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
        self.settings.settings["api"]["hypixel"] = value
        self.settings.save_settings()
        self.notify("Hypixel API key saved", title="Success")


    @on(Input.Submitted, "#urchin-key")
    def update_urchin_key(self):
        value = self.query_one("#urchin-key", Input).value.strip()
        if not value:
            self.notify("Key can't be empty", title="Error", severity="error")
            return
        self.settings.settings["api"]["urchin"] = value
        self.settings.save_settings()
        self.notify("Urchin API key saved", title="Success")


    @on(Input.Submitted, "#blacklist-key")
    def update_blacklist_key(self):
        value = self.query_one("#blacklist-key", Input).value.strip()
        if not value:
            self.notify("Key can't be empty", title="Error", severity="error")
            return
        self.settings.settings["api"]["blacklist"] = value
        self.settings.save_settings()
        self.notify("Blacklist API key saved", title="Success")


    @on(Input.Submitted, "#game-path")
    def update_game_path(self):
        value = self.query_one("#game-path", Input).value.strip()
        if not value:
            self.notify("Key can't be empty", title="Error", severity="error")
            return
        self.settings.settings["path"] = value
        self.settings.save_settings()
        self.notify("Game path saved", title="Success")


    @on(Switch.Changed, "#urchin-toggle")
    def toggle_urchin(self, event):
        self.settings.settings["urchin"] = bool(event.value)
        self.settings.save_settings()
        self.notify(f"Toggled urchin {"off" if event.value is False else "on"}", title="Success")


    @on(Switch.Changed, "#blacklist-toggle")
    def toggle_blacklist(self, event):
        self.settings.settings["blacklist"] = bool(event.value)
        self.settings.save_settings()
        self.notify(f"Toggled blacklist {"off" if event.value is False else "on"}", title="Success")


    @on(DataTable.HeaderSelected, "#table")
    def sort_table(self, event: DataTable.HeaderSelected):
        event.data_table.sort(event.column_key, key=self.sort_util, reverse=True)
        self.settings.settings["sort_by"] = event.column_key.value
        self.settings.save_settings()


    @on(DataTable.CellSelected, "#table")
    def player_details(self, event: DataTable.CellSelected):
        row = self.query_one("#table").get_row(event.cell_key.row_key)
        self.push_screen(PlayerModal(row, self.stats))


    def start_stream(self):
        self.stream_thread = threading.Thread(
            target=self.stream.wrapper,
            daemon=True
        )
        self.stream_thread.start()
        self.set_interval(0.1, self.watch)


    def sort_util(self, x):
        if type(x) is str:
            try:
                date = datetime.datetime.strptime(x, "%m/%Y")
                return date.timestamp()
            except Exception:
                if x is not None:
                    return 0
                return -1
        if x is None:
            return 0
        return x


    @work
    async def test_data(self):
        table = self.query_one("#table")
        d = await self.stats.fetch_stats("shlawg")
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
                    table.sort(self.settings.settings["sort_by"], key=self.sort_util, reverse=True)
                
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
    def __init__(self, settings_obj):
        self.data = {}
        self.cache = {}
        self.settings = settings_obj
        self.hypixel_client = hypixel.Client(self.settings.settings["api"]["hypixel"])
        self.urchin_client = UrchinClient(api_key=self.settings.settings["api"]["urchin"]) if (self.settings.settings["api"]["urchin"] != None and self.settings.settings["urchin"]) else None
        self.blacklist_client = BlacklistClient(api_key=self.settings.settings["api"]["blacklist"]) if (self.settings.settings["api"]["blacklist"] != None and self.settings.settings["blacklist"]) else None

    async def fetch_stats(self, player: str):
        async with hypixel.Client(self.settings.settings["api"]["hypixel"]) as h_client, UrchinClient(api_key=self.settings.settings["api"]["urchin"]) as u_client:
            tasks = [h_client.player(player)]
            if self.settings.settings["api"]["urchin"] != "" and self.settings.settings["urchin"]:
                tasks.append(u_client.get_tags(player))
            # if self.settings.blacklist_key != "" and self.settings.blacklist_toggled:
            if self.settings.settings["blacklist"]:
                tasks.append(self.blacklist_client.fetch_player_tag(player))

            
            response = await asyncio.gather(*tasks, return_exceptions=True)
            if type(response[0]) is PlayerNotFound or type(response[0]) is TimeoutError:
                return player
            info = {
                "player": player,
                "uuid": response[0].uuid,
                "level": response[0].level,
                "urchin_tags": response[1][0].tag_type if self.settings.settings["urchin"] and self.settings.settings["api"]["urchin"] != "" and (type(response[1]) != UrchinError and len(response[1]) > 0) else "",
                "urchin_reason": response[1][0].reason if self.settings.settings["urchin"] and self.settings.settings["api"]["urchin"] != "" and (type(response[1]) != UrchinError and len(response[1]) > 0) else "",
                "blacklist_tags": response[-1][0] if self.settings.settings["blacklist"] else "",
                "blacklist_reason": response[-1][1] if self.settings.settings["blacklist"] else "",
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
            self.cache[player] = info
            return info


    async def batch_fetch_stats(self, players: list[str]):
        tasks = [self.fetch_stats(p) for p in players]
        response = await asyncio.gather(*tasks, return_exceptions=True)
        return response


class ChatStream:
    def __init__(self, settings_obj):
        self.settings = settings_obj
        self.queue = queue.Queue()


    def stream(self):
        path = None
        f = None
        try:
            while True:
                if path != os.path.join(self.settings.settings["path"], "latest.log"):
                    try:
                        new_path = os.path.join(self.settings.settings["path"], "latest.log")
                        new = open(new_path, 'r', errors="replace", encoding="utf-8")
                        if f:
                            f.close()
                        f = new
                        f.seek(0, os.SEEK_END)
                        path = new_path
                    except OSError:
                        sleep(0.1)
                        continue
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
                except OSError:
                    pass
                sleep(0.1)
        finally:
            if f:
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