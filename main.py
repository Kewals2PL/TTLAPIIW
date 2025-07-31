import requests
from PIL import Image, ImageTk, ImageSequence
import tkinter as tk
from io import BytesIO
import tempfile
import shutil
import os
import pathlib


class ScalableImage(tk.Label):
    def __init__(self, master, image_data):
        super().__init__(master)
        self.master = master
        self.image_data = image_data
        self.original_image = Image.open(self.image_data)
        self.is_animated = getattr(self.original_image, "is_animated", False)

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
        self.resize_and_display(self.original_image)

    def update_scaled_frames(self):
        self.tk_frames.clear()
        width, height = self.master.winfo_width(), self.master.winfo_height()
        if width < 1 or height < 1:
            width, height = 400, 400

        for frame in self.frames:
            img_w, img_h = frame.size
            ratio = min(width / img_w, height / img_h)
            new_size = (int(img_w * ratio), int(img_h * ratio))

            resized = frame.resize(new_size, Image.Resampling.LANCZOS)
            self.tk_frames.append(ImageTk.PhotoImage(resized))

    def animate_gif(self):
        if not self.animate or not self.tk_frames:
            return
        self.config(image=self.tk_frames[self.index])
        self.index = (self.index + 1) % len(self.tk_frames)
        self.after(100, self.animate_gif)

    def resize_and_display(self, image):
        width, height = self.master.winfo_width(), self.master.winfo_height()
        if width < 1 or height < 1:
            width, height = 400, 400

        img_w, img_h = image.size
        ratio = min(width / img_w, height / img_h)
        new_size = (int(img_w * ratio), int(img_h * ratio))

        resized_image = image.resize(new_size, Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)
        self.config(image=self.tk_image)


    def on_resize(self, event):
        if self.is_animated:
            self.update_scaled_frames()
        else:
            self.resize_and_display(self.original_image)

def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Zapisz tymczasowy plik
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".img")
        temp_file.write(response.content)
        temp_file.close()

        return temp_file.name, BytesIO(response.content)  # ścieżka + dane obrazu

    except Exception as e:
        print(f"Błąd pobierania obrazu: {e} -- Spróbuj link z końcówką .png/.jpg/.gif")
        return None, None

def main():
    url = input("Podaj link do obrazka lub GIF-a: ").strip()
    temp_path, image_data = download_image(url)
    if not image_data:
        return

    root = tk.Tk()
    root.geometry("600x600")
    root.title("Site Media (scalable)")

    try:
        icon = tk.PhotoImage(file="icon.png")
        root.iconphoto(False, icon)
    except Exception:
        pass  # brak ikony to nie problem krytyczny

    # Konfiguracja siatki
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Obraz (wiersz 0)
    viewer = ScalableImage(root, image_data)
    viewer.grid(row=0, column=0, sticky="nsew")

    # Przycisk (wiersz 1)
    def save_to_downloads():
        filename = url.split("/")[-1].split("?")[0] or "obraz"
        if "." not in filename:
            filename += ".png"

        downloads_path = pathlib.Path.home() / "Downloads"
        downloads_path.mkdir(exist_ok=True)

        dest = downloads_path / filename
        shutil.copy(temp_path, dest)
        print(f"Zapisano do: {dest}")

    save_button = tk.Button(root, text="Pobierz", command=save_to_downloads)
    save_button.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

    def delayed_start():
        if viewer.is_animated:
            viewer.update_scaled_frames()
        else:
            viewer.update_static_image()

    root.after(100, delayed_start)
    root.mainloop()

if __name__ == "__main__":
    main()
