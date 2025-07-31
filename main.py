import requests
from PIL import Image, ImageTk, ImageSequence
import tkinter as tk
from tkinter import simpledialog, messagebox
from io import BytesIO
import tempfile
import shutil
import pathlib
import os

class ScalableImage(tk.Label):
    def __init__(self, master, image_data, update_title_callback):
        super().__init__(master)
        self.master = master
        self.image_data = image_data
        self.original_image = Image.open(self.image_data)
        self.is_animated = getattr(self.original_image, "is_animated", False)
        self.stretch = False
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
        self.resize_and_display(self.original_image)

    def update_scaled_frames(self):
        self.tk_frames.clear()
        width, height = self.master.winfo_width(), self.master.winfo_height()
        if width < 1 or height < 1:
            width, height = 400, 400

        for frame in self.frames:
            if self.stretch:
                new_size = (width, height)
            else:
                img_w, img_h = frame.size
                ratio = min(width / img_w, height / img_h)
                new_size = (int(img_w * ratio), int(img_h * ratio))

            resized = frame.resize(new_size, Image.Resampling.LANCZOS)
            self.tk_frames.append(ImageTk.PhotoImage(resized))

    def animate_gif(self):
        if not self.animate or not self.tk_frames:
            self.after(100, self.animate_gif)
            return
        self.config(image=self.tk_frames[self.index])
        self.index = (self.index + 1) % len(self.tk_frames)
        self.after(100, self.animate_gif)

    def resize_and_display(self, image):
        width, height = self.master.winfo_width(), self.master.winfo_height()
        if width < 1 or height < 1:
            width, height = 400, 400

        if self.stretch:
            new_size = (width, height)
        else:
            img_w, img_h = image.size
            ratio = min(width / img_w, height / img_h)
            new_size = (int(img_w * ratio), int(img_h * ratio))

        resized_image = image.resize(new_size, Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)
        self.config(image=self.tk_image)

    def on_resize(self, event):
        if self.is_animated:
            self.update_scaled_frames()
        self.update_static_image()

    def toggle_stretch(self):
        self.stretch = not self.stretch
        self.update_title(self.stretch)
        if self.is_animated:
            self.update_scaled_frames()
        else:
            self.update_static_image()

def download_image(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        suffix = ""
        basename = url.split("/")[-1].split("?")[0]
        if "." in basename:
            suffix = os.path.splitext(basename)[1]
        else:
            suffix = ".img"

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(response.content)
        temp_file.close()

        return temp_file.name, BytesIO(response.content)
    except Exception as e:
        print(f"Błąd pobierania obrazu: {e} -- podaj link ktory konczy sie na .png/.jpg/.gif")
        return None, None

def main():
    root = tk.Tk()
    root.geometry("600x600")

    try:
        root.iconphoto(False, tk.PhotoImage(file="icon.png"))
    except Exception:
        pass

    url = simpledialog.askstring("Podaj URL", "Podaj link do obrazka lub GIF-a (.png/.jpg/.gif):", parent=root)
    if not url:
        root.destroy()
        return

    temp_path, image_data = download_image(url)
    if not image_data:
        root.destroy()
        return

    def update_window_title(stretching):
        root.title("Site media (scalable)" if stretching else "Site media")

    root.title("Site media")

    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=0)
    root.grid_rowconfigure(2, weight=0)
    root.grid_rowconfigure(3, weight=0)
    root.grid_columnconfigure(0, weight=1)

    viewer = ScalableImage(root, image_data, update_window_title)
    viewer.grid(row=0, column=0, sticky="nsew")

    def save_to_downloads():
        filename = url.split("/")[-1].split("?")[0] or "obraz"
        if "." not in filename:
            try:
                fmt = viewer.original_image.format or "PNG"
                ext = "." + fmt.lower()
            except Exception:
                ext = ".png"
            filename += ext

        downloads_path = pathlib.Path.home() / "Downloads"
        downloads_path.mkdir(exist_ok=True)

        dest = downloads_path / filename
        try:
            shutil.copy(temp_path, dest)
            messagebox.showinfo("Zapisano", f"Obraz zapisany do: {dest}")
        except Exception as e:
            print(f"Błąd zapisu: {e}")

    save_button = tk.Button(root, text="Pobierz", command=save_to_downloads)
    save_button.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

    advanced_frame = tk.Frame(root, relief="groove", bd=1)
    advanced_frame.grid(row=2, column=0, sticky="ew", padx=10)
    advanced_frame.grid_remove()

    stretch_button = tk.Button(advanced_frame, text="Skalowanie: WYŁ.", width=25)
    stretch_button.pack(fill="x", pady=2)

    def toggle_stretch_mode():
        viewer.toggle_stretch()
        stretch_button.config(text=f"Skalowanie: {'WŁ.' if viewer.stretch else 'WYŁ.'}")
    stretch_button.config(command=toggle_stretch_mode)

    def toggle_advanced():
        if advanced_frame.winfo_viewable():
            advanced_frame.grid_remove()
            advanced_toggle_btn.config(text="Zaawansowane ˅")
        else:
            advanced_frame.grid()
            advanced_toggle_btn.config(text="Zaawansowane ˄")

    advanced_toggle_btn = tk.Button(root, text="Zaawansowane ˅", command=toggle_advanced)
    advanced_toggle_btn.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

    def delayed_start():
        if viewer.is_animated:
            viewer.update_scaled_frames()
        else:
            viewer.update_static_image()

    root.after(100, delayed_start)

    def on_close():
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
