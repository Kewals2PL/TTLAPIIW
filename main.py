import requests
from PIL import Image, ImageTk, ImageSequence
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from io import BytesIO
import os

class ScalableImage(tk.Label):
    def __init__(self, master, image_data, update_title_callback):
        super().__init__(master)
        self.master = master
        self.image_data = image_data
        self.original_image = Image.open(self.image_data)
        self.is_animated = getattr(self.original_image, "is_animated", False)
        self.scaling_enabled = False
        self.update_title = update_title_callback

        if self.is_animated:
            self.frames = [frame.copy().convert("RGBA") for frame in ImageSequence.Iterator(self.original_image)]
            self.tk_frames = []
            self.index = 0
            self.animate = True
            self.update_scaled_frames()
            self.animate_gif()
        else:
            self.update_static_image()

        self.bind("<Configure>", self.on_resize)

    def update_static_image(self):
        if self.scaling_enabled:
            self.resize_and_display(self.original_image)
        else:
            self.display_keep_aspect_ratio(self.original_image)

    def update_scaled_frames(self):
        self.tk_frames.clear()
        if not self.scaling_enabled:
            for frame in self.frames:
                self.tk_frames.append(ImageTk.PhotoImage(frame))
            return

        width, height = self.winfo_width(), self.winfo_height()
        for frame in self.frames:
            resized = self.resize_with_aspect_ratio(frame, width, height)
            self.tk_frames.append(ImageTk.PhotoImage(resized))

    def animate_gif(self):
        if not self.animate:
            return
        self.config(image=self.tk_frames[self.index])
        self.index = (self.index + 1) % len(self.tk_frames)
        self.after(100, self.animate_gif)

    def resize_and_display(self, image):
        width, height = self.winfo_width(), self.winfo_height()
        resized_image = image.resize((width, height), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)
        self.config(image=self.tk_image)

    def resize_with_aspect_ratio(self, image, max_w, max_h):
        orig_w, orig_h = image.size
        ratio = min(max_w / orig_w, max_h / orig_h)
        new_size = (int(orig_w * ratio), int(orig_h * ratio))
        return image.resize(new_size, Image.LANCZOS)

    def display_keep_aspect_ratio(self, image):
        resized = self.resize_with_aspect_ratio(image, self.winfo_width(), self.winfo_height())
        self.tk_image = ImageTk.PhotoImage(resized)
        self.config(image=self.tk_image)

    def on_resize(self, event):
        if self.is_animated:
            self.update_scaled_frames()
        self.update_static_image()

    def toggle_scaling(self):
        self.scaling_enabled = not self.scaling_enabled
        self.update_title(self.scaling_enabled)
        if self.is_animated:
            self.update_scaled_frames()
        self.update_static_image()

    def save_to_downloads(self):
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads, exist_ok=True)

        format = self.original_image.format or "PNG"
        extension = format.lower()
        filename = f"pobrany_obraz.{extension}"
        path = os.path.join(downloads, filename)

        with open(path, "wb") as f:
            f.write(self.image_data.getvalue())

        messagebox.showinfo("Zapisano", f"Obraz zapisany do: {path}")

def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        print(f"Błąd pobierania obrazu: {e} -- podaj link który kończy się na .png/.jpg/.gif")
        return None

def main():
    root = tk.Tk()
    root.geometry("800x600")
    root.iconphoto(False, tk.PhotoImage(file="icon.png"))

    # Ustawienie ikony także dla okna dialogowego
    dialog = tk.Toplevel()
    dialog.withdraw()
    dialog.iconphoto(False, tk.PhotoImage(file="icon.png"))
    url = simpledialog.askstring("Podaj URL", "Podaj link do obrazka lub GIF-a (.png/.jpg/.gif):", parent=dialog)
    dialog.destroy()

    if not url:
        root.destroy()
        return

    image_data = download_image(url)
    if not image_data:
        root.destroy()
        return

    def update_window_title(is_scaling):
        root.title("Site media (scalable)" if is_scaling else "Site media")

    root.title("Site media")

    # Główne ramki
    top_frame = tk.Frame(root)
    top_frame.pack(fill="both", expand=True)

    bottom_frame = tk.Frame(root)
    bottom_frame.pack(side="bottom", fill="x")

    viewer = ScalableImage(top_frame, image_data, update_window_title)
    viewer.pack(fill="both", expand=True)

    download_btn = tk.Button(bottom_frame, text="Pobierz", command=viewer.save_to_downloads)
    toggle_scaling_btn = ttk.Button(bottom_frame, text="Tryb rozciągania: WYŁ.", command=lambda: toggle_scaling_mode())

    # Logika przycisku zaawansowane
    def toggle_advanced():
        if toggle_scaling_btn.winfo_ismapped():
            toggle_scaling_btn.pack_forget()
            advanced_btn.config(text="Zaawansowane ˅")
        else:
            toggle_scaling_btn.pack(side="left", padx=10)
            advanced_btn.config(text="Zaawansowane ˄")

    def toggle_scaling_mode():
        viewer.toggle_scaling()
        toggle_scaling_btn.config(text=f"Tryb rozciągania: {'WŁ.' if viewer.scaling_enabled else 'WYŁ.'}")

    advanced_btn = tk.Button(bottom_frame, text="Zaawansowane ˅", command=toggle_advanced)

    # Pakowanie przycisków
    download_btn.pack(side="left", padx=10, pady=5)
    advanced_btn.pack(side="left", padx=10, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
#fajnaliczba
