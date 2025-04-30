import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import re
import os
import sys
import tempfile

class ModernCronGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CronGUI - GUI crontab editor")
        self.root.geometry("1450x1000")  
        
        # my pretty new theme
        self.apply_modern_theme()
        
        # sudo check
        self.is_elevated = os.geteuid() == 0
        
        # init cron
        self.crontab_entries = []
        self.current_user = self.get_username()
        
        # create a central container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=50, pady=40)
        
        self.create_header()
        
        # the main content 
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # controls
        self.create_top_controls()
        
        # entries view
        self.create_entries_view()
        
        # editor 
        self.create_editor_section()
        
        # load the current crontab
        self.load_crontab()
        
        # status bar
        self.create_status_bar()

    def apply_modern_theme(self):
        
        # paint it grey
        self.bg_dark = "#0D1117"
        self.bg_medium = "#161B22"
        self.bg_light = "#30363D"

        
        self.accent_main = "#30363D"   
        self.accent_hover = "#30363D"  
        self.accent_subtle = "#7D00FF" 

        self.text_light = "#E6EDF3"    
        self.text_muted = "#8B949E"    
        
        # root window
        self.root.configure(bg=self.bg_dark)
        
        style = ttk.Style(self.root)
        
        # frames
        style.configure("TFrame", background=self.bg_dark)
        style.configure("Container.TFrame", background=self.bg_medium)
        style.configure("Card.TFrame", background=self.bg_medium)
        
        # label styles
        style.configure("TLabel", 
                      background=self.bg_dark, 
                      foreground=self.text_light,
                      font=("Orbitron", 12))
        style.configure("Header.TLabel", 
                      background=self.bg_dark, 
                      foreground=self.text_light, 
                      font=("Orbitron", 24, "bold"))
        style.configure("SubHeader.TLabel", 
                      background=self.bg_dark, 
                      foreground=self.text_muted, 
                      font=("Orbitron", 16))
        style.configure("StatusBar.TLabel", 
                      background=self.bg_medium, 
                      foreground=self.text_muted, 
                      font=("Orbitron", 11))
        
        style.configure("TButton",
                      background=self.bg_dark,
                      foreground=self.text_light,
                      borderwidth=2,
                      relief="solid",
                      padding=(12, 6),
                      font=("Orbitron", 10, "bold"))
        style.map("TButton",
                background=[("active", self.bg_dark), ("pressed", self.bg_dark)],
                foreground=[("active", self.text_light)])

        style.configure("Accent.TButton",
                      background=self.bg_dark,
                      foreground=self.text_light,
                      borderwidth=2,
                      relief="solid",
                      padding=(12, 6),
                      font=("Orbitron", 10, "bold"))
        style.map("Accent.TButton",
                background=[("active", self.bg_dark), ("pressed", self.bg_dark)],
                foreground=[("active", self.text_light)])
        
        # treeview styling
        style.configure("Treeview",
                      background=self.bg_medium,
                      foreground=self.text_light,
                      fieldbackground=self.bg_medium,
                      borderwidth=0,
                      font=("Orbitron", 10))
        style.map("Treeview",
                background=[("selected", self.accent_subtle)],
                foreground=[("selected", self.text_light)])
        
        # treeview header
        style.configure("Treeview.Heading",
                      background=self.bg_light,
                      foreground=self.text_light,
                      relief="flat",
                      borderwidth=0,
                      font=("Orbitron", 10, "bold"))
        style.map("Treeview.Heading",
                background=[("active", self.accent_subtle)])
        
        # some entry widgets
        style.configure("TEntry", 
                      fieldbackground=self.bg_medium,
                      foreground=self.text_light,
                      borderwidth=0,
                      font=("Orbitron", 10))
        
        # combobox
        style.configure("TCombobox", 
                      fieldbackground=self.bg_medium,
                      background=self.bg_medium,
                      foreground=self.text_light,
                      arrowcolor=self.accent_main,
                      borderwidth=0,
                      font=("Orbitron", 10))
        style.map("TCombobox",
                fieldbackground=[("readonly", self.bg_medium)],
                selectbackground=[("readonly", self.bg_light)])
        
        style.configure("TNotebook", 
                      background=self.bg_dark,
                      borderwidth=0)
        style.configure("TNotebook.Tab", 
                      background=self.bg_medium,
                      foreground=self.text_muted,
                      padding=(15, 5),
                      borderwidth=0,
                      font=("Orbitron", 10))
        style.map("TNotebook.Tab",
                background=[("selected", self.bg_light)],
                foreground=[("selected", self.text_light)],
                expand=[("selected", (0, 0, 0, 0))])
        
        style.configure("TLabelframe", 
                      background=self.bg_medium,
                      borderwidth=0,
                      relief="flat")
        style.configure("TLabelframe.Label", 
                      background=self.bg_dark,
                      foreground=self.text_light,
                      font=("Orbitron", 11, "bold"))
        
        style.configure("Vertical.TScrollbar", 
                      background=self.accent_main,  
                      arrowcolor=self.text_light,
                      borderwidth=0,
                      troughcolor=self.bg_medium)
        style.map("Vertical.TScrollbar",
                background=[("active", self.accent_hover), ("pressed", self.accent_hover)])

    def get_username(self):
        if 'SUDO_USER' in os.environ:
            return os.environ['SUDO_USER']
        elif 'USER' in os.environ:
            return os.environ['USER']
        else:
            try:
                import pwd
                return pwd.getpwuid(os.getuid()).pw_name
            except:
                return "unknown"

    def create_header(self):
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        title_label = ttk.Label(header_frame, text="CronGUI", style="Header.TLabel")
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = ttk.Label(header_frame, text="Easy Crontab Editor", style="SubHeader.TLabel")
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0))

    def create_top_controls(self):
        top_frame = ttk.Frame(self.content_frame)
        top_frame.pack(fill=tk.X, pady=(0, 15))
        
        # left side buttons
        left_buttons = ttk.Frame(top_frame)
        left_buttons.pack(side=tk.LEFT)
        
        # switched to tk.Button instead of ttk.Button for white borders
        refresh_btn = tk.Button(
            left_buttons, 
            text="↻ Refresh", 
            command=self.load_crontab,
            bg=self.bg_dark,
            fg=self.text_light,
            bd=2,                
            relief="solid",      
            highlightbackground=self.text_light,  
            highlightcolor=self.text_light,       
            activebackground=self.bg_dark,
            activeforeground=self.text_light,
            font=("Orbitron", 10, "bold"),
            padx=12,
            pady=6
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        add_btn = tk.Button(
            left_buttons, 
            text="+ New Entry", 
            command=self.add_new_entry,
            bg=self.bg_dark,
            fg=self.text_light,
            bd=2,
            relief="solid",
            highlightbackground=self.text_light, 
            highlightcolor=self.text_light,       
            activebackground=self.bg_dark,
            activeforeground=self.text_light,
            font=("Orbitron", 10, "bold"),
            padx=12,
            pady=6
        )
        add_btn.pack(side=tk.LEFT, padx=4)
        
        # buttons on the right
        right_buttons = ttk.Frame(top_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        help_btn = tk.Button(
            right_buttons, 
            text="Help", 
            command=self.show_help,
            bg=self.bg_dark,
            fg=self.text_light,
            bd=2,
            relief="solid",
            highlightbackground=self.text_light,  
            highlightcolor=self.text_light,       
            activebackground=self.bg_dark,
            activeforeground=self.text_light,
            font=("Orbitron", 10, "bold"),
            padx=12,
            pady=6
        )
        help_btn.pack(side=tk.LEFT, padx=4)
        
        save_btn = tk.Button(
            right_buttons, 
            text="Save Changes", 
            command=self.save_crontab,
            bg=self.bg_dark,
            fg=self.text_light,
            bd=2,
            relief="solid",
            highlightbackground=self.text_light,  
            highlightcolor=self.text_light,       
            activebackground=self.bg_dark,
            activeforeground=self.text_light,
            font=("Orbitron", 10, "bold"),
            padx=12,
            pady=6
        )
        save_btn.pack(side=tk.LEFT, padx=(4, 0))

    def create_entries_view(self):
        
        entries_frame = ttk.LabelFrame(
            self.content_frame, 
            text=" Current Crontab Entries ",
        )
        entries_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 25))
        
        # tree container
        tree_container = ttk.Frame(entries_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # treeview columns
        columns = ("schedule", "command", "comment")
        self.entries_tree = ttk.Treeview(
            tree_container, 
            columns=columns, 
            show="headings", 
            style="Treeview",
            height=5  
        )
        
        # headings
        self.entries_tree.heading("schedule", text="Schedule")
        self.entries_tree.heading("command", text="Command")
        self.entries_tree.heading("comment", text="Comment")
        
        # columns
        self.entries_tree.column("schedule", width=250, minwidth=180)
        self.entries_tree.column("command", width=650, minwidth=400)
        self.entries_tree.column("comment", width=320, minwidth=200)
        
        # scrollbar
        scrollbar = ttk.Scrollbar(
            tree_container, 
            orient=tk.VERTICAL, 
            command=self.entries_tree.yview
        )
        self.entries_tree.configure(yscrollcommand=scrollbar.set)
        
        # widgets
        self.entries_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # bindings
        self.entries_tree.bind("<<TreeviewSelect>>", self.on_entry_select)
        self.entries_tree.bind("<Button-3>", self.show_context_menu)

    def create_editor_section(self):
        self.editor_frame = ttk.LabelFrame(
            self.content_frame, 
            text=" Edit Entry ",
        )
        self.editor_frame.pack(fill=tk.BOTH, pady=(0, 25))
        
        # tabbed interface
        self.notebook = ttk.Notebook(self.editor_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=25, pady=25) 
        
        # basic editor tab
        basic_tab = ttk.Frame(self.notebook)
        self.notebook.add(basic_tab, text="Basic Editor")
        
        # time fields container 
        time_frame = ttk.Frame(basic_tab)
        time_frame.pack(fill=tk.X, pady=(35, 25), padx=25)  
        
        # define fields and values
        fields = ["Minute", "Hour", "Day", "Month", "Weekday"]
        field_values = {
            "Minute": ["*"] + [str(i) for i in range(0, 60, 5)],
            "Hour": ["*"] + [str(i) for i in range(24)],
            "Day": ["*"] + [str(i) for i in range(1, 32)],
            "Month": ["*", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"],
            "Weekday": ["*", "0 (Sun)", "1 (Mon)", "2 (Tue)", "3 (Wed)", "4 (Thu)", "5 (Fri)", "6 (Sat)"]
        }
        
        self.time_entries = {}
        
        # time field entries
        for i, field in enumerate(fields):
            field_container = ttk.Frame(time_frame)
            field_container.grid(row=0, column=i, padx=15, pady=10)  
            
            label = ttk.Label(field_container, text=field)
            label.pack(anchor=tk.W, pady=(0, 8))  
            
            combo = ttk.Combobox(
                field_container, 
                width=10,  
                values=field_values[field],
                style="TCombobox"
            )
            combo.pack(fill=tk.X, ipady=3) 
            combo.insert(0, "*")
            
            self.time_entries[field.lower()] = combo
        
        command_frame = ttk.Frame(basic_tab)
        command_frame.pack(fill=tk.X, pady=25, padx=25)  
        
        command_label = ttk.Label(command_frame, text="Command")
        command_label.pack(anchor=tk.W, pady=(0, 10))  
        
        self.command_entry = ttk.Entry(command_frame, style="TEntry")
        self.command_entry.pack(fill=tk.X, ipady=5)  
        
        comment_frame = ttk.Frame(basic_tab)
        comment_frame.pack(fill=tk.X, pady=25, padx=25)  
        
        comment_label = ttk.Label(comment_frame, text="Comment")
        comment_label.pack(anchor=tk.W, pady=(0, 10))  
        
        self.comment_entry = ttk.Entry(comment_frame, style="TEntry")
        self.comment_entry.pack(fill=tk.X, ipady=5)  
        
        advanced_tab = ttk.Frame(self.notebook)
        self.notebook.add(advanced_tab, text="Advanced")
        
        # raw container
        raw_container = ttk.Frame(advanced_tab)
        raw_container.pack(fill=tk.X, pady=15, padx=15)
        
        raw_label = ttk.Label(raw_container, text="Raw crontab entry:")
        raw_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.raw_entry = ttk.Entry(raw_container, style="TEntry")
        self.raw_entry.pack(fill=tk.X)
        
        # syntax help
        help_label = ttk.Label(
            advanced_tab, 
            text="Format: minute hour day month weekday command # comment",
            wraplength=600
        )
        help_label.pack(anchor=tk.W, padx=15, pady=10)
        
        # syntax explanation
        explanation_frame = ttk.Frame(advanced_tab)
        explanation_frame.pack(fill=tk.X, padx=15, pady=5)
        
        syntax_text = (
            "• minute (0-59)\n"
            "• hour (0-23)\n"
            "• day (1-31)\n"
            "• month (1-12)\n"
            "• weekday (0-6, 0=Sunday)\n\n"
            "Special characters: * (any), , (list), - (range), / (step)"
        )
        
        explanation = ttk.Label(
            explanation_frame, 
            text=syntax_text,
            justify=tk.LEFT,
            wraplength=600
        )
        explanation.pack(anchor=tk.W)
        
        # buttons
        buttons_frame = ttk.Frame(self.editor_frame)
        buttons_frame.pack(fill=tk.X, pady=10, padx=10)
        
        update_btn = tk.Button(
            buttons_frame, 
            text="Update Entry", 
            command=self.update_entry,
            bg=self.bg_dark,
            fg=self.text_light,
            bd=2,
            relief="solid",
            highlightbackground=self.text_light,  
            highlightcolor=self.text_light,       
            activebackground=self.bg_dark,
            activeforeground=self.text_light,
            font=("Orbitron", 10, "bold"),
            padx=12,
            pady=6
        )
        update_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(
            buttons_frame, 
            text="Clear Fields", 
            command=self.clear_fields,
            bg=self.bg_dark,
            fg=self.text_light,
            bd=2,
            relief="solid",
            highlightbackground=self.text_light, 
            highlightcolor=self.text_light,       
            activebackground=self.bg_dark,
            activeforeground=self.text_light,
            font=("Orbitron", 10, "bold"),
            padx=12,
            pady=6
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

    def create_status_bar(self):
        status_container = ttk.Frame(self.root, style="Container.TFrame")
        status_container.pack(side=tk.BOTTOM, fill=tk.X)
        
        status_frame = ttk.Frame(status_container, style="Container.TFrame")
        status_frame.pack(fill=tk.X, padx=15, pady=8)
        
        status_text = f"User: {self.current_user}"
        if not self.is_elevated:
            status_text += " (limited permissions)"
        
        status_label = ttk.Label(
            status_frame, 
            text=status_text,
            style="StatusBar.TLabel"
        )
        status_label.pack(side=tk.LEFT)
        
        # display the version
        version_label = ttk.Label(
            status_frame, 
            text="CronGUI v2.0",
            style="StatusBar.TLabel"
        )
        version_label.pack(side=tk.RIGHT)

        # might remove this now
    def apply_preset(self, schedule):
        parts = schedule.split()
        fields = ["minute", "hour", "day", "month", "weekday"]
        
        for i, field in enumerate(fields):
            self.time_entries[field].delete(0, tk.END)
            self.time_entries[field].insert(0, parts[i])
    
    def clear_fields(self):
        fields = ["minute", "hour", "day", "month", "weekday"]
        for field in fields:
            self.time_entries[field].delete(0, tk.END)
            self.time_entries[field].insert(0, "*")
        
        self.command_entry.delete(0, tk.END)
        self.comment_entry.delete(0, tk.END)
        self.raw_entry.delete(0, tk.END)
    
    def load_crontab(self):
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            
            if result.returncode != 0:
                if "no crontab" in result.stderr:
                    self.crontab_entries = []
                else:
                    messagebox.showerror("Error", f"Failed to load crontab: {result.stderr}")
                    return
            
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            self.crontab_entries = []
            
            for line in lines:
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                self.crontab_entries.append(line)
            
            self.update_entries_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def update_entries_display(self):
        # clear
        for item in self.entries_tree.get_children():
            self.entries_tree.delete(item)
        
        # add entries
        for i, entry in enumerate(self.crontab_entries):
            # comment check
            comment = ""
            if '#' in entry:
                entry_parts, comment = entry.split('#', 1)
                entry_parts = entry_parts.strip()
                comment = comment.strip()
            else:
                entry_parts = entry
            
            # split it
            parts = entry_parts.split(None, 5)
            
            if len(parts) >= 6:
                schedule = " ".join(parts[:5])
                command = parts[5]
            else:
                schedule = "Invalid schedule"
                command = entry_parts
            
            self.entries_tree.insert("", tk.END, values=(schedule, command, comment), iid=str(i))
    
    def on_entry_select(self, event):
        selected_items = self.entries_tree.selection()
        
        if not selected_items:
            return
        
        item_id = selected_items[0]
        entry = self.crontab_entries[int(item_id)]
        
        comment = ""
        if '#' in entry:
            entry_parts, comment = entry.split('#', 1)
            entry_parts = entry_parts.strip()
            comment = comment.strip()
        else:
            entry_parts = entry
        
        parts = entry_parts.split(None, 5)
        
        if len(parts) >= 6:
            fields = ["minute", "hour", "day", "month", "weekday"]
            for i, field in enumerate(fields):
                self.time_entries[field].delete(0, tk.END)
                self.time_entries[field].insert(0, parts[i])
            
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, parts[5])
            
            self.comment_entry.delete(0, tk.END)
            self.comment_entry.insert(0, comment)
            
            self.raw_entry.delete(0, tk.END)
            self.raw_entry.insert(0, entry_parts)
    
    def update_entry(self):
        selected_items = self.entries_tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Warning", "No entry selected to edit")
            return
        
        active_tab = self.notebook.index(self.notebook.select())
        
        if active_tab == 0:  
            # get values
            minute = self.time_entries["minute"].get()
            hour = self.time_entries["hour"].get()
            day = self.time_entries["day"].get()
            month = self.time_entries["month"].get()
            weekday = self.time_entries["weekday"].get()
            
            # remove the day name part from weekday if needed
            if '(' in weekday:
                weekday = weekday.split('(')[0].strip()
                
            command = self.command_entry.get()
            comment = self.comment_entry.get()
            
            # validation check
            if not (minute and hour and day and month and weekday and command):
                messagebox.showwarning("Warning", "All schedule fields and command are required")
                return
            
            # create it
            entry = f"{minute} {hour} {day} {month} {weekday} {command}"
            
        else: 
            entry = self.raw_entry.get()
            
            # check it's a valid entry
            if not entry or len(entry.split()) < 6:
                messagebox.showwarning("Warning", "Invalid crontab format. Need at least 6 components")
                return
            
            # get comment
            comment = self.comment_entry.get()
        
        # add comment
        if comment:
            entry = f"{entry} # {comment}"
        
        item_id = selected_items[0]
        self.crontab_entries[int(item_id)] = entry

        self.update_entries_display()
    
    def add_new_entry(self):
        # default new job
        self.crontab_entries.append("* * * * * echo 'New task'")
        
        self.update_entries_display()
        
        new_id = len(self.crontab_entries) - 1
        self.entries_tree.selection_set(str(new_id))
        self.entries_tree.see(str(new_id))
        
        self.on_entry_select(None)
        
    
    def show_context_menu(self, event):
        item = self.entries_tree.identify_row(event.y)
        
        if item:
            self.entries_tree.selection_set(item)
            
            # context menu
            context_menu = tk.Menu(self.root, tearoff=0, bg=self.bg_medium, fg=self.text_light)
            context_menu.add_command(label="Delete Entry", command=self.delete_selected_entry)
            context_menu.add_command(label="Duplicate Entry", command=self.duplicate_selected_entry)
            
            # display menu
            context_menu.post(event.x_root, event.y_root)
    
    def duplicate_selected_entry(self):
        selected_items = self.entries_tree.selection()
        
        if not selected_items:
            return
        
        item_id = selected_items[0]
        index = int(item_id)
        
        # dupes
        self.crontab_entries.append(self.crontab_entries[index])
        
        self.update_entries_display()
        
        new_id = len(self.crontab_entries) - 1
        self.entries_tree.selection_set(str(new_id))
        self.entries_tree.see(str(new_id))
    
    def delete_selected_entry(self):
        selected_items = self.entries_tree.selection()
        
        if not selected_items:
            return
        
        # confirm delete
        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this cron job?",
            icon='warning'
        )
        
        if confirm:
            item_id = selected_items[0]
            index = int(item_id)
            
            del self.crontab_entries[index]
            
            self.update_entries_display()

    def show_help(self):
        """Show help dialog with crontab syntax information"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Cron Syntax Help")
        help_window.geometry("600x500")
        help_window.configure(bg=self.bg_dark)
        help_window.resizable(True, True)
        
        container = ttk.Frame(help_window)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_label = ttk.Label(
            container, 
            text="Cron Syntax Reference",
            style="Header.TLabel"
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        help_notebook = ttk.Notebook(container)
        help_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # basic syntax tab
        syntax_tab = ttk.Frame(help_notebook)
        help_notebook.add(syntax_tab, text="Basic Syntax")
        
        syntax_content = """
Time Fields:
• Minute (0-59)
• Hour (0-23)
• Day of month (1-31)
• Month (1-12)
• Day of week (0-6, 0=Sunday)

Special Characters:
• * : Matches all values
• , : Separates multiple values (1,3,5)
• - : Defines a range (i.e 1-5)
• / : Defines step values (*/15 = every 15 units)
        """
        
        syntax_label = ttk.Label(
            syntax_tab, 
            text=syntax_content,
            justify=tk.LEFT,
            wraplength=550
        )
        syntax_label.pack(anchor=tk.W, padx=10, pady=10, fill=tk.BOTH)
        
        # examples
        examples_tab = ttk.Frame(help_notebook)
        help_notebook.add(examples_tab, text="Examples")
        
        examples_content = """
Examples:
• 0 * * * * - Run at the start of every hour
• */15 * * * * - Run every 15 minutes
• 0 0 * * * - Run daily at midnight
• 0 0 * * 0 - Run at midnight on Sundays
• 0 0 1 * * - Run at midnight on the first day of each month
• 0 8-17 * * 1-5 - Run hourly from 8 AM to 5 PM on weekdays
• 0 0,12 * * * - Run at midnight and noon every day
• 30 9 * * 1,3,5 - Run at 9:30 AM on Monday, Wednesday, and Friday
        """
        
        examples_label = ttk.Label(
            examples_tab, 
            text=examples_content,
            justify=tk.LEFT,
            wraplength=550
        )
        examples_label.pack(anchor=tk.W, padx=10, pady=10, fill=tk.BOTH)
        
        # Tips tab
        tips_tab = ttk.Frame(help_notebook)
        help_notebook.add(tips_tab, text="Tips")
        
        tips_content = """
Best Practices:
• Use good cooments
• Run resource heavy jobs at appropriate times
• Output to log files for debugging (for example: command > /path/to/log 2>&1)
• Use absolute paths for commands and scripts!!

Environment Variables:
When a cron job runs, it uses a minimal environment. If your commands require specific environment variables, you should set them in the crontab or within your scripts.
        """
        
        tips_label = ttk.Label(
            tips_tab, 
            text=tips_content,
            justify=tk.LEFT,
            wraplength=550
        )
        tips_label.pack(anchor=tk.W, padx=10, pady=10, fill=tk.BOTH)
        
        close_btn = tk.Button(
            container, 
            text="Close", 
            command=help_window.destroy,
            bg=self.bg_dark,
            fg=self.text_light,
            bd=2,
            relief="solid",
            highlightbackground=self.text_light,  
            highlightcolor=self.text_light,       
            activebackground=self.bg_dark,
            activeforeground=self.text_light,
            font=("Orbitron", 10, "bold"),
            padx=12,
            pady=6
        )
        close_btn.pack(pady=(10, 0))

    def save_crontab(self):
        try:
            # create a temp file with the entries
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                for entry in self.crontab_entries:
                    temp_file.write(f"{entry}\n")
                temp_file_name = temp_file.name
            
            # use the temp file to update crontab
            result = subprocess.run(["crontab", temp_file_name], capture_output=True, text=True)
            
            # clean up temp file
            os.unlink(temp_file_name)
            
            if result.returncode == 0:
                messagebox.showinfo(
                    "Success", 
                    "Crontab updated successfully",
                    icon='info'
                )
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                messagebox.showerror(
                    "Error", 
                    f"Failed to update crontab: {error_msg}",
                    icon='error'
                )
                
                if not self.is_elevated:
                    messagebox.showinfo(
                        "Permission Issue", 
                        "You don't have permissions to edit.\n"
                        "Try running with sudo or as root.",
                        icon='warning'
                    )
        
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"An error occurred: {str(e)}",
                icon='error'
            )


def main():
    # create the root window
    root = tk.Tk()
    
    # init the app
    app = ModernCronGUI(root)
    
    # window behavior
    root.protocol("WM_DELETE_WINDOW", lambda: root.destroy())
    
    # for macs
    if sys.platform == 'darwin':  
        root.createcommand('tkAboutDialog', lambda: messagebox.showinfo(
            "About CronGUI",
            "CronGUI v2.0\n\nA simple GUI editor"
        ))
    
    # let's go!
    root.mainloop()


if __name__ == "__main__":
    main()