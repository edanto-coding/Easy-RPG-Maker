import tkinter as tk
from tkinter import filedialog, scrolledtext
import re
import json
import os
import random

# -------------------
# RPG Parser
# -------------------
def parse_rpg(file_path):
    with open(file_path, 'r') as f:
        lines = []
        for line in f:
            stripped_line = line.rstrip()
            if stripped_line.strip():
                indent = len(stripped_line) - len(stripped_line.lstrip(' \t'))
                content = stripped_line.strip()
                lines.append((indent, content))

    def build_tree(index, current_indent):
        node = {}
        while index < len(lines):
            indent, content = lines[index]
            if indent <= current_indent:
                break
            index += 1
            if ' ' in content and not (content.startswith('"') and content.endswith('"')):
                parts = content.split(' ', 1)
                key, value = parts[0], parts[1].strip().strip('"')
                node[key] = value
            else:
                key = content.strip().strip('"')
                child_node, next_index = build_tree(index, indent)
                node[key] = child_node
                index = next_index
        return node, index

    full_data, _ = build_tree(0, -1)
    return full_data

# -------------------
# Digital Shell
# -------------------
class RPGShell:
    def __init__(self, data):
        # Drill down to find the 'rooms' block regardless of headers
        temp_data = data
        for _ in range(3):
            if "rooms" in temp_data: break
            if isinstance(temp_data, dict) and len(temp_data) > 0:
                temp_data = list(temp_data.values())[0]
            else: break
            
        self.rooms = temp_data.get("rooms", {})
        self.global_enemies = temp_data.get("enemies", {})
        self.global_items = temp_data.get("items", {})
        
        start_room = temp_data.get("start", "room1")
        self.current_room = start_room if start_room in self.rooms else list(self.rooms.keys())[0]
        
        # Player Stats
        self.inventory = []
        self.equipment = {"Weapon": "None", "Armor": "None"}
        self.base_hp, self.hp = 100, 100
        self.base_atk, self.current_atk = 5, 5
        self.base_armor, self.current_armor = 0, 0
        
        # Combat State
        self.active_enemy = None
        self.enemy_hp = 0

        # GUI Setup
        self.root = tk.Tk()
        self.root.title("RPG Digital Shell")
        self.root.geometry("800x550")
        self.root.configure(bg="#1e1e1e")

        self.main_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sidebar = tk.Frame(self.root, bg="#2d2d2d", width=200, padx=10, pady=10)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(self.sidebar, text="STATUS", bg="#2d2d2d", fg="#00ff00", font=("Consolas", 14, "bold")).pack(anchor="w")
        self.hp_label = tk.Label(self.sidebar, text=f"HP: {self.hp}", bg="#2d2d2d", fg="#ffffff", font=("Consolas", 12))
        self.hp_label.pack(anchor="w")
        self.atk_label = tk.Label(self.sidebar, text=f"ATK: {self.current_atk}", bg="#2d2d2d", fg="#ff4444", font=("Consolas", 12))
        self.atk_label.pack(anchor="w")
        self.arm_label = tk.Label(self.sidebar, text=f"ARMOR: {self.current_armor}", bg="#2d2d2d", fg="#4444ff", font=("Consolas", 12))
        self.arm_label.pack(anchor="w", pady=(0, 10))
        
        tk.Label(self.sidebar, text="EQUIPMENT", bg="#2d2d2d", fg="#00ff00", font=("Consolas", 14, "bold")).pack(anchor="w")
        self.equip_label = tk.Label(self.sidebar, text="Weapon: None\nArmor: None", bg="#2d2d2d", fg="#ffffff", font=("Consolas", 10), justify=tk.LEFT)
        self.equip_label.pack(anchor="w")

        self.display = scrolledtext.ScrolledText(self.main_frame, state='disabled', wrap='word', bg="#1e1e1e", fg="#00ff00", font=("Consolas", 12), borderwidth=0, highlightthickness=0)
        self.display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.input_frame = tk.Frame(self.main_frame, bg="#1e1e1e")
        self.input_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        
        self.prompt_label = tk.Label(self.input_frame, text=">", bg="#1e1e1e", fg="#00ff00", font=("Consolas", 14, "bold"))
        self.prompt_label.pack(side=tk.LEFT, padx=(0, 10))

        self.entry = tk.Entry(self.input_frame, bg="#2d2d2d", fg="#ffffff", insertbackground="white", font=("Consolas", 12), borderwidth=0, highlightthickness=1, highlightbackground="#333", highlightcolor="#00ff00")
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.entry.bind("<Return>", self.process_command)
        self.entry.focus_set()

        self.log("--- RPG Engine Loaded ---")
        self.show_room()
        self.root.mainloop()

    def log(self, text):
        self.display.configure(state='normal')
        self.display.insert(tk.END, str(text) + "\n")
        self.display.see(tk.END)
        self.display.configure(state='disabled')

    def format_multiline(self, data):
        result = []
        if isinstance(data, dict):
            for key, val in data.items():
                result.append(key)
                if val and isinstance(val, dict):
                    result.append(self.format_multiline(val))
                elif val:
                    result.append(str(val))
        elif data:
            result.append(str(data))
        return " ".join(result).replace('"', '').strip()

    def calculate_stats(self):
        bonus_atk, bonus_armor = 0, 0
        for slot in self.equipment.values():
            if slot != "None" and slot in self.global_items:
                eff = str(self.global_items[slot].get("actualeffect", "")).lower().replace('"', '')
                atk_m = re.search(r'atk\+(\d+)', eff)
                arm_m = re.search(r'armor\+(\d+)', eff)
                if atk_m: bonus_atk += int(atk_m.group(1))
                if arm_m: bonus_armor += int(arm_m.group(1))
        self.current_atk = self.base_atk + bonus_atk
        self.current_armor = self.base_armor + bonus_armor
        self.update_sidebar()

    def update_sidebar(self):
        self.hp_label.config(text=f"HP: {self.hp}")
        self.atk_label.config(text=f"ATK: {self.current_atk}")
        self.arm_label.config(text=f"ARMOR: {self.current_armor}")
        self.equip_label.config(text=f"Weapon: {self.equipment['Weapon']}\nArmor: {self.equipment['Armor']}")

    def show_room(self):
        room = self.rooms.get(self.current_room, {})
        if not room: return
        self.log(f"\n[{self.current_room.upper()}]")
        desc_val = room.get("description", room.get("desc", ""))
        self.log(self.format_multiline(desc_val) if desc_val else "A nondescript room.")
        for key in ["items", "enemies", "exits"]:
            val = room.get(key, {})
            if val:
                names = list(val.keys()) if isinstance(val, dict) else [val]
                self.log(f"{key.capitalize()}: {', '.join(names)}")

    # --- COMBAT LOGIC ---
    def start_combat(self, enemy_name):
        enemy_data = self.global_enemies.get(enemy_name)
        if not enemy_data: return
        self.active_enemy = enemy_name
        self.enemy_hp = int(enemy_data.get("hp", 30))
        self.log(f"\n!!! {enemy_name.upper()} APPEARS !!!")
        self.log(f"{enemy_name} HP: {self.enemy_hp} | ATK: {enemy_data.get('atk')} | ARMOR: {enemy_data.get('armor', 0)}")

    def resolve_combat(self, action):
        enemy_data = self.global_enemies.get(self.active_enemy)
        e_atk = int(enemy_data.get("atk", 5))
        e_arm = min(50, int(enemy_data.get("armor", 0))) 

        if action == "attack":
            # 1. Player Attacks Enemy
            raw_p_dmg = self.current_atk + random.randint(-1, 2)
            reduction = 1 - (e_arm * 0.01)
            final_dmg_to_enemy = max(1, round(raw_p_dmg * reduction))
            
            self.enemy_hp -= final_dmg_to_enemy
            self.log(f"You hit {self.active_enemy} for {final_dmg_to_enemy} damage.")

            if self.enemy_hp <= 0:
                self.log(f"Victory! {self.active_enemy} defeated.")
                room_enemies = self.rooms[self.current_room].get("enemies", {})
                if isinstance(room_enemies, dict) and self.active_enemy in room_enemies:
                    del room_enemies[self.active_enemy]
                self.active_enemy = None
                
                # Check for next enemy
                if room_enemies:
                    next_e = list(room_enemies.keys())[0] if isinstance(room_enemies, dict) else room_enemies
                    self.log("The next foe steps up...")
                    self.start_combat(next_e)
                return

            # 2. Enemy Attacks Player
            p_arm = min(50, self.current_armor)
            raw_e_dmg = e_atk + random.randint(-1, 1)
            p_reduction = 1 - (p_arm * 0.01)
            final_dmg_to_player = max(1, round(raw_e_dmg * p_reduction))
            
            self.hp -= final_dmg_to_player
            self.update_sidebar()
            self.log(f"{self.active_enemy} hits you for {final_dmg_to_player} damage.")

            if self.hp <= 0:
                self.log("--- YOU HAVE DIED ---")
                self.active_enemy = None
            else:
                self.log(f"{self.active_enemy} HP: {self.enemy_hp} | Your HP: {self.hp}")

        elif action == "flee":
            if random.random() > 0.4:
                self.log("Fled successfully!")
                self.active_enemy = None
            else:
                self.log("Failed to escape!")
                raw_e_dmg = e_atk + random.randint(0, 1)
                final_dmg = max(1, round(raw_e_dmg * (1 - (min(50, self.current_armor) * 0.01))))
                self.hp -= final_dmg
                self.update_sidebar()
                self.log(f"{self.active_enemy} hits you for {final_dmg} while you try to run!")

    def process_command(self, event):
        cmd = self.entry.get().strip().lower()
        self.entry.delete(0, tk.END)
        if not cmd: return
        
        if self.active_enemy:
            if cmd in ["attack", "flee"]: self.resolve_combat(cmd)
            else: self.log("In combat! Commands: attack, flee")
            return

        self.log(f"\n> {cmd}")
        room = self.rooms.get(self.current_room, {})

        if cmd == "look": self.show_room()
        elif cmd.startswith("go "):
            dest = cmd[3:]
            if dest in room.get("exits", {}):
                self.current_room = room["exits"][dest]
                self.show_room()
                # Check for new enemies
                new_room = self.rooms.get(self.current_room, {})
                enemies = new_room.get("enemies", {})
                if enemies:
                    self.start_combat(list(enemies.keys())[0] if isinstance(enemies, dict) else enemies)
            else: self.log("Can't go there.")
        elif cmd.startswith("take "):
            item = cmd[5:].strip()
            if item in room.get("items", {}):
                self.inventory.append(item)
                del room["items"][item]
                self.log(f"Taken {item}.")
            else: self.log("Not here.")
        elif cmd.startswith("equip "):
            item = cmd[6:].strip()
            if item in self.inventory:
                eff = str(self.global_items.get(item, {}).get("actualeffect", "")).lower()
                if "atk" in eff or "sword" in item: self.equipment["Weapon"] = item
                else: self.equipment["Armor"] = item
                self.calculate_stats()
                self.log(f"Equipped {item}.")
        elif cmd.startswith("inspect "):
            target = cmd[8:].strip()
            info = self.global_items.get(target)
            if info:
                self.log(f"--- {target.upper()} ---")
                self.log(f"Desc: {self.format_multiline(info.get('description', info.get('desc')))}")
                self.log(f"Effect: {info.get('actualeffect')}")
        elif cmd == "save":
            path = filedialog.asksaveasfilename(filetypes=[("RPG Save", "*.rpgsv")], defaultextension=".rpgsv")
            if path:
                with open(path, 'w') as f:
                    json.dump({"room": self.current_room, "inv": self.inventory, "equip": self.equipment, "rooms": self.rooms, "hp": self.hp}, f)
                self.log(f"Saved: {os.path.basename(path)}")
        elif cmd == "load":
            path = filedialog.askopenfilename(filetypes=[("RPG Save", "*.rpgsv")])
            if path:
                with open(path, 'r') as f:
                    sd = json.load(f)
                    self.current_room, self.inventory, self.equipment, self.rooms = sd["room"], sd["inv"], sd["equip"], sd["rooms"]
                    self.hp = sd.get("hp", 100)
                self.calculate_stats()
                self.log(f"Loaded: {os.path.basename(path)}")
                self.show_room()
        elif cmd == "quit": self.root.destroy(); quit()

def main():
    root = tk.Tk(); root.withdraw()
    path = filedialog.askopenfilename(filetypes=[("RPG", "*.rpg")])
    if path: RPGShell(parse_rpg(path))

if __name__ == "__main__": main()