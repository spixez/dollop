import sys
import os
import json
from . import _vron
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static, Input, Button, Label, Markdown
from textual.containers import Container, Horizontal, Vertical

PYTHON_FUNDAMENTALS = """
# Python Fundamentals Cheat Sheet

## 1. Variables & Types
```python
x = 10          # Integer
y = 3.14        # Float
name = "Vron"   # String
is_fast = True  # Boolean
```

## 2. Data Structures
```python
nums = [1, 2, 3]          # List
person = {"name": "User"} # Dictionary
unique = {1, 2, 2}        # Set {1, 2}
coords = (10, 20)         # Tuple
```

## 3. Control Flow
```python
if x > 5:
    print("Large")
else:
    print("Small")

for i in range(3):
    print(i)
```

## 4. Functions
```python
def greet(name):
    return f"Hello {name}"

square = lambda x: x * x
```

## 5. Classes
```python
class Tool:
    def __init__(self, name):
        self.name = name
```
"""

class SystemTab(Static):
    def on_mount(self):
        self.update_info()
        self.set_interval(2.0, self.update_info)

    def update_info(self):
        data = _vron.sys_info_data()
        lines = [
            f"[bold cyan]SYSTEM DASHBOARD[/]",
            f"-------------------",
            f"[green]OS:[/]         {data.get('OS', 'Unknown')}",
            f"[green]Kernel:[/]     {data.get('Kernel', 'Unknown')}",
            f"[green]CPU:[/]        {data.get('CPU', 'Unknown')}",
            f"[green]RAM:[/]        {data.get('RAM_Used')} / {data.get('RAM_Total')} MB",
            f"[green]Uptime:[/]     {data.get('Uptime')} seconds",
        ]
        self.update("\n".join(lines))

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
        except Exception as e:
            self.query_one("Label").update(f"Error: {e}")

class VronApp(App):
    TITLE = "VRON HIGH-PERFORMANCE CLI"
    BINDINGS = [("q", "quit", "Quit"), ("d", "toggle_dark", "Toggle Dark Mode")]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("System", id="sys"):
                yield SystemTab()
            with TabPane("Algorithms", id="algo"):
                yield AlgoTab()
            with TabPane("Security & Net", id="sec"):
                yield SecurityTab()
            with TabPane("Python Fundamentals", id="py"):
                yield Markdown(PYTHON_FUNDAMENTALS)
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

def main():
    if len(sys.argv) < 2:
        VronApp().run()
    else:
        # Fallback for old CLI commands if needed, but primary focus is the TUI
        cmd = sys.argv[1]
        if cmd == "sys":
            data = _vron.sys_info_data()
            for k, v in data.items(): print(f"{k}: {v}")
        else:
            VronApp().run()

if __name__ == "__main__":
    main()
