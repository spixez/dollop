import sys
import os
import json
from . import _dollop

try:
    import questionary
    from prompt_toolkit import prompt
except ImportError:
    questionary = None

class Math:
    def evaluate(self, expr: str) -> float:
        try: return _dollop.evaluate_math(expr)
        except Exception as e: print(f"❌ {e}"); return 0.0

class Measure:
    UNITS = ["m", "ft", "km", "mi", "kg", "lb", "c", "f"]
    def convert(self, v: float, f: str, t: str) -> float:
        try: return _dollop.convert_measure(v, f, t)
        except Exception as e: 
            print(f"❌ {e}\n💡 Supported: {', '.join(self.UNITS)}")
            return 0.0

class Web:
    def run(self, p: int = 8000, d: str = "."):
        try: _dollop.run_web(p, d)
        except KeyboardInterrupt: print("\n👋 Stopped.")
        except Exception as e: print(f"❌ {e}")

class Compute:
    def dot(self, v1: list, v2: list) -> float:
        try: return _dollop.compute_dot(v1, v2)
        except Exception as e: print(f"❌ {e}"); return 0.0
    def mean(self, v: list) -> float: return _dollop.compute_mean(v)
    def median(self, v: list) -> float: return _dollop.compute_median(v)
    def std_dev(self, v: list) -> float:
        try: return _dollop.compute_std_dev(v)
        except Exception as e: print(f"❌ {e}"); return 0.0
    def sort(self, v: list) -> list: return _dollop.compute_sort(v)
    def matmul(self, a: list, b: list) -> list:
        if not isinstance(a, list) or not a or not isinstance(a[0], list):
            print("❌ Matrix must be a 2D list: [[1,2],[3,4]]")
            return []
        try: return _dollop.compute_matrix_mul(a, b)
        except Exception as e: print(f"❌ {e}"); return []

class Secure:
    def hash(self, text: str) -> str: return _dollop.secure_hash(text)
    def gen_password(self, length: int) -> str: 
        try: return _dollop.secure_gen_password(length)
        except Exception as e: print(f"❌ {e}"); return ""

class Network:
    def my_ip(self):
        try: return _dollop.net_my_ip()
        except Exception as e: print(f"❌ {e}"); return "Unknown"
    def scan(self, host: str, start: int = 1, end: int = 1024):
        print(f"🔍 Scanning {host}...")
        try:
            open_ports = _dollop.net_scan_ports(host, start, end)
            if open_ports: print(f"✅ Open ports: {open_ports}")
            else: print("🔒 No open ports found.")
        except KeyboardInterrupt:
            print("\n👋 Scan cancelled.")
        except Exception as e: print(f"❌ {e}")

class System:
    def fetch(self): _dollop.sys_info()

class Editor:
    def open(self, filename: str):
        print(f"📝 {filename}\n💡 [Esc]+[Enter] Save | [Ctrl+C] Cancel")
        content = ""
        if os.path.exists(filename):
            with open(filename, 'r') as f: content = f.read()
        try:
            new = prompt(f"Edit {filename}:\n", default=content, multiline=True)
            with open(filename, 'w') as f: f.write(new)
            print(f"✅ Saved")
        except KeyboardInterrupt: print("\n❌ Cancelled.")

class Viewer:
    def view(self, path: str):
        try: _dollop.view_file(path)
        except Exception as e: print(f"❌ {e}")
    def find(self, pattern: str, path: str):
        try: _dollop.find_in_file(pattern, path)
        except Exception as e: print(f"❌ {e}")

math = Math()
measure = Measure()
web = Web()
editor = Editor()
compute = Compute()
system = System()
viewer = Viewer()
net = Network()
secure = Secure()

def help(): _dollop.help_internal()

def interactive_menu():
    if not questionary:
        print("Error: Missing libs (pip install questionary prompt_toolkit)")
        return
    while True:
        try:
            action = questionary.select(
                "🚀 Dollop Menu",
                choices=["System Fetch", "File Viewer", "Math", "Compute", "Security", "Network Security", "Converter", "Web Server", "Editor", "Help", "Exit"]
            ).ask()
            if action in ["Exit", None]: break
            elif action == "System Fetch": system.fetch()
            elif action == "File Viewer":
                sub = questionary.select("Tool:", choices=["View", "Search", "Back"]).ask()
                if sub == "Back": continue
                f = questionary.text("File:").ask()
                if f:
                    if sub == "View": viewer.view(f)
                    else:
                        p = questionary.text("Pattern:").ask()
                        if p: viewer.find(p, f)
            elif action == "Math":
                e = questionary.text("Expr:").ask()
                if e: print(f"Result: {math.evaluate(e)}")
            elif action == "Compute":
                sub = questionary.select("Tool:", choices=["Matrix Mul", "Stats", "Vector Dot", "Fast Sort", "Back"]).ask()
                if sub == "Back": continue
                if sub == "Matrix Mul":
                    a_str = questionary.text("Matrix A:").ask()
                    b_str = questionary.text("Matrix B:").ask()
                    if a_str and b_str:
                        try: 
                            a = json.loads(a_str)
                            b = json.loads(b_str)
                            print(f"Result: {compute.matmul(a, b)}")
                        except Exception as e: print(f"❌ {e}")
                else:
                    v_str = questionary.text("Numbers:").ask()
                    if v_str:
                        try:
                            v = [float(x) for x in v_str.split()]
                            if sub == "Stats":
                                print(f"Mean: {compute.mean(v)}\nMedian: {compute.median(v)}\nStdDev: {compute.std_dev(v)}")
                            elif sub == "Fast Sort": print(f"Sorted: {compute.sort(v)}")
                            elif sub == "Vector Dot":
                                v2_str = questionary.text("Vector 2:").ask()
                                if v2_str: print(f"Result: {compute.dot(v, [float(x) for x in v2_str.split()])}")
                        except ValueError: print("❌ Invalid numbers")
            elif action == "Security":
                sub = questionary.select("Tool:", choices=["Hash", "Pass Gen", "Back"]).ask()
                if sub == "Back": continue
                if sub == "Hash":
                    t = questionary.text("Text:").ask()
                    if t: print(f"Hash: {secure.hash(t)}")
                else:
                    l = questionary.text("Length:", default="16").ask()
                    if l: 
                        try: print(f"Pass: {secure.gen_password(int(l))}")
                        except ValueError: print("❌ Length must be a number")
            elif action == "Network Security":
                sub = questionary.select("Tool:", choices=["My IP", "Port Scan", "Back"]).ask()
                if sub == "Back": continue
                if sub == "My IP": print(f"IP: {net.my_ip()}")
                else:
                    h = questionary.text("Host:").ask()
                    if h: net.scan(h)
            elif action == "Converter":
                v_str = questionary.text("Value:").ask()
                if v_str:
                    try:
                        v = float(v_str)
                        f = questionary.select("From:", choices=measure.UNITS).ask()
                        t = questionary.select("To:", choices=measure.UNITS).ask()
                        res = measure.convert(v, f, t)
                        if res != 0.0: print(f"Result: {res}")
                    except ValueError: print("❌ Value must be a number")
            elif action == "Web Server":
                p = questionary.text("Port:", default="8000").ask()
                d = questionary.text("Dir:", default=".").ask()
                try: web.run(int(p), d)
                except ValueError: print("❌ Port must be a number")
            elif action == "Editor":
                f = questionary.text("File:").ask()
                if f: editor.open(f)
            elif action == "Help": help()
        except KeyboardInterrupt: break

def main():
    try:
        if len(sys.argv) < 2: interactive_menu()
        elif sys.argv[1] == "sys": system.fetch()
        elif sys.argv[1] == "view" and len(sys.argv) == 3: viewer.view(sys.argv[2])
        elif sys.argv[1] == "find" and len(sys.argv) == 4: viewer.find(sys.argv[2], sys.argv[3])
        elif sys.argv[1] == "help": help()
        elif sys.argv[1] == "net":
            if len(sys.argv) < 3: help(); return
            if sys.argv[2] == "ip": print(net.my_ip())
            elif sys.argv[2] == "scan":
                h = sys.argv[3] if len(sys.argv) > 3 else "127.0.0.1"
                net.scan(h)
        elif sys.argv[1] == "secure":
            if len(sys.argv) < 3: help(); return
            if sys.argv[2] == "hash": print(secure.hash(" ".join(sys.argv[3:])))
            elif sys.argv[2] == "pass":
                try:
                    l = 16
                    if len(sys.argv) == 4: l = int(sys.argv[3])
                    print(secure.gen_password(l))
                except ValueError: print("❌ Length must be a number")
        elif sys.argv[1] == "web":
            p, d = 8000, "."
            try:
                if len(sys.argv) > 2: p = int(sys.argv[2])
                if len(sys.argv) > 3: d = sys.argv[3]
                web.run(p, d)
            except ValueError: print("❌ Port must be a number")
        elif sys.argv[1] == "math": print(math.evaluate(" ".join(sys.argv[2:])))
        elif sys.argv[1] == "convert" and len(sys.argv) == 5:
            try: print(measure.convert(float(sys.argv[2]), sys.argv[3], sys.argv[4]))
            except ValueError: print("❌ Value must be a number")
        elif sys.argv[1] == "edit" and len(sys.argv) == 3: editor.open(sys.argv[2])
        elif sys.argv[1] == "compute":
            if len(sys.argv) < 3: help(); return
            cmd = sys.argv[2]
            try:
                if cmd == "matmul": print(compute.matmul(json.loads(sys.argv[3]), json.loads(sys.argv[4])))
                elif cmd == "stats":
                    v = json.loads(sys.argv[3])
                    print(f"Mean: {compute.mean(v)}\nMedian: {compute.median(v)}\nStdDev: {compute.std_dev(v)}")
                elif cmd == "sort": print(compute.sort(json.loads(sys.argv[3])))
            except json.JSONDecodeError: print("❌ Invalid input: Use JSON format like [1,2,3]")
        else: help()
    except KeyboardInterrupt:
        print("\n👋 Process cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

__all__ = ["math", "measure", "web", "help", "main", "editor", "compute", "system", "viewer", "net", "secure"]
