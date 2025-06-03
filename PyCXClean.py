import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
from pathlib import Path
import numpy as np
from PIL import Image
import os

class PaletteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PyCX Clean")
        self.root.geometry("530x200")
        self.palette_path = ""
        self.image_folder = ""
        self.transparent_color = (0, 0, 0)

        self.create_widgets()

    def create_widgets(self):
        pad = {'padx': 10, 'pady': 5}

        # Palette selector
        tk.Label(self.root, text="Palette (.act) File:").grid(row=0, column=0, sticky="w", **pad)
        self.palette_entry = tk.Entry(self.root, width=50)
        self.palette_entry.grid(row=0, column=1, **pad)
        tk.Button(self.root, text="Browse", command=self.browse_palette).grid(row=0, column=2, **pad)

        # Image folder selector
        tk.Label(self.root, text="PNG Image Folder:").grid(row=1, column=0, sticky="w", **pad)
        self.folder_entry = tk.Entry(self.root, width=50)
        self.folder_entry.grid(row=1, column=1, **pad)
        tk.Button(self.root, text="Browse", command=self.browse_folder).grid(row=1, column=2, **pad)

        # Transparency color
        tk.Label(self.root, text="Transparent Color:").grid(row=2, column=0, sticky="w", **pad)
        self.color_label = tk.Label(self.root, bg="#000000", width=20, relief="sunken")
        self.color_label.grid(row=2, column=1, **pad)
        tk.Button(self.root, text="Choose", command=self.choose_color).grid(row=2, column=2, **pad)

        # Run button
        tk.Button(self.root, text="Clean", command=self.run_process, height=2, width=20, bg="green", fg="white").grid(
            row=4, column=1, pady=20
        )

    def browse_palette(self):
        path = filedialog.askopenfilename(filetypes=[("ACT files", "*.act")])
        if path:
            self.palette_path = path
            self.palette_entry.delete(0, tk.END)
            self.palette_entry.insert(0, path)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.image_folder = folder
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)

    def choose_color(self):
        color_code, _ = colorchooser.askcolor(title="Choose Transparent Color")
        if color_code:
            self.transparent_color = tuple(map(int, color_code))
            hex_color = "#{:02x}{:02x}{:02x}".format(*self.transparent_color)
            self.color_label.config(bg=hex_color)

    def run_process(self):
        if not self.palette_path or not self.image_folder:
            messagebox.showerror("Error", "Please select both a palette file and image folder.")
            return

        output_folder = Path(self.image_folder) / "output"
        output_folder.mkdir(exist_ok=True)

        try:
            palette = self.load_act_palette(self.palette_path)
            for image_file in Path(self.image_folder).glob("*.png"):
                output_path = output_folder / image_file.name
                self.apply_palette(image_file, palette, output_path, self.transparent_color)
            messagebox.showinfo("Done", f"Images saved to: {output_folder}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_act_palette(self, act_path):
        with open(act_path, "rb") as f:
            data = f.read()
        palette = [tuple(data[i:i+3]) for i in range(0, min(len(data), 768), 3)]
        return palette + [(0, 0, 0)] * (256 - len(palette))  # pad to 256 colors

    def apply_palette(self, image_path, palette, output_path, transparent_color):
        img = Image.open(image_path).convert("RGBA")
        flat_palette = sum(palette, ())
        pal_img = Image.new("P", (1, 1))
        pal_img.putpalette(flat_palette)
        indexed = img.convert("RGB").quantize(palette=pal_img)

        used_indexes = set(np.array(indexed))

        indexed_rgb = indexed.convert("RGBA")
        data = np.array(indexed_rgb)

        for idx in range(256):
            if idx not in used_indexes:
                r, g, b = palette[idx]
                mask = (data[:, :, 0] == r) & (data[:, :, 1] == g) & (data[:, :, 2] == b)
                data[mask] = [*transparent_color, 0]

        result = Image.fromarray(data, mode="RGBA")
        result.save(output_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = PaletteApp(root)
    root.mainloop()
