import tkinter as tk  # GUI framework for desktop windows and widgets
from tkinter import filedialog  # file dialog for choosing an image from disk
import math
import random
from game_image import GameImage  # encapsulated image model for original/modified image handling
from difference_generator import DifferenceGenerator  # generates the 5 random difference regions

# Color palette and constants
BG_MAIN      = "#f5f0f8"
BG_PANEL     = "#fdf8ff"
BG_CARD      = "#ffffff"
PINK         = "#e8799a"
PINK_LIGHT   = "#f5b8cb"
PINK_DARK    = "#c45070"
PINK_BG      = "#fdeef3"
TEAL         = "#4db8b8"
TEAL_DARK    = "#2a8080"
TEXT_DARK    = "#1a1a2e"
TEXT_MID     = "#4a4a6a"
TEXT_DIM     = "#8888aa"
RED_ERR      = "#e05252"
GREEN_OK     = "#3aaa72"
BORDER       = "#e8d8f0"
BORDER_DARK  = "#d0b8e0"

MAX_MISTAKES = 3
NUM_DIFFS    = 5
CANVAS_W     = 530
CANVAS_H     = 400

# Utility function to create styled buttons with hover behavior
def make_button(parent, text, command, style="pink", font_size=12, width=24, pady=10):
    styles = {
        "pink":  {"bg": PINK_DARK,  "fg": "#ffffff",  "hover": PINK,      "active": PINK_LIGHT},
        "teal":  {"bg": TEAL_DARK,  "fg": "#ffffff",  "hover": TEAL,      "active": "#80e8e8"},
        "red":   {"bg": "#8a1a1a",  "fg": "#ffffff",  "hover": RED_ERR,   "active": "#ff8080"},
        "dark":  {"bg": BORDER,     "fg": TEXT_MID,   "hover": BORDER_DARK, "active": TEXT_MID},
    }
    s = styles.get(style, styles["pink"])
    btn = tk.Button(
        parent, text=text, command=command,
        bg=s["bg"], fg=s["fg"],
        font=("Georgia", font_size, "bold"),
        relief="flat", cursor="hand2",
        width=width, pady=pady,
        activebackground=s["active"], activeforeground=TEXT_DARK,
        bd=0, highlightthickness=1, highlightbackground=PINK_DARK
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=s["hover"]))
    btn.bind("<Leave>", lambda e: btn.config(bg=s["bg"]))
    return btn

# Main application class that launches the UI and hosts the game page
class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Spot the Difference")
        self.root.state('zoomed')
        self.root.minsize(1024, 720)
        self.current_page = GamePage(self.root)
        self.current_page.pack(fill="both", expand=True)

# GamePage is the main frame that encapsulates all game logic and state
class GamePage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG_MAIN)
        self.total_found_overall = 0  # cumulative number of found differences across images
        self.game_image = None  # GameImage object stores the loaded image state
        self.generator = DifferenceGenerator()  # DifferenceGenerator creates the 5 difference regions
        self.mistakes = 0
        self.game_over = False
        self.has_revealed = False
        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self, bg=BG_PANEL, highlightthickness=1, highlightbackground=BORDER_DARK)
        top.pack(fill="x")
        tk.Frame(self, bg=PINK_DARK, height=3).place(relx=0, rely=0, relwidth=1)
        
        top_inner = tk.Frame(top, bg=BG_PANEL)
        top_inner.pack(fill="x", padx=14, pady=10)

        self.load_btn_top = make_button(top_inner, "+  Load Image", self._load_image, style="pink", font_size=11, width=18, pady=6)
        self.load_btn_top.pack(side="left", padx=(0, 8))
        
        self.reveal_btn_top = make_button(top_inner, "◈  Reveal All", self._reveal_all, style="teal", font_size=11, width=18, pady=6)
        self.reveal_btn_top.pack(side="left")
        self.reveal_btn_top.config(state="disabled", disabledforeground="#ffffff")

        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(fill="both", expand=True, padx=14, pady=(10, 12))
        
        side = tk.Frame(body, bg=BG_PANEL, width=220, highlightthickness=1, highlightbackground=BORDER_DARK)
        side.pack(side="left", fill="y", padx=(0, 10))
        side.pack_propagate(False)

        tk.Label(side, text="── STATUS ──", bg=BG_PANEL, fg=PINK_DARK, font=("Georgia", 12, "bold")).pack(pady=(20, 10))
        
        rem_f = tk.Frame(side, bg=PINK_BG, highlightthickness=1, highlightbackground=BORDER)
        rem_f.pack(fill="x", padx=12, pady=8)
        self.remaining_var = tk.StringVar(value="—")
        tk.Label(rem_f, text="Remaining", bg=PINK_BG, fg=TEXT_MID, font=("Georgia", 10)).pack()
        tk.Label(rem_f, textvariable=self.remaining_var, bg=PINK_BG, fg=PINK_DARK, font=("Georgia", 26, "bold")).pack()

        mist_f = tk.Frame(side, bg=PINK_BG, highlightthickness=1, highlightbackground=BORDER)
        mist_f.pack(fill="x", padx=12, pady=8)
        self.mistakes_var = tk.StringVar(value="0 / 3")
        tk.Label(mist_f, text="Mistakes", bg=PINK_BG, fg=TEXT_MID, font=("Georgia", 10)).pack()
        tk.Label(mist_f, textvariable=self.mistakes_var, bg=PINK_BG, fg=PINK_DARK, font=("Georgia", 16, "bold")).pack()
        
        self.hearts_frame = tk.Frame(mist_f, bg=PINK_BG)
        self.hearts_frame.pack(pady=(0, 5))
        self._render_hearts(0)

        tk.Frame(side, bg=BORDER, height=1, width=160).pack(pady=10)
        tk.Label(side, text="Total differences found", bg=BG_PANEL, fg=PINK_DARK, font=("Georgia", 11, "italic")).pack(pady=(15, 0))
        self.total_num_var = tk.StringVar(value="0")
        tk.Label(side, textvariable=self.total_num_var, bg=BG_PANEL, fg=PINK_DARK, font=("Georgia", 18, "bold")).pack()
        tk.Frame(side, bg=BORDER, height=1, width=160).pack(pady=10)

        self.status_var = tk.StringVar(value="Load an image to begin")
        tk.Label(side, textvariable=self.status_var, bg=BG_PANEL, fg=TEXT_MID, font=("Georgia", 10, "italic"), wraplength=190).pack(pady=(0, 15))

        centre = tk.Frame(body, bg=BG_MAIN)
        centre.pack(side="left", fill="both", expand=True)
        
        header = tk.Frame(centre, bg=BG_MAIN)
        header.pack(fill="x", pady=(0, 8))
        for title, sub in [("ORIGINAL IMAGE", "Reference"), ("MODIFIED IMAGE", "Click here to find differences")]:
            col = tk.Frame(header, bg=BG_MAIN)
            col.pack(side="left", expand=True, fill="x")
            tk.Label(col, text=title, bg=BG_MAIN, fg=PINK_DARK, font=("Georgia", 13, "bold")).pack()
            tk.Label(col, text=sub, bg=BG_MAIN, fg=TEXT_DIM, font=("Georgia", 10)).pack()

        canvas_row = tk.Frame(centre, bg=BG_MAIN)
        canvas_row.pack(fill="both", expand=True)

        l_wrap = tk.Frame(canvas_row, bg=BG_MAIN, highlightthickness=1, highlightbackground=PINK_DARK)
        l_wrap.pack(side="left", expand=True, fill="both", padx=5)
        self.left_canvas = tk.Canvas(l_wrap, bg=BG_MAIN, highlightthickness=0, width=CANVAS_W, height=CANVAS_H)
        self.left_canvas.pack(expand=True, fill="both")

        r_wrap = tk.Frame(canvas_row, bg=BG_MAIN, highlightthickness=1, highlightbackground=PINK_DARK)
        r_wrap.pack(side="left", expand=True, fill="both", padx=5)
        self.right_canvas = tk.Canvas(r_wrap, bg=BG_MAIN, highlightthickness=0, width=CANVAS_W, height=CANVAS_H)
        self.right_canvas.pack(expand=True, fill="both")
        self.right_canvas.bind("<Button-1>", self._on_click)

    def _render_hearts(self, mistakes):
        for w in self.hearts_frame.winfo_children(): w.destroy()
        for i in range(MAX_MISTAKES):
            color = TEXT_DIM if i < mistakes else RED_ERR 
            tk.Label(self.hearts_frame, text="♥", bg=PINK_BG, fg=color, font=("Georgia", 16)).pack(side="left", padx=2)

    def _load_image(self):
        # load a new image and initialize the game state for 5 new randomized differences
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")])
        if not path: return
        self.game_image = GameImage(path)
        self.game_image.apply_differences(self.generator)
        self.update() 
        self.mistakes = 0
        self.game_over = False
        self.has_revealed = False
        self.reveal_btn_top.config(state="normal")
        self.status_var.set("Find the 5 differences!")
        self._update_stats()
        self._refresh_canvases()

    def _on_click(self, event):
        # process player clicks on the modified image and validate them against regions
        if self.game_image is None or self.game_over: return
        cw, ch = self.right_canvas.winfo_width(), self.right_canvas.winfo_height()
        ix, iy = self.game_image.canvas_to_image_coords(event.x, event.y, cw, ch)
        idx = self.game_image.check_click(ix, iy)
        
        if idx >= 0:
            self.game_image.mark_found(idx, (0, 0, 255)) 
            self.total_found_overall += 1
            self._update_stats()
            self._refresh_canvases()
            
            if self.game_image.all_found():
                self.game_over = True
                self.reveal_btn_top.config(state="normal")
                self._show_win_popup()
        else:
            self.mistakes += 1
            self._update_stats()
            if self.mistakes >= MAX_MISTAKES:
                self.game_over = True
                self.reveal_btn_top.config(state="disabled") 
                self._show_fail_popup()

    def _refresh_canvases(self):
        # redraw both original and modified images on their canvases
        lw, lh = self.left_canvas.winfo_width(), self.left_canvas.winfo_height()
        l_tk = self.game_image.to_tk_image(self.game_image.original, lw, lh)
        self.left_canvas.delete("all")
        self.left_canvas.create_image(lw//2, lh//2, image=l_tk)
        self.left_canvas._img = l_tk
        rw, rh = self.right_canvas.winfo_width(), self.right_canvas.winfo_height()
        r_tk = self.game_image.to_tk_image(self.game_image.modified, rw, rh)
        self.right_canvas.delete("all")
        self.right_canvas.create_image(rw//2, rh//2, image=r_tk)
        self.right_canvas._img = r_tk

    def _update_stats(self):
        # update the UI counters for remaining diffs, mistakes, and total found
        if self.game_image:
            self.remaining_var.set(str(NUM_DIFFS - self.game_image.count_found()))
            self.mistakes_var.set(f"{self.mistakes} / 3")
            self.total_num_var.set(str(self.total_found_overall))
            self._render_hearts(self.mistakes)

    def _reveal_all(self):
        # reveal every remaining unfound difference and stop further guesses
        if self.game_image is None: return
        if self.has_revealed:
            self._show_already_revealed_popup()
            return
        if self.game_image.all_found():
            self._show_already_found_popup()
            return

        self.game_image.reveal_all() 
        self.has_revealed = True
        self.game_over = True
        self._refresh_canvases()
        self._show_reveal_popup()

    def _styled_popup(self, title, lines, title_color=None):
        # reusable popup builder for win, fail, reveal, and info dialogs
        popup = tk.Toplevel(self)
        popup.configure(bg=BG_CARD, highlightthickness=2, highlightbackground=BORDER_DARK)
        popup.overrideredirect(True)
        popup.grab_set()

        pw, ph = 460, 170
        sx = self.winfo_rootx() + (self.winfo_width() - pw) // 2
        sy = self.winfo_rooty() + (self.winfo_height() - ph) // 2
        popup.geometry(f"{pw}x{ph}+{sx}+{sy}")

        top_drag_bar = tk.Frame(popup, bg=PINK_DARK, height=8, cursor="fleur")
        top_drag_bar.pack(fill="x")

        def start_move(event):
            popup.x = event.x
            popup.y = event.y

        def do_move(event):
            deltax = event.x - popup.x
            deltay = event.y - popup.y
            x = popup.winfo_x() + deltax
            y = popup.winfo_y() + deltay
            popup.geometry(f"+{x}+{y}")

        top_drag_bar.bind("<Button-1>", start_move)
        top_drag_bar.bind("<B1-Motion>", do_move)

        inner = tk.Frame(popup, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=10, pady=8)

        tk.Label(
            inner,
            text=title,
            bg=BG_CARD,
            fg=title_color or PINK_DARK,
            font=("Georgia", 15, "bold")
        ).pack(pady=(2, 4))

        for line, col in lines:
            tk.Label(
                inner,
                text=line,
                bg=BG_CARD,
                fg=col,
                font=("Georgia", 11)
            ).pack()

        btn_frame = tk.Frame(inner, bg=BG_CARD)
        btn_frame.pack(pady=(10, 2))

        return popup, btn_frame

    def _show_win_popup(self):
        # show the success dialog when all 5 differences are found
        p, b = self._styled_popup("✦ MISSION COMPLETE ✦", [("Congratulations!", PINK_DARK), ("You found them all!", TEXT_DARK)])
        make_button(b, "Load Another Image", lambda: [p.destroy(), self._load_image()], style="pink", width=22, pady=6).pack(side="left", padx=10)
        make_button(b, "Stay", p.destroy, style="dark", width=12, pady=6).pack(side="left", padx=10)

    def _show_fail_popup(self):
        # show the failure dialog when the player reaches the mistake limit
        found = self.game_image.count_found()
        p, b = self._styled_popup("✘ MISSION FAILED ✘", [("Game Over.", RED_ERR), (f"You found {found} differences.", TEXT_DIM)], RED_ERR)
        make_button(b, "Load Another Image", lambda: [p.destroy(), self._load_image()], style="pink", width=22, pady=6).pack(side="left", padx=10)

    def _show_reveal_popup(self):
        # show confirmation after reveal all is used
        p, b = self._styled_popup("◈ REVEALED ◈", [("The differences are marked.", TEAL)], TEAL)
        make_button(b, "Load Another Image", lambda: [p.destroy(), self._load_image()], style="pink", width=22, pady=6).pack(side="left", padx=10)
        make_button(b, "Stay", p.destroy, style="dark", width=12, pady=6).pack(side="left", padx=10)

    def _show_already_revealed_popup(self):
        # show a warning when reveal all is pressed again
        p, b = self._styled_popup("◈ REVEALED ◈", [("Differences already revealed!", TEAL)], TEAL)
        make_button(b, "Load Another Image", lambda: [p.destroy(), self._load_image()], style="pink", width=22, pady=6).pack(side="left", padx=10)
        make_button(b, "Stay", p.destroy, style="dark", width=12, pady=6).pack(side="left", padx=10)

    def _show_already_found_popup(self):
        # show a message if the player already finished the current image
        p, b = self._styled_popup("✦ COMPLETED ✦", [
            ("You already found the 5 differences!", GREEN_OK),
        ], GREEN_OK)
        make_button(b, "Load Another Image", lambda: [p.destroy(), self._load_image()], style="pink", width=22, pady=6).pack(side="left", padx=10)
        make_button(b, "Stay", p.destroy, style="dark", width=12, pady=6).pack(side="left", padx=10)