from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Input, Label
from textual.containers import VerticalScroll, Horizontal
from datetime import datetime
from . import client_globals # Global db to track activity
from . import client_errors
from . import commands
from . import server_codes
import asyncio

class ImplantList(VerticalScroll):
    def init(self):
        self.mount(Horizontal(id="implant_list_titles"))
        titles = self.get_child_by_id("implant_list_titles")
        titles.mount(Label("ID"))
        titles.mount(Label("Nickname"))
        titles.mount(Label("IP"))
        titles.mount(Label("User"))
        titles.mount(Label("Last Seen"))
        # Populate the existing implants from the implant db
        for implant_name in client_globals.instance_db.implant_db:
            self.mount(Horizontal(id=f"imp-{implant_name}"))
            implant = client_globals.instance_db.implant_db[implant_name]
            implant_item = self.get_child_by_id(f"imp-{implant_name}")
            implant_item.mount(Label(implant_name))
            implant_item.mount(Label("", id=f"nick-{implant_name}"))
            implant_item.mount(Label(implant["ip"]))
            implant_item.mount(Label(implant["user"]))
            implant_item.mount(Label("0s", id=f"timer-{implant_name}"))
            asyncio.create_task(self.update_timer(implant_item.get_child_by_id(f"timer-{implant_name}")))
        self.scroll_end()
    def add_implant(self, implant_name: str, IP: str, user: str):
        self.mount(Horizontal(id=f"imp-{implant_name}"))
        implant_item = self.get_child_by_id(f"imp-{implant_name}")
        implant_item.mount(Label(implant_name))
        implant_item.mount(Label("", id=f"nick-{implant_name}"))
        implant_item.mount(Label(IP))
        implant_item.mount(Label(user))
        implant_item.mount(Label("0s", id=f"timer-{implant_name}"))
        asyncio.create_task(self.update_timer(implant_item.get_child_by_id(f"timer-{implant_name}")))
        self.scroll_end()
    async def update_timer(self, timer_label):
        last_seen = int(timer_label.renderable.plain[:-1])
        while True:
            await asyncio.sleep(1)
            last_seen = last_seen + 1
            timer_label.update(f"{last_seen}s")
    def reset_timer(self, implant_name: str):
        self.get_child_by_id(f"imp-{implant_name}").get_child_by_id(f"timer-{implant_name}").update("0s")

# Where server updates are displayed
class ServerLog(VerticalScroll):
    def add_log(self, text: str):
        # Prepend with the time and Update:
        self.mount(Label(Text.assemble((f"({datetime.now().strftime('%Y/%m/%d %H:%M:%S')}) UPDATE: ","#6495ed bold" ), f"{text}")))
        self.scroll_end()
# Where command output is displayed
# either directly from the client (like input errors)
# or from the implant responding to a command
class CommandOutput(VerticalScroll):
    def print(self, text: Text):
        # Prepend with the time and OK:
        to_print = Text().assemble((f"({datetime.now().strftime('%Y/%m/%d %H:%M:%S')})", "green bold"), (" OK: ", "green bold"))
        to_print.append(text)
        self.mount(Label(to_print))
        self.scroll_end()
    def err_generic(self, text: Text):
        to_print = Text().assemble((f"({datetime.now().strftime('%Y/%m/%d %H:%M:%S')})", "red bold"), (" ERROR: ", "red bold"))
        to_print.append(text)
        self.mount(Label(to_print))
        self.scroll_end()
# Input box at the bottom of the TUI
class CommandInput(Input):
    def clear(self):
        self.value = ""
    def log_output(self, text: Text):
        self.app.get_widget_by_id("command_output").print(text)
    def log_error(self, text: Text):
        self.app.get_widget_by_id("command_output").err_generic(text)
    def action_submit(self):
        # Parse the command
        to_parse = self.value.strip()
        args = ' '.join(to_parse.split())
        args = args.split(' ')

        # Call the function associated with the args[0] from the 
        # CMD_TABLE using the args[1:] slice and pass the client app as well
        # so the function can handle the associated success output / edit the app
        try:
            commands.CMD_TABLE[args[0]](args, self.app)
        # The exceptions raised get handled by an ERROR_TABLE of handlers
        except Exception as err:
            if type(err) in client_errors.ERROR_TABLE:
                client_errors.ERROR_TABLE[type(err)](args, self.app)
            else:
                self.log_error("Exception: {}".format(type(err).__name__))
                self.log_error("Exception message: {}".format(err))

        # Clear input box and exit
        self.clear()
        return

# The actual client, also implements the server update functionality
# with an asyncio task that checks for the server update flag
# in the global 
class Client(App):
    CSS_PATH = "client.css" 
    async def server_update(self):
        while True:
            await asyncio.sleep(3)
            while client_globals.instance_db.server_updates.empty() == False:
                # Get the update from the queue
                s_update = client_globals.instance_db.server_updates.get()
                data = s_update["update_data"]
                # Match the type of update
                match s_update["update_type"]:
                    # If new implant connected
                    case server_codes.ServerUpdates.NEW_IMPLANT.value:
                        new_imp = data
                        # Log the new implant in the server logs section
                        self.get_widget_by_id("server_logs").add_log(Text().assemble(f"New implant \'", (new_imp['name'], "bold"), "\' has connected to the Diet-C2 server."))
                        # Add it to local db
                        client_globals.instance_db.implant_db[new_imp["name"]] = new_imp
                        # Append to implant List
                        self.get_widget_by_id("implant_list").add_implant(implant_name=str(new_imp["name"]), IP=str(new_imp["ip"]), user=str(new_imp["user"]))
                        self.refresh()
                    # If command response from implant
                    case server_codes.ServerUpdates.NEW_COMMAND_RESPONSE.value:
                        # Pull out response
                        cmd_data = data["command"]
                        # Log the response
                        self.get_widget_by_id("command_output").print(Text().assemble(f"Response from \'", (cmd_data['implant_name'], "bold"), "\' for command ID \'", (cmd_data['id'], "bold"), f"\'\n{cmd_data['output']}"))
                        self.refresh()
                    case server_codes.ServerUpdates.IMPLANT_CHECKIN.value:
                        # Pull out the implant name
                        implant_name = data
                        # Reset the timer
                        self.get_widget_by_id("implant_list").reset_timer(str(implant_name))
                        self.refresh()
                    # Default case, just log the error to server_logs for now
                    case _:
                        self.get_widget_by_id("server_logs").add_log(f"Unhandled server update:\ndata={data}\ntype={s_update['update_type']}")
                        self.refresh()
    def on_mount(self):
        self.auto_refresh = 0.5
        asyncio.create_task(self.server_update())
    def compose(self) -> ComposeResult:
        # Initialize the TUI
        with Horizontal():
            implant_list = ImplantList(id="implant_list")
            implant_list.border_title = "Implant List"
            yield implant_list
            implant_list.init()
            server_logs = ServerLog(id="server_logs")
            server_logs.border_title = "Server Logs"
            server_logs.can_focus = False
            yield server_logs
            server_logs.add_log(f"Successfully connected to the Diet-C2 server \'{client_globals.instance_db.server}:{client_globals.instance_db.port}\' as \'{client_globals.instance_db.operator_name}\'")
        command_output = CommandOutput(id="command_output")
        command_output.border_title = "Command Output - No Implant Selected"
        command_output.can_focus = False
        yield command_output
        yield CommandInput(placeholder="Input commands here, 'help' for available commands", id="command_input")
