import requests
from PIL import Image, ImageTk, ImageSequence
import tkinter as tk
from io import BytesIO

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
            width, height = 400, 400  # default size if window too small
        for frame in self.frames:
            resized = frame.resize((width, height), Image.ANTIALIAS)
            self.tk_frames.append(ImageTk.PhotoImage(resized))

    def animate_gif(self):
        if not self.animate:
            return
        self.config(image=self.tk_frames[self.index])
        self.index = (self.index + 1) % len(self.tk_frames)
        self.after(100, self.animate_gif)

    def resize_and_display(self, image):
        width, height = self.master.winfo_width(), self.master.winfo_height()
        if width < 1 or height < 1:
            width, height = 400, 400
        resized_image = image.resize((width, height), Image.ANTIALIAS)
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
        return BytesIO(response.content)
    except Exception as e:
        print(f"Błąd pobierania obrazu: {e}")
        return None

def main():
    url = input("Podaj link do obrazka lub GIF-a: ").strip()
    image_data = download_image(url)
    if not image_data:
        return

    root = tk.Tk()
    root.geometry("600x600")
    root.title("Obraz z internetu (skalowany)")

    viewer = ScalableImage(root, image_data)
    viewer.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()