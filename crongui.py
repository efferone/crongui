import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import re
import os
import sys
import tempfile

class CrontabEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("CronGUI - Crontab Editor")
        self.root.geometry("900x750")

        # Apply the dark blue theme
        self.apply_dark_blue_theme()

        # Check if running as root or with sudo
        self.is_elevated = os.geteuid() == 0

        # Initialize crontab entries and username
        self.crontab_entries = []
        self.current_user = self.get_username()

        # main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # top controls
        self.create_top_controls()

        # entries frame
        self.create_entries_frame()

        # editor frame
        self.create_editor_frame()

        # getcrontab entries
        self.load_crontab()

        # adding a status bar
        self.create_status_bar()

    def apply_dark_blue_theme(self):
        """dark blue 4tw"""
        self.root.configure(bg="#2B2B52")  # Dark blue background for the main window

        # Style ttk widgets 
        style = ttk.Style(self.root)
        style.configure("TFrame", background="#2B2B52")
        style.configure("TLabel", background="#2B2B52", foreground="white")
        style.configure("TButton",
                        background="#4834D4",
                        foreground="white",
                        relief="flat",
                        padding=6)
        style.map("TButton",
                  background=[("active", "#5F4B8B")],  # Slightly lighter colour on hover
                  relief=[("active", "groove")])

        # Treeview config, not sure if gonna use yet
        style.configure("Treeview",
                        background="#3B3B6B",
                        foreground="white")
        style.map("Treeview",
                  background=[("selected", "#4834D4")])

    def get_username(self):
        """Get the actual username even when run with sudo"""
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

    def create_status_bar(self):
        """Create a status bar at the bottom"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=2)

        # display current user permissions
        status_text = f"User: {self.current_user}"
        if not self.is_elevated:
            status_text += " (Limited permissions - some operations may fail)"

        status_label = ttk.Label(status_frame, text=status_text)
        status_label.pack(side=tk.LEFT, padx=5)

    def create_top_controls(self):
        """Create top control buttons"""
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        refresh_btn = ttk.Button(top_frame, text="Refresh", command=self.load_crontab)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        add_btn = ttk.Button(top_frame, text="Add New Entry", command=self.add_new_entry)
        add_btn.pack(side=tk.LEFT, padx=5)

        save_btn = ttk.Button(top_frame, text="Save Changes", command=self.save_crontab)
        save_btn.pack(side=tk.RIGHT, padx=5)

        # help button, set up below
        help_btn = ttk.Button(top_frame, text="Help", command=self.show_help)
        help_btn.pack(side=tk.RIGHT, padx=5)

    
    def show_help(self):
        """Show help dialog with crontab syntax information"""
        help_text = """
Crontab Syntax Help:

Time Fields Format:
* Minute (0-59)
* Hour (0-23)
* Day of month (1-31)
* Month (1-12)
* Day of week (0-6, 0=Sunday)

Special Characters:
* Asterisk (*): Matches all values
* Comma (,): Separate multiple values
* Hyphen (-): Range of values
* Slash (/): Step values

Examples:
* "0 12 * * *" - Run at noon every day
* "*/15 * * * *" - Run every 15 minutes
* "0 0 * * 0" - Run at midnight on Sundays
* "0 6,18 * * 1-5" - Run at 6am and 6pm on weekdays
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Crontab Syntax Help")
        help_window.geometry("500x400")
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        close_btn = ttk.Button(help_window, text="Close", command=help_window.destroy)
        close_btn.pack(pady=10)
    
    def create_entries_frame(self):
        """Create the frame that displays crontab entries"""
        entries_frame = ttk.LabelFrame(self.main_frame, text="Current Crontab Entries")
        entries_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # let's make a treeview for displaying entries
        columns = ("schedule", "command", "comment")
        self.entries_tree = ttk.Treeview(entries_frame, columns=columns, show="headings")
        
        #  headings
        self.entries_tree.heading("schedule", text="Schedule")
        self.entries_tree.heading("command", text="Command")
        self.entries_tree.heading("comment", text="Comment")
        
        # columns
        self.entries_tree.column("schedule", width=200)
        self.entries_tree.column("command", width=350)
        self.entries_tree.column("comment", width=150)
        
        # scrollbar
        scrollbar = ttk.Scrollbar(entries_frame, orient=tk.VERTICAL, command=self.entries_tree.yview)
        self.entries_tree.configure(yscrollcommand=scrollbar.set)
        
        # widgets
        self.entries_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.entries_tree.bind("<<TreeviewSelect>>", self.on_entry_select)
        
        # Add a delete function on right-click
        self.entries_tree.bind("<Button-3>", self.show_context_menu)
    
    def create_editor_frame(self):
        """Create the frame for editing a crontab entry"""
        self.editor_frame = ttk.LabelFrame(self.main_frame, text="Edit Entry")
        self.editor_frame.pack(fill=tk.BOTH, pady=5)
        
        # tabs for basic and advanced editing
        self.notebook = ttk.Notebook(self.editor_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Basic editor tab
        basic_tab = ttk.Frame(self.notebook)
        self.notebook.add(basic_tab, text="Basic")
        
        # Create fields for time components
        time_frame = ttk.Frame(basic_tab)
        time_frame.pack(fill=tk.X, pady=5)
        
        # Labels for crontab time fields
        fields = ["Minute", "Hour", "Day", "Month", "Weekday"]
        field_values = {
            "Minute": ["*"] + [str(i) for i in range(0, 60, 5)],
            "Hour": ["*"] + [str(i) for i in range(24)],
            "Day": ["*"] + [str(i) for i in range(1, 32)],
            "Month": ["*", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"],
            "Weekday": ["*", "0 (Sun)", "1 (Mon)", "2 (Tue)", "3 (Wed)", "4 (Thu)", "5 (Fri)", "6 (Sat)"]
        }
        
        self.time_entries = {}
        
        for i, field in enumerate(fields):
            label = ttk.Label(time_frame, text=field)
            label.grid(row=0, column=i, padx=5, pady=5)
            
            # Create combobox with common values
            combo = ttk.Combobox(time_frame, width=8, values=field_values[field])
            combo.grid(row=1, column=i, padx=5, pady=5)
            combo.insert(0, "*")  # Default value
            
            self.time_entries[field.lower()] = combo
        
        # Command entry
        command_frame = ttk.Frame(basic_tab)
        command_frame.pack(fill=tk.X, pady=5)
        
        command_label = ttk.Label(command_frame, text="Command")
        command_label.pack(side=tk.LEFT, padx=5)
        
        self.command_entry = ttk.Entry(command_frame)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Comment entry
        comment_frame = ttk.Frame(basic_tab)
        comment_frame.pack(fill=tk.X, pady=5)
        
        comment_label = ttk.Label(comment_frame, text="Comment")
        comment_label.pack(side=tk.LEFT, padx=5)
        
        self.comment_entry = ttk.Entry(comment_frame)
        self.comment_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Common presets
        presets_frame = ttk.LabelFrame(basic_tab, text="Common Schedules")
        presets_frame.pack(fill=tk.X, pady=10)
        
        presets = [
            ("Every hour", "0 * * * *"),
            ("Every day at midnight", "0 0 * * *"),
            ("Every weekday at 8am", "0 8 * * 1-5"),
            ("Every 15 minutes", "*/15 * * * *"),
            ("First of month", "0 0 1 * *")
        ]
        
        for i, (name, schedule) in enumerate(presets):
            btn = ttk.Button(presets_frame, text=name, 
                            command=lambda s=schedule: self.apply_preset(s))
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="ew")
        
        # Advanced editor tab
        advanced_tab = ttk.Frame(self.notebook)
        self.notebook.add(advanced_tab, text="Advanced")
        
        # Raw crontab entry
        raw_label = ttk.Label(advanced_tab, text="Raw crontab entry:")
        raw_label.pack(anchor=tk.W, padx=5, pady=5)
        
        self.raw_entry = ttk.Entry(advanced_tab)
        self.raw_entry.pack(fill=tk.X, padx=5, expand=False)
        
        # Add explanation text
        explanation = ttk.Label(advanced_tab, text="Format: minute hour day month weekday command # comment",
                             wraplength=700)
        explanation.pack(anchor=tk.W, padx=5, pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.editor_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        update_btn = ttk.Button(buttons_frame, text="Update Entry", command=self.update_entry)
        update_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(buttons_frame, text="Clear Fields", command=self.clear_fields)
        clear_btn.pack(side=tk.LEFT, padx=5)
    
    def apply_preset(self, schedule):
        """Apply a preset schedule"""
        parts = schedule.split()
        fields = ["minute", "hour", "day", "month", "weekday"]
        
        for i, field in enumerate(fields):
            self.time_entries[field].delete(0, tk.END)
            self.time_entries[field].insert(0, parts[i])
    
    def clear_fields(self):
        """Clear all input fields"""
        fields = ["minute", "hour", "day", "month", "weekday"]
        for field in fields:
            self.time_entries[field].delete(0, tk.END)
            self.time_entries[field].insert(0, "*")
        
        self.command_entry.delete(0, tk.END)
        self.comment_entry.delete(0, tk.END)
        self.raw_entry.delete(0, tk.END)
    
    def load_crontab(self):
        """Load current crontab entries"""
        try:
            # Run the crontab -l command
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            
            if result.returncode != 0:
                # If user has no crontab, this is not an error
                if "no crontab" in result.stderr:
                    self.crontab_entries = []
                else:
                    messagebox.showerror("Error", f"Failed to load crontab: {result.stderr}")
                    return
            
            # Parse the output
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            self.crontab_entries = []
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Skip comments but not inline comments
                if line.startswith('#'):
                    continue
                
                # Add to our entries list
                self.crontab_entries.append(line)
            
            # Update the UI
            self.update_entries_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def update_entries_display(self):
        """Update the treeview with current entries"""
        # Clear the treeview
        for item in self.entries_tree.get_children():
            self.entries_tree.delete(item)
        
        # Add entries to the treeview
        for i, entry in enumerate(self.crontab_entries):
            # Check for inline comments
            comment = ""
            if '#' in entry:
                entry_parts, comment = entry.split('#', 1)
                entry_parts = entry_parts.strip()
                comment = comment.strip()
            else:
                entry_parts = entry
            
            # Split entry into schedule and command
            parts = entry_parts.split(None, 5)  # Split at most 5 times
            
            if len(parts) >= 6:
                schedule = " ".join(parts[:5])
                command = parts[5]
            else:
                schedule = "Invalid format"
                command = entry_parts
            
            self.entries_tree.insert("", tk.END, values=(schedule, command, comment), iid=str(i))
    
    def on_entry_select(self, event):
        """Handle selection of an entry in the treeview"""
        selected_items = self.entries_tree.selection()
        
        if not selected_items:
            return
        
        # Get the selected entry
        item_id = selected_items[0]
        entry = self.crontab_entries[int(item_id)]
        
        # Check for inline comments
        comment = ""
        if '#' in entry:
            entry_parts, comment = entry.split('#', 1)
            entry_parts = entry_parts.strip()
            comment = comment.strip()
        else:
            entry_parts = entry
        
        # Parse the entry
        parts = entry_parts.split(None, 5)  # Split at most 5 times
        
        if len(parts) >= 6:
            # Fill the time entries
            fields = ["minute", "hour", "day", "month", "weekday"]
            for i, field in enumerate(fields):
                self.time_entries[field].delete(0, tk.END)
                self.time_entries[field].insert(0, parts[i])
            
            # Fill the command entry
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, parts[5])
            
            # Fill the comment entry
            self.comment_entry.delete(0, tk.END)
            self.comment_entry.insert(0, comment)
            
            # Fill the raw entry
            self.raw_entry.delete(0, tk.END)
            self.raw_entry.insert(0, entry_parts)
    
    def update_entry(self):
        """Update the selected entry with values from editor"""
        selected_items = self.entries_tree.selection()
        
        if not selected_items:
            messagebox.showwarning("Warning", "No entry selected")
            return
        
        # Get current active tab
        active_tab = self.notebook.index(self.notebook.select())
        
        if active_tab == 0:  # Basic tab
            # Get the values from the editor
            minute = self.time_entries["minute"].get()
            hour = self.time_entries["hour"].get()
            day = self.time_entries["day"].get()
            month = self.time_entries["month"].get()
            weekday = self.time_entries["weekday"].get()
            
            # Remove the day name part from weekday if present
            if '(' in weekday:
                weekday = weekday.split('(')[0].strip()
                
            command = self.command_entry.get()
            comment = self.comment_entry.get()
            
            # Validate input (very basic validation)
            if not (minute and hour and day and month and weekday and command):
                messagebox.showwarning("Warning", "All schedule fields and command are required")
                return
            
            # Create the crontab entry
            entry = f"{minute} {hour} {day} {month} {weekday} {command}"
            
        else:  # Advanced tab
            entry = self.raw_entry.get()
            
            # Simple validation
            if not entry or len(entry.split()) < 6:
                messagebox.showwarning("Warning", "Invalid crontab format. Need at least 6 components (5 time fields + command)")
                return
            
            # Extract comment from basic tab
            comment = self.comment_entry.get()
        
        # Add comment if present
        if comment:
            entry = f"{entry} # {comment}"
        
        # Update the entry in our list
        item_id = selected_items[0]
        self.crontab_entries[int(item_id)] = entry
        
        # Update the display
        self.update_entries_display()
    
    def add_new_entry(self):
        """Add a new empty entry"""
        # Add a default entry
        self.crontab_entries.append("0 0 * * * echo 'New task'")
        
        # Update the display
        self.update_entries_display()
        
        # Select the new entry
        new_id = len(self.crontab_entries) - 1
        self.entries_tree.selection_set(str(new_id))
        
        # Trigger the selection event
        self.on_entry_select(None)
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Get the item under cursor
        item = self.entries_tree.identify_row(event.y)
        
        if item:
            # Select the item
            self.entries_tree.selection_set(item)
            
            # Create a context menu
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Delete", command=self.delete_selected_entry)
            context_menu.add_command(label="Duplicate", command=self.duplicate_selected_entry)
            
            # Display the context menu
            context_menu.post(event.x_root, event.y_root)
    
    def duplicate_selected_entry(self):
        """Duplicate the selected entry"""
        selected_items = self.entries_tree.selection()
        
        if not selected_items:
            return
        
        item_id = selected_items[0]
        index = int(item_id)
        
        # Duplicate the entry
        self.crontab_entries.append(self.crontab_entries[index])
        
        # Update the display
        self.update_entries_display()
        
        # Select the new entry
        new_id = len(self.crontab_entries) - 1
        self.entries_tree.selection_set(str(new_id))
    
    def delete_selected_entry(self):
        """Delete the selected entry"""
        selected_items = self.entries_tree.selection()
        
        if not selected_items:
            return
        
        item_id = selected_items[0]
        index = int(item_id)
        
        # Remove the entry from our list
        del self.crontab_entries[index]
        
        # Update the display
        self.update_entries_display()
    
    def save_crontab(self):
        """Save the current entries back to crontab"""
        try:
            # Create a temporary file with our entries
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                for entry in self.crontab_entries:
                    temp_file.write(f"{entry}\n")
                temp_file_name = temp_file.name
            
            # Use the temporary file to update crontab
            result = subprocess.run(["crontab", temp_file_name], capture_output=True, text=True)
            
            # Clean up the temporary file
            os.unlink(temp_file_name)
            
            if result.returncode == 0:
                messagebox.showinfo("Success", "Crontab updated successfully")
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                messagebox.showerror("Error", f"Failed to update crontab: {error_msg}")
                
                if not self.is_elevated:
                    messagebox.showinfo("Permission Issue", 
                                    "You may need to run this application with elevated privileges.\n"
                                    "Try running with sudo or as root.")
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

def main():
    root = tk.Tk()
    app = CrontabEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
