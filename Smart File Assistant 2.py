#Import libraries
#Used for reading file paths and stats.
import os
#Used for handling dates and times.
import datetime
#Used for saving and loading the state log.
import json
#Used for safely moving files.
import shutil
#The main library for creating the GUI.
import tkinter as tk
#Import specific GUI components we need.
from tkinter import filedialog, scrolledtext, messagebox, Entry

#Configuration
#The size in MB to consider a file "large".
LARGE_FILE_MB = 50
#The age in days to consider a file "old".
OLD_FILE_DAYS = 365
#The name of the log file.
STATE_FILE_NAME = "smart_assistant_state.json"

#Core Logic Functions
def load_state(folder_path):
    """Loads the last saved state for a specific folder from the JSON log file."""
    state_file_path = os.path.join(folder_path, STATE_FILE_NAME)
    if not os.path.exists(state_file_path):
        return {}
    try:
        with open(state_file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_state(folder_path, state_data):
    """Saves the current state of the folder to the JSON log file."""
    state_file_path = os.path.join(folder_path, STATE_FILE_NAME)
    try:
        with open(state_file_path, 'w') as f:
            json.dump(state_data, f, indent=4)
    except IOError as e:
        print(f"Error: Could not save state file. Reason: {e}")


def analyze_folder(folder_path):
    """Scans a folder and returns its current state."""
    current_state = {}
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if file_name == STATE_FILE_NAME:
                continue
            file_path = os.path.join(root, file_name)
            try:
                stats = os.stat(file_path)
                current_state[file_path] = {
                    'size': stats.st_size,
                    'last_modified': stats.st_mtime
                }
            except FileNotFoundError:
                continue
    return current_state


def detect_changes(old_state, new_state):
    """Compares two states to find added, deleted, and modified files."""
    old_files, new_files = set(old_state.keys()), set(new_state.keys())
    added = list(new_files - old_files)
    deleted = list(old_files - new_files)
    modified = [p for p in new_files.intersection(old_files) if
                old_state[p]['last_modified'] != new_state[p]['last_modified']]
    return added, deleted, modified


def get_files_to_archive(new_state):
    """This is the AI function. It identifies the *paths* of files that meet the archive criteria.This is used by the "Archive" button."""
    #Create an empty set to store the paths of files to archive, using a set avoids duplicates.
    files_to_move = set()
    #Get the current time for comparison.
    now = datetime.datetime.now()
    #Loop through all the files in the current state.
    for file_path, file_data in new_state.items():
        #Check if the file is large.
        if (file_data['size'] / (1024 * 1024)) > LARGE_FILE_MB:
            #If it is, add its path to our set.
            files_to_move.add(file_path)
        #Check if the file is old.
        last_modified_date = datetime.datetime.fromtimestamp(file_data['last_modified'])
        if (now - last_modified_date).days > OLD_FILE_DAYS:
            #If it is, add its path to our set.
            files_to_move.add(file_path)
    #Return the files to be moved as a list.
    return list(files_to_move)


def generate_report_text(changes, state, recommendations):
    """Generates the full report text to be displayed in the GUI."""
    added, deleted, modified = changes
    report_lines = [
        "--- Smart File Assistant Report ---",
        f"\nFound {len(state)} files in total.\n",
        "--- File Changes Since Last Scan ---"
    ]
    if not any(changes):
        report_lines.append("No changes since the last scan.")
    else:
        report_lines.extend(
            [f"\nAdded ({len(added)}):"] + ([f"  + {os.path.basename(p)}" for p in added] or ["  (None)"]))
        report_lines.extend(
            [f"\nDeleted ({len(deleted)}):"] + ([f"  - {os.path.basename(p)}" for p in deleted] or ["  (None)"]))
        report_lines.extend(
            [f"\nModified ({len(modified)}):"] + ([f"  ~ {os.path.basename(p)}" for p in modified] or ["  (None)"]))

    report_lines.append("\n\n--- Recommendations (Based on Current Files) ---")
    if not recommendations:
        report_lines.append("No specific recommendations at this time.")
    else:
        report_lines.extend([f"- {rec}" for rec in recommendations])

    report_lines.append("\n\n--- Detailed File List ---")
    #Sort the state by file path for consistent display.
    sorted_files = sorted(state.items())
    for path, data in sorted_files:
        size_mb = data['size'] / (1024 * 1024)
        modified_date = datetime.datetime.fromtimestamp(data['last_modified']).strftime('%Y-%m-%d')
        report_lines.append(f"{os.path.basename(path):<40} | Size: {size_mb:7.2f} MB | Modified: {modified_date}")

    report_lines.append("\n--- End of Report ---")
    return "\n".join(report_lines)


#GUI Application Class
class App:
    def __init__(self, root):
        #Store the main window.
        self.root = root
        #Set the window title.
        self.root.title("Smart File Assistant")
        #Set a larger default size for the new features.
        self.root.geometry("900x700")
        #Variable to store the path of the selected folder.
        self.folder_path = ""
        #Variable to hold the results of the last full scan.
        self.full_state = {}

        #Frame for Folder Selection
        top_frame = tk.Frame(root, padx=10, pady=5)
        top_frame.pack(fill='x')
        self.select_button = tk.Button(top_frame, text="1. Select Folder to Scan", command=self.select_folder)
        self.select_button.pack(side='left', padx=5)
        self.folder_label = tk.Label(top_frame, text="No folder selected", fg="blue")
        self.folder_label.pack(side='left', padx=5)

        #Main Action Frame
        action_frame = tk.Frame(root, padx=10, pady=5)
        action_frame.pack(fill='x')
        self.run_button = tk.Button(action_frame, text="2. Run Full Analysis", command=self.run_analysis,
                                    state='disabled', font=('Helvetica', 10, 'bold'))
        self.run_button.pack(side='left', padx=5)
        #Create the "Archive" button. It starts disabled.
        self.archive_button = tk.Button(action_frame, text="Archive Recommended Files", command=self.archive_files,
                                        state='disabled')
        self.archive_button.pack(side='left', padx=20)

        #Interactive for search and sort.
        query_frame = tk.Frame(root, padx=10, pady=10)
        query_frame.pack(fill='x')
        #Create a label for the search bar.
        tk.Label(query_frame, text="Search by Name:").pack(side='left')
        #Create a text box for typing.
        self.search_entry = Entry(query_frame, width=30)
        self.search_entry.pack(side='left', padx=5)
        #Create the "Search" button. It starts disabled.
        self.search_button = tk.Button(query_frame, text="Search", command=self.search_files, state='disabled')
        self.search_button.pack(side='left')
        #Create the "Sort" button. It starts disabled.
        self.sort_button = tk.Button(query_frame, text="Sort by Extension", command=self.sort_files, state='disabled')
        self.sort_button.pack(side='left', padx=20)
        #Create a "Clear" button to reset the view. It starts disabled.
        self.clear_button = tk.Button(query_frame, text="Clear Filter/Sort", command=self.clear_filter,
                                      state='disabled')
        self.clear_button.pack(side='left')

        #Report Area
        #Create a text area to display all output.
        self.report_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier New", 10))
        self.report_area.pack(pady=10, padx=10, fill="both", expand=True)

    def select_folder(self):
        """Called when the 'Select Folder' button is clicked."""
        path = filedialog.askdirectory()
        if path:
            self.folder_path = path
            self.folder_label.config(text=f"Selected: {path}")
            #Enable the main run button.
            self.run_button.config(state='normal')
            #Disable other buttons until a scan is complete.
            self.archive_button.config(state='disabled')
            self.search_button.config(state='disabled')
            self.sort_button.config(state='disabled')
            self.clear_button.config(state='disabled')

    def run_analysis(self):
        """Orchestrates the entire scan and report process."""
        if not self.folder_path: return

        self.report_area.delete(1.0, tk.END)
        self.report_area.insert(tk.END, f"Scanning {self.folder_path}...")
        self.root.update_idletasks()

        #Execute the core logic.
        old_state = load_state(self.folder_path)
        new_state = analyze_folder(self.folder_path)
        #Save the full results for interactive queries.
        self.full_state = new_state
        changes = detect_changes(old_state, new_state)

        #AI part: get recommendations based on the scan.
        recommendations = self.get_recommendations_text(new_state)

        #Generate and display the report.
        report_text = generate_report_text(changes, new_state, recommendations)
        self.display_report(report_text)

        #Save the new state for the next time.
        save_state(self.folder_path, new_state)

        #Enable all buttons after we have data.
        self.archive_button.config(state='normal')
        self.search_button.config(state='normal')
        self.sort_button.config(state='normal')
        self.clear_button.config(state='normal')

    def search_files(self):
        """Filters the displayed file list based on the search term."""
        #Get the search term from the entry box.
        search_term = self.search_entry.get().lower()
        #Do nothing if the search box is empty.
        if not search_term: return
        #Create a new dictionary containing only files that match the search term.
        filtered_state = {path: data for path, data in self.full_state.items() if
                          search_term in os.path.basename(path).lower()}
        #Generate a new report for the filtered files.
        report_text = generate_report_text(([], [], []), filtered_state, [])  # No changes or recs in this view.
        self.display_report(f"--- Search Results for '{search_term}' ---\n\n" + report_text)

    def sort_files(self):
        """Sorts the displayed file list by file extension."""
        #'sorted' can take a 'key' function. Here, we use a lambda to tell it to sort by the extension.
        #os.path.splitext('/path/to/file.txt') returns ('/path/to/file', '.txt'). We sort by the second part.
        sorted_state = dict(sorted(self.full_state.items(), key=lambda item: os.path.splitext(item[0])[1]))
        report_text = generate_report_text(([], [], []), sorted_state, [])
        self.display_report("--- Files Sorted by Extension ---\n\n" + report_text)

    def clear_filter(self):
        """Resets the view to the last full analysis report."""
        #Just re-run the report generation with the saved full state.
        recommendations = self.get_recommendations_text(self.full_state)
        report_text = generate_report_text(([], [], []), self.full_state, recommendations)
        self.display_report(report_text)
        self.search_entry.delete(0, tk.END)  # Clear the search box.

    def archive_files(self):
        """Moves all recommended files to a user-selected archive folder."""
        #First, identify which files need to be moved using our AI helper function [2].
        files_to_move = get_files_to_archive(self.full_state)
        if not files_to_move:
            messagebox.showinfo("Archive Files", "No old or large files to archive were found.")
            return

        #Ask user to confirm.
        if not messagebox.askyesno("Confirm Archive",
                                   f"Found {len(files_to_move)} files to archive. Do you want to proceed?"):
            return

        #Ask user to select an archive destination folder.
        archive_path = filedialog.askdirectory(title="Select a folder to move files into")
        if not archive_path: return  # Stop if the user cancels.

        #Move the files.
        moved_count = 0
        for file_path in files_to_move:
            try:
                # 'shutil.move' safely moves a file from a source to a destination.
                shutil.move(file_path, archive_path)
                moved_count += 1
            except Exception as e:
                print(f"Could not move {file_path}. Reason: {e}")

        #Show a final confirmation message.
        messagebox.showinfo("Archive Complete", f"Successfully moved {moved_count} out of {len(files_to_move)} files.")

        #Automatically run the analysis again to show the updated folder state.
        self.run_analysis()

    def get_recommendations_text(self, state):
        """Helper to generate just the recommendation text list."""
        recommendations = []
        now = datetime.datetime.now()
        for path, data in state.items():
            size_mb = data['size'] / (1024 * 1024)
            if size_mb > LARGE_FILE_MB:
                recommendations.append(
                    f"Large File: '{os.path.basename(path)}' ({size_mb:.2f} MB). Consider archiving.")
            last_mod = datetime.datetime.fromtimestamp(data['last_modified'])
            if (now - last_mod).days > OLD_FILE_DAYS:
                recommendations.append(
                    f"Old File: '{os.path.basename(path)}' (Modified {(now - last_mod).days} days ago). Consider archiving.")
        return recommendations

    def display_report(self, report_text):
        """A helper method to safely update the report area text."""
        #Make it editable.
        self.report_area.config(state='normal')
        #Clear previous content.
        self.report_area.delete(1.0, tk.END)
        #Insert new content.
        self.report_area.insert(tk.END, report_text)
        #Make it read-only for the user.
        self.report_area.config(state='disabled')


#Main entry point of the script
if __name__ == "__main__":
    #Create the main window.
    main_window = tk.Tk()
    #Create the App, which builds the GUI.
    app = App(main_window)
    #Start the GUI event loop.
    main_window.mainloop()