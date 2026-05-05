import sys
import os
import json
from . import _vron
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static, Input, Button, Label, Markdown
from textual.containers import Container, Horizontal, Vertical

TYPE_HELP = {
    "Integer": """# Integer (int)
Whole numbers without a fraction.
- **Example:** `x = 42`
- **Use for:** Counting, indexing, math without decimals.""",
    "Float": """# Float (float)
Numbers with a decimal point.
- **Example:** `price = 19.99`
- **Use for:** Precise measurements, money, scientific math.""",
    "String": """# String (str)
Text wrapped in quotes.
- **Example:** `name = "Vron"`
- **Use for:** Names, labels, messages, any text data.""",
    "Boolean": """# Boolean (bool)
Logical values: True or False.
- **Example:** `is_running = True`
- **Use for:** Switches, flags, if-conditions.""",
    "List": """# List (list)
An ordered collection of items.
- **Example:** `items = [1, "two", 3.0]`
- **Use for:** Shopping lists, queues, group of similar data.""",
    "Dict": """# Dictionary (dict)
Key-Value pairs (like a real dictionary).
- **Example:** `user = {"id": 1, "name": "Vron"}`
- **Use for:** Databases, profiles, mapping labels to values."""
}

class SystemTab(Static):
    def on_mount(self):
        self.update_info()
        self.set_interval(2.0, self.update_info)

    def update_info(self):
        try:
            data = _vron.sys_info_data()
            lines = [
                f"[bold cyan]SYSTEM DASHBOARD[/]",
                f"-------------------",
                f"OS:         {data.get('OS', 'Unknown')}",
                f"Kernel:     {data.get('Kernel', 'Unknown')}",
                f"CPU:        {data.get('CPU', 'Unknown')}",
                f"RAM:        {data.get('RAM_Used')} / {data.get('RAM_Total')} MB",
                f"Uptime:     {data.get('Uptime')} seconds",
            ]
            self.update("\n".join(lines))
        except Exception as e:
            self.update(f"Error fetching system info: {e}")

class TypeExplorerTab(Static):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Select a type to explore:")
            with Horizontal(id="type_buttons"):
                yield Button("Integer", id="exp_int")
                yield Button("Float", id="exp_float")
                yield Button("String", id="exp_str")
                yield Button("Boolean", id="exp_bool")
                yield Button("List", id="exp_list")
                yield Button("Dict", id="exp_dict")
            yield Markdown(id="type_display")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        display = self.query_one("#type_display")
        key_map = {
            "exp_int": "Integer", "exp_float": "Float", "exp_str": "String",
            "exp_bool": "Boolean", "exp_list": "List", "exp_dict": "Dict"
        }
        if event.button.id in key_map:
            display.update(TYPE_HELP[key_map[event.button.id]])

class CodeBuilderTab(Static):
    code_lines = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Scratch-like Code Builder")
            with Horizontal(id="block_buttons"):
                yield Button("+ Var", id="blk_var", variant="success")
                yield Button("+ Print", id="blk_print", variant="success")
                yield Button("+ If", id="blk_if", variant="success")
                yield Button("+ For", id="blk_for", variant="success")
                yield Button("Clear", id="blk_clear", variant="error")
            yield Static("", id="code_preview", classes="code_box")

    def update_preview(self):
        preview = self.query_one("#code_preview")
        if not self.code_lines:
            preview.update("Your code will appear here...")
        else:
            preview.update("\n".join(self.code_lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "blk_var":
            self.code_lines.append("x = 10")
        elif event.button.id == "blk_print":
            self.code_lines.append('print("Hello from Vron!")')
        elif event.button.id == "blk_if":
            self.code_lines.append("if x > 5:")
            self.code_lines.append('    print("x is large")')
        elif event.button.id == "blk_for":
            self.code_lines.append("for i in range(5):")
            self.code_lines.append("    print(i)")
        elif event.button.id == "blk_clear":
            self.code_lines = []
        
        self.update_preview()

class AlgoTab(Static):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Algorithms & Math")
            yield Input(placeholder="Number for Fibonacci/Factorial/Prime", id="algo_input")
            with Horizontal():
                yield Button("Fibonacci", variant="primary", id="btn_fib")
                yield Button("Factorial", variant="primary", id="btn_fact")
                yield Button("Is Prime?", variant="primary", id="btn_prime")
            yield Label("", id="algo_result")
            yield Label("Sorting & Search")
            yield Input(placeholder="Space separated numbers: 5 2 9 1", id="sort_input")
            with Horizontal():
                yield Button("Sort", id="btn_sort")
                yield Input(placeholder="Search Target", id="search_target", classes="small_input")
                yield Button("Binary Search", id="btn_search")
            yield Label("", id="sort_result")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        input_val = self.query_one("#algo_input").value
        result_label = self.query_one("#algo_result")
        
        try:
            if event.button.id == "btn_fib":
                n = int(input_val)
                result_label.update(f"Fibonacci({n}) = {_vron.math_fibonacci(n)}")
            elif event.button.id == "btn_fact":
                n = int(input_val)
                result_label.update(f"Factorial({n}) = {_vron.math_factorial(n)}")
            elif event.button.id == "btn_prime":
                n = int(input_val)
                res = "is Prime" if _vron.math_is_prime(n) else "is NOT Prime"
                result_label.update(f"{n} {res}")
            
            sort_val = self.query_one("#sort_input").value
            sort_res_label = self.query_one("#sort_result")
            if event.button.id == "btn_sort":
                nums = [float(x) for x in sort_val.split()]
                sorted_nums = _vron.compute_sort(nums)
                sort_res_label.update(f"Sorted: {sorted_nums}")
            elif event.button.id == "btn_search":
                nums = sorted([float(x) for x in sort_val.split()])
                target = float(self.query_one("#search_target").value)
                idx = _vron.algo_binary_search(nums, target)
                sort_res_label.update(f"Binary Search (on sorted list): Index {idx}")
        except ValueError:
            result_label.update("Error: Please enter valid numbers")
        except Exception as e:
            result_label.update(f"Error: {e}")

class SecurityTab(Static):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Security Tools")
            yield Input(placeholder="Text to hash (SHA256)", id="hash_input")
            yield Button("Generate Hash", id="btn_hash")
            yield Label("", id="hash_result")
            yield Label("Password Generator")
            yield Input(placeholder="Length", value="16", id="pass_len")
            yield Button("Generate Password", id="btn_pass")
            yield Label("", id="pass_result")
            yield Label("Network")
            yield Button("Get My IP", id="btn_ip")
            yield Label("", id="ip_result")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        try:
            if event.button.id == "btn_hash":
                t = self.query_one("#hash_input").value
                self.query_one("#hash_result").update(f"Hash: {_vron.secure_hash(t)}")
            elif event.button.id == "btn_pass":
                l = int(self.query_one("#pass_len").value)
                self.query_one("#pass_result").update(f"Pass: {_vron.secure_gen_password(l)}")
            elif event.button.id == "btn_ip":
                self.query_one("#ip_result").update(f"IP: {_vron.net_my_ip()}")
        except ValueError:
            self.query_one("Label").update("Error: Invalid length")
        except Exception as e:
            self.query_one("Label").update(f"Error: {e}")

class VronApp(App):
    TITLE = "VRON HIGH-PERFORMANCE CLI"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("System", id="sys"):
                yield SystemTab()
            with TabPane("Algorithms", id="algo"):
                yield AlgoTab()
            with TabPane("Security & Net", id="sec"):
                yield SecurityTab()
            with TabPane("Type Explorer", id="types"):
                yield TypeExplorerTab()
            with TabPane("Code Builder", id="scratch"):
                yield CodeBuilderTab()
        yield Footer()

def main():
    if len(sys.argv) < 2:
        VronApp().run()
        return

    cmd = sys.argv[1]
    try:
        if cmd == "sys":
            data = _vron.sys_info_data()
            for k, v in data.items(): print(f"{k}: {v}")
        elif cmd == "math" and len(sys.argv) > 2:
            print(_vron.evaluate_math(" ".join(sys.argv[2:])))
        elif cmd == "compute" and len(sys.argv) > 3:
            sub = sys.argv[2]
            val = json.loads(sys.argv[3])
            if sub == "stats":
                print(f"Mean: {_vron.compute_mean(val)}")
                print(f"Median: {_vron.compute_median(val)}")
                print(f"StdDev: {_vron.compute_std_dev(val)}")
            elif sub == "sort":
                print(_vron.compute_sort(val))
        elif cmd == "secure" and len(sys.argv) > 3:
            sub = sys.argv[2]
            if sub == "hash": print(_vron.secure_hash(" ".join(sys.argv[3:])))
            elif sub == "pass": print(_vron.secure_gen_password(int(sys.argv[3])))
        elif cmd == "net" and len(sys.argv) > 2:
            if sys.argv[2] == "ip": print(_vron.net_my_ip())
        elif cmd == "algo" and len(sys.argv) > 3:
            sub, n = sys.argv[2], int(sys.argv[3])
            if sub == "fib": print(_vron.math_fibonacci(n))
            elif sub == "fact": print(_vron.math_factorial(n))
            elif sub == "prime": print(_vron.math_is_prime(n))
        else:
            VronApp().run()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
