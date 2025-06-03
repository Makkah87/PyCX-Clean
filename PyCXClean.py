import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox, ttk
from pathlib import Path
from PIL import Image
import numpy as np
import os

class PaletteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PyCX Clean")
        self.root.geometry("550x280")
        self.palette_path = ""
        self.image_folder = ""
        self.replacement_color = (0, 0, 0)

        self.create_widgets()

    def create_widgets(self):
        pad = {'padx': 10, 'pady': 5}

        tk.Label(self.root, text="Palette (.act) File:").grid(row=0, column=0, sticky="w", **pad)
        self.palette_entry = tk.Entry(self.root, width=50)
        self.palette_entry.grid(row=0, column=1, **pad)
        tk.Button(self.root, text="Browse", command=self.browse_palette).grid(row=0, column=2, **pad)

        tk.Label(self.root, text="PNG Image Folder:").grid(row=1, column=0, sticky="w", **pad)
        self.folder_entry = tk.Entry(self.root, width=50)
        self.folder_entry.grid(row=1, column=1, **pad)
        tk.Button(self.root, text="Browse", command=self.browse_folder).grid(row=1, column=2, **pad)

        tk.Label(self.root, text="Replacement Color:").grid(row=2, column=0, sticky="w", **pad)
        self.color_label = tk.Label(self.root, bg="#000000", width=20, relief="sunken")
        self.color_label.grid(row=2, column=1, **pad)
        tk.Button(self.root, text="Choose", command=self.choose_color).grid(row=2, column=2, **pad)

        # Run button with sky blue background and rounded effect
        self.run_button = tk.Button(
            self.root,
            text="Run",
            command=self.run_process,
            height=2,
            width=20,
            bg="#3629de",  # Sky blue
            fg="white",
            relief="flat",
            bd=6,
            font=("Segoe UI", 10, "bold")
        )
        self.run_button.grid(row=4, column=1, pady=(20, 5))

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=5, column=0, columnspan=3, padx=20, pady=10)

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
        color_code, _ = colorchooser.askcolor(title="Choose Replacement Color")
        if color_code:
            self.replacement_color = tuple(map(int, color_code))
            hex_color = "#{:02x}{:02x}{:02x}".format(*self.replacement_color)
            self.color_label.config(bg=hex_color)

    def run_process(self):
        if not self.palette_path or not self.image_folder:
            messagebox.showerror("Error", "Please select both a palette file and image folder.")
            return

        output_folder = Path(self.image_folder) / "output"
        output_folder.mkdir(exist_ok=True)

        try:
            palette = self.load_act_palette(self.palette_path)
            image_files = list(Path(self.image_folder).glob("*.png"))
            total = len(image_files)
            if total == 0:
                messagebox.showinfo("No PNGs", "No PNG images found in the selected folder.")
                return

            self.progress["maximum"] = total
            self.progress["value"] = 0
            self.root.update_idletasks()

            for idx, image_file in enumerate(image_files, 1):
                output_path = output_folder / image_file.name
                self.process_image(image_file, palette, output_path)
                self.progress["value"] = idx
                self.root.update_idletasks()

            messagebox.showinfo("Done", f"Processed images saved to: {output_folder}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_act_palette(self, act_path):
        with open(act_path, "rb") as f:
            data = f.read()
        palette = [tuple(data[i:i+3]) for i in range(0, min(len(data), 768), 3)]
        return palette + [(0, 0, 0)] * (256 - len(palette))  # Ensure 256 colors

    def process_image(self, image_path, palette, output_path):
        img = Image.open(image_path).convert("RGBA")
        data = np.array(img)

        # Compare only RGB
        rgb_pixels = data[:, :, :3].reshape(-1, 3)
        palette_set = set(palette)

        # Mask for pixels not in the palette
        mask = np.array([tuple(pixel) not in palette_set for pixel in rgb_pixels])
        mask = mask.reshape(data.shape[:2])

        # Replace with user-selected color (fully opaque)
        data[mask] = [*self.replacement_color, 255]

        # Convert back to RGBA image
        cleaned = Image.fromarray(data, mode="RGBA")

        # Convert to RGB (quantize only supports RGB or L)
        rgb_cleaned = cleaned.convert("RGB")

        # Create P-mode palette image
        pal_img = Image.new("P", (1, 1))
        flat_palette = sum(palette, ())[:768]
        pal_img.putpalette(flat_palette)

        # Quantize using the ACT palette
        final_img = rgb_cleaned.quantize(palette=pal_img, dither=Image.NONE)

        # Save result
        final_img.save(output_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = PaletteApp(root)
    root.mainloop()
