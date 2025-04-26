import tkinter as tk
from tkinter import (
    ttk,
    scrolledtext,
    messagebox,
    Listbox,
    END,
    Label,
)
import os
import glob
import re
import html
from PIL import Image, ImageTk
import datetime
from markdown_it import MarkdownIt 


class JournalAuthorApp:
    def __init__(self, master):
        self.master = master
        master.title("Journal Entry Authoring Tool")
        master.geometry("950x880")  # Increased height slightly more

        input_frame = ttk.LabelFrame(master, text="Entry Details")
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(input_frame, text="Member:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.member_var = tk.StringVar()

        self.member_combobox = ttk.Combobox(
            input_frame,
            textvariable=self.member_var,
            values=["1", "2", "3", "4"],
            width=3,
            state="readonly",
        )
        self.member_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.member_combobox.set("1")  # Default to member 1

        ttk.Label(input_frame, text="Week:").grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.W
        )
        self.week_var = tk.StringVar()
        self.week_entry = ttk.Entry(input_frame, textvariable=self.week_var, width=5)
        self.week_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

        ttk.Label(input_frame, text="Entry:").grid(
            row=0, column=4, padx=5, pady=5, sticky=tk.W
        )
        self.entry_var = tk.StringVar()
        self.entry_entry = ttk.Entry(input_frame, textvariable=self.entry_var, width=5)
        self.entry_entry.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)

        self.find_images_button = ttk.Button(
            input_frame, text="Find Images", command=self.find_images
        )
        self.find_images_button.grid(row=0, column=6, padx=10, pady=5, sticky=tk.W)

        ttk.Label(input_frame, text="Date:").grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.W
        )
        self.date_var = tk.StringVar()
        self.date_var.set(datetime.date.today().strftime("%B %d"))
        self.date_entry = ttk.Entry(input_frame, textvariable=self.date_var, width=20)
        self.date_entry.grid(
            row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W
        )  # Span 2

        ttk.Label(input_frame, text="Start Time:").grid(
            row=1, column=3, padx=5, pady=5, sticky=tk.W
        )  # Shifted right
        self.start_time_var = tk.StringVar()
        self.start_time_entry = ttk.Entry(
            input_frame, textvariable=self.start_time_var, width=10
        )
        self.start_time_entry.grid(
            row=1, column=4, padx=5, pady=5, sticky=tk.W
        )  # Shifted right

        ttk.Label(input_frame, text="Duration (hrs):").grid(
            row=1, column=5, padx=5, pady=5, sticky=tk.W
        )  # Shifted right
        self.duration_var = tk.StringVar()
        self.duration_entry = ttk.Entry(
            input_frame, textvariable=self.duration_var, width=5
        )
        self.duration_entry.grid(
            row=1, column=6, padx=5, pady=5, sticky=tk.W
        )  # Shifted right

        self.member_var.trace_add("write", self._load_and_fill_metadata)
        self.week_var.trace_add("write", self._load_and_fill_metadata)
        self.entry_var.trace_add("write", self._load_and_fill_metadata)

        ttk.Label(input_frame, text="Intro Text:").grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.NW
        )
        self.intro_text = scrolledtext.ScrolledText(
            input_frame, wrap=tk.WORD, height=4, width=100
        )
        self.intro_text.grid(
            row=2, column=1, columnspan=6, padx=5, pady=5, sticky=tk.W
        )  # Span 6 cols now

        image_frame = ttk.LabelFrame(master, text="Image Selection and Grouping")
        image_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        selection_preview_frame = ttk.Frame(image_frame)
        selection_preview_frame.pack(
            side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True
        )

        image_list_frame = ttk.Frame(selection_preview_frame)
        image_list_frame.pack(
            side=tk.LEFT, padx=5, pady=5, fill=tk.Y
        )  # List on the left

        ttk.Label(image_list_frame, text="Available Images:").pack(anchor=tk.W)
        self.image_listbox = Listbox(
            image_list_frame, selectmode=tk.EXTENDED, height=15, width=35
        )
        self.image_listbox.pack(fill=tk.Y, expand=True)
        self.image_listbox.bind(
            "<<ListboxSelect>>", self.on_image_select
        )  # Changed binding function

        preview_frame = ttk.Frame(selection_preview_frame)
        preview_frame.pack_propagate(
            False
        )  # Prevent frame from resizing to fit children

        preview_frame.pack(
            side=tk.LEFT, padx=10, pady=5, fill=tk.BOTH, expand=True
        )  # Preview on the right
        ttk.Label(preview_frame, text="Preview:").pack(anchor=tk.N)
        self.preview_label = Label(
            preview_frame, background="lightgrey"
        )  # Removed fixed size
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        self.preview_label.image = None  # Keep reference to prevent garbage collection
        preview_frame.bind("<Configure>", self.on_preview_resize)  # Bind resize event

        grouping_controls_frame = ttk.Frame(image_frame)
        grouping_controls_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)

        caption_frame = ttk.Frame(grouping_controls_frame)
        caption_frame.pack(pady=5)
        ttk.Label(caption_frame, text="Caption for Selected:").pack(anchor=tk.W)
        self.caption_text = scrolledtext.ScrolledText(
            caption_frame, wrap=tk.WORD, height=5, width=35
        )
        self.caption_text.pack(fill=tk.X)
        self.add_group_button = ttk.Button(
            caption_frame, text="Add Image Group", command=self.add_image_group
        )
        self.add_group_button.pack(pady=5)

        grouped_images_frame = ttk.Frame(grouping_controls_frame)
        grouped_images_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        ttk.Label(grouped_images_frame, text="Added Groups:").pack(anchor=tk.W)
        self.grouped_listbox = Listbox(
            grouped_images_frame, height=8, width=35
        )  # Adjusted height
        self.grouped_listbox.pack(fill=tk.BOTH, expand=True)
        self.remove_group_button = ttk.Button(
            grouped_images_frame,
            text="Remove Selected Group",
            command=self.remove_image_group,
        )
        self.remove_group_button.pack(pady=5)

        outro_frame = ttk.LabelFrame(master, text="Outro Text")
        outro_frame.pack(padx=10, pady=5, fill=tk.X)
        self.outro_text = scrolledtext.ScrolledText(
            outro_frame, wrap=tk.WORD, height=4, width=110
        )  # Wider
        self.outro_text.pack(padx=5, pady=5)

        output_frame = ttk.LabelFrame(master, text="Generated HTML")
        output_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        button_container = ttk.Frame(output_frame)  # Frame to hold buttons side-by-side
        button_container.pack(pady=5)

        self.generate_button = ttk.Button(
            button_container, text="Generate HTML", command=self.generate_html
        )
        self.generate_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(
            button_container, text="Clear All Fields", command=self.clear_all_fields
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.output_text = scrolledtext.ScrolledText(
            output_frame, wrap=tk.WORD, height=10, state=tk.DISABLED
        )
        self.output_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.available_images_data = []  # List of tuples: (display_name, full_path, relative_path_for_html)
        self.grouped_images_data = []  # List of tuples: (caption, [image_paths_for_html])
        self.current_preview_index = None  # Track which image is being previewed

        self._load_and_fill_metadata()

    def _load_and_fill_metadata(self, *args):
        """Loads metadata from file and pre-fills fields if found."""
        member_num = self.member_var.get()
        week_str = self.week_var.get()
        entry_str = self.entry_var.get()

        if not member_num or not week_str.isdigit() or not entry_str.isdigit():
            self.date_var.set(datetime.date.today().strftime("%B %d"))
            self.start_time_var.set("")
            self.duration_var.set("")
            return

        metadata_file = os.path.join(
            "Team", "journal", f"member{member_num}metadata.txt"
        )

        found = False
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, "r") as f:
                    for line in f:
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) == 5:
                            (
                                file_week_str,
                                file_entry_str,
                                duration,
                                start_time,
                                date,
                            ) = parts

                            file_week_match = re.match(
                                r"W(\d+)", file_week_str, re.IGNORECASE
                            )
                            file_entry_match = re.match(
                                r"E(\d+)", file_entry_str, re.IGNORECASE
                            )

                            if (
                                file_week_match
                                and file_entry_match
                                and file_week_match.group(1) == week_str
                                and file_entry_match.group(1) == entry_str
                            ):
                                self.duration_var.set(duration)
                                self.start_time_var.set(start_time)
                                self.date_var.set(date)
                                found = True
                                break  # Stop searching once found
            except Exception as e:
                print(f"Error reading metadata file {metadata_file}: {e}")

                self.date_var.set(datetime.date.today().strftime("%B %d"))
                self.start_time_var.set("")
                self.duration_var.set("")
                return  # Exit after error

        if not found:
            self.date_var.set(datetime.date.today().strftime("%B %d"))
            self.start_time_var.set("")
            self.duration_var.set("")

    def find_images(self):
        member_num = self.member_var.get()
        week = self.week_var.get()
        entry = self.entry_var.get()

        if not member_num:
            messagebox.showerror("Error", "Please select a Member number.")
            return
        if not week.isdigit() or not entry.isdigit():
            messagebox.showerror("Error", "Week and Entry must be numbers.")
            return

        base_image_path = os.path.join(
            "Team", "journal", f"img - member{member_num}", f"week{week}"
        )
        image_pattern = os.path.join(
            base_image_path, f"{entry}.*.*"
        )  # entry.<any>.<ext>

        self.image_listbox.delete(0, END)
        self.available_images_data = []
        self.clear_preview()

        if not os.path.isdir(base_image_path):
            messagebox.showwarning(
                "Warning", f"Image directory not found: {base_image_path}"
            )
            return

        found_files = sorted(glob.glob(image_pattern))
        image_regex = re.compile(rf"{re.escape(entry)}\.(\d+)\..+")
        valid_images_paths = []
        for f in found_files:
            match = image_regex.search(os.path.basename(f))
            if match:
                try:
                    index = int(match.group(1))
                    valid_images_paths.append((index, f))
                except ValueError:
                    pass

        valid_images_paths.sort()

        if not valid_images_paths:
            messagebox.showinfo(
                "Info", f"No images found matching pattern in {base_image_path}"
            )
            return

        for index, img_path in valid_images_paths:
            try:
                full_path = os.path.abspath(img_path)

                relative_path_for_html = os.path.relpath(full_path).replace("\\", "/")
                display_name = os.path.basename(img_path)
                self.available_images_data.append(
                    (display_name, full_path, relative_path_for_html)
                )
                self.image_listbox.insert(END, display_name)
            except Exception as e:
                print(f"Error processing image path {img_path}: {e}")
                display_name = os.path.basename(img_path) + " (Error)"
                self.available_images_data.append(
                    (display_name, None, None)
                )  # Mark as error
                self.image_listbox.insert(END, display_name)

    def clear_preview(self):
        """Clears the image preview label."""
        self.preview_label.config(image="", text="")
        self.preview_label.image = None
        self.current_preview_index = None

    def on_image_select(self, event):
        """Handles selection changes in the image listbox."""
        selected_indices = self.image_listbox.curselection()
        if not selected_indices:
            self.clear_preview()
            return
        first_selected_index = selected_indices[0]
        self.update_preview(first_selected_index)

    def on_preview_resize(self, event):
        """Handles resizing of the preview area."""

        if self.current_preview_index is not None:
            self.update_preview(self.current_preview_index)

    def update_preview(self, index):
        """Loads, resizes, and displays the image at the given index."""
        if not (0 <= index < len(self.available_images_data)):
            self.clear_preview()
            return

        _display_name, full_path, _relative_path = self.available_images_data[index]
        self.current_preview_index = index

        if not full_path:
            self.preview_label.config(image="", text="Preview N/A")
            self.preview_label.image = None
            return

        try:
            preview_width = self.preview_label.winfo_width()
            preview_height = self.preview_label.winfo_height()
            if preview_width <= 1 or preview_height <= 1:
                self.preview_label.config(image="", text="...")
                self.preview_label.image = None
                return

            img = Image.open(full_path)
            img_copy = img.copy()
            img_copy.thumbnail((preview_width, preview_height))
            photo = ImageTk.PhotoImage(img_copy)

            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo

        except Exception as e:
            print(f"Error loading/resizing preview for {full_path}: {e}")
            self.preview_label.config(image="", text="Preview Error")
            self.preview_label.image = None
            self.current_preview_index = None

    def add_image_group(self):
        selected_indices = self.image_listbox.curselection()
        caption = self.caption_text.get("1.0", tk.END).strip()

        if not selected_indices and not caption:
            messagebox.showerror("Error", "Please select images or enter a caption.")
            return
        elif not caption:
            messagebox.showerror("Error", "Please enter a caption for the group.")
            return

        selected_image_paths_for_html = []
        error_images = []
        for i in selected_indices:
            if 0 <= i < len(self.available_images_data):
                display_name, _full_path, relative_path_for_html = (
                    self.available_images_data[i]
                )
                if relative_path_for_html:  # Check if it's not an error entry
                    selected_image_paths_for_html.append(relative_path_for_html)
                else:
                    error_images.append(display_name)

        if error_images:
            messagebox.showwarning(
                "Skipped Images",
                f"Skipping images that failed to load: {', '.join(error_images)}",
            )

        if not selected_image_paths_for_html:
            if selected_indices:
                messagebox.showerror("Error", "No valid images selected.")
                return

        group_data = (caption, selected_image_paths_for_html)
        self.grouped_images_data.append(group_data)

        if selected_image_paths_for_html:
            group_display_text = f"Group {len(self.grouped_images_data)}: {len(selected_image_paths_for_html)} images - {caption[:30]}..."
        else:
            group_display_text = (
                f"Group {len(self.grouped_images_data)}: Text Only - {caption[:30]}..."
            )
        self.grouped_listbox.insert(END, group_display_text)

        self.image_listbox.selection_clear(0, END)
        self.caption_text.delete("1.0", tk.END)
        self.clear_preview()

    def remove_image_group(self):
        selected_indices = self.grouped_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select a group to remove.")
            return

        for i in sorted(selected_indices, reverse=True):
            self.grouped_listbox.delete(i)
            del self.grouped_images_data[i]

        current_items = self.grouped_listbox.get(0, END)
        self.grouped_listbox.delete(0, END)
        for idx, item_text in enumerate(current_items):
            parts = item_text.split(":", 1)
            new_text = f"Group {idx + 1}:{parts[1]}"
            self.grouped_listbox.insert(END, new_text)

    def generate_html(self):
        md = MarkdownIt()  # Initialize Markdown parser
        member_num = self.member_var.get()  # Get selected member
        week = self.week_var.get()
        entry = self.entry_var.get()
        date_str = self.date_var.get().strip()
        start_time_str = self.start_time_var.get().strip()
        duration_str = self.duration_var.get().strip()
        intro = self.intro_text.get("1.0", tk.END).strip()
        outro = self.outro_text.get("1.0", tk.END).strip()

        if not member_num:
            messagebox.showerror("Error", "Please select a Member number.")
            return
        if not week or not entry:
            messagebox.showerror("Error", "Please enter Week and Entry numbers.")
            return

        html_output = []

        html_output.append(
            f'          <h4 id="sec-week{week}-e{entry}">'
        )  # Sticking to original format
        html_output.append(
            f"            <b>Entry {entry}: -----------------------------------------------------------------</b>"
        )
        html_output.append("          </h4>")

        html_output.append('          <div class="entry-metadata">')
        html_output.append(f"            <p><b>Date:</b> {html.escape(date_str)}</p>")
        html_output.append(
            f"            <p><b>Start Time:</b> {html.escape(start_time_str)}</p>"
        )
        html_output.append(
            f"            <p><b>Duration:</b> {html.escape(duration_str)} hours</p>"
        )
        html_output.append("          </div>")

        html_output.append('          <div class="entry-content">')
        html_output.append('            <div class="section">')

        if intro:
            intro_html = md.render(
                intro
            ).strip()  # Render and remove leading/trailing whitespace

            html_output.append(intro_html)
            html_output.append("")  # Add blank line after intro block

        if self.grouped_images_data:
            html_output.append('              <div class="image-section">')
            html_output.append('                <div class="grid">')
            for i, (caption_raw, image_paths_for_html) in enumerate(
                self.grouped_images_data
            ):
                html_output.append('                  <figure class="grid-item">')
                html_output.append("                    <figcaption>")

                caption_html = md.render(caption_raw).strip()  # Render and strip

                html_output.append(f"                      <h4>{i + 1}.</h4>")
                html_output.append(caption_html)  # Add raw HTML
                html_output.append("                    </figcaption>")

                if image_paths_for_html:
                    for img_path in image_paths_for_html:
                        safe_img_path = html.escape(img_path)
                        html_output.append(
                            f'                    <img src="{safe_img_path}">'
                        )
                html_output.append("                  </figure>")
            html_output.append("                </div>")
            html_output.append("              </div>")
            html_output.append("")  # Add blank line after image section

        if outro:
            outro_html = md.render(outro).strip()  # Render and strip

            html_output.append(outro_html)

        html_output.append("            </div>")
        html_output.append("          </div>")

        final_html = "\n".join(html_output)
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, final_html)
        self.output_text.config(state=tk.DISABLED)

    def clear_all_fields(self):
        """Clears all input fields, grouped images, and output."""

        self.intro_text.delete("1.0", tk.END)
        self.caption_text.delete("1.0", tk.END)
        self.outro_text.delete("1.0", tk.END)

        self.grouped_listbox.delete(0, END)
        self.grouped_images_data = []

        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)

        self.clear_preview()

        self.date_var.set(datetime.date.today().strftime("%B %d"))
        self.start_time_var.set("")
        self.duration_var.set("")

        messagebox.showinfo("Cleared", "All input fields and groups have been cleared.")


if __name__ == "__main__":
    root = tk.Tk()
    app = JournalAuthorApp(root)
    root.mainloop()
