# ui_panels.py
import customtkinter as ctk

def build_main_panel(parent, state, servo):
    """
    Builds a single panel:
      - shows current pan/tilt
      - sliders for pan/tilt
      - Home button
      - safe range inputs (optional quick edit)
      - keyboard help
    """
    frame = ctk.CTkFrame(parent, corner_radius=12)
    frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=0)
    frame.grid_columnconfigure(0, weight=1)

    title = ctk.CTkLabel(frame, text="Pi Servo Test (Pan/Tilt)", font=ctk.CTkFont(size=18, weight="bold"))
    title.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")

    pos_var = ctk.StringVar(value="")
    pos_label = ctk.CTkLabel(frame, textvariable=pos_var)
    pos_label.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")

    def refresh_pos():
        pos_var.set(f"Pan: {servo.pan_angle}°   Tilt: {servo.tilt_angle}°   | Safe: "
                    f"Pan[{servo.pan_min},{servo.pan_max}] Tilt[{servo.tilt_min},{servo.tilt_max}]")

    # --- Pan slider ---
    pan_row = ctk.CTkFrame(frame, fg_color="transparent")
    pan_row.grid(row=2, column=0, padx=12, pady=6, sticky="ew")
    pan_row.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(pan_row, text="Pan").grid(row=0, column=0, padx=(0, 8), sticky="w")
    pan_slider = ctk.CTkSlider(
        pan_row, from_=0, to=180, number_of_steps=180,
        command=lambda v: (servo.set_pan_tilt(int(float(v)), servo.tilt_angle), refresh_pos())
    )
    pan_slider.grid(row=0, column=1, sticky="ew")
    pan_slider.set(state.pan)

    # --- Tilt slider ---
    tilt_row = ctk.CTkFrame(frame, fg_color="transparent")
    tilt_row.grid(row=3, column=0, padx=12, pady=6, sticky="ew")
    tilt_row.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(tilt_row, text="Tilt").grid(row=0, column=0, padx=(0, 8), sticky="w")
    tilt_slider = ctk.CTkSlider(
        tilt_row, from_=0, to=180, number_of_steps=180,
        command=lambda v: (servo.set_pan_tilt(servo.pan_angle, int(float(v))), refresh_pos())
    )
    tilt_slider.grid(row=0, column=1, sticky="ew")
    tilt_slider.set(state.tilt)

    # Buttons row
    btn_row = ctk.CTkFrame(frame, fg_color="transparent")
    btn_row.grid(row=4, column=0, padx=12, pady=(10, 12), sticky="ew")

    def do_home():
        servo.home(90, 90)
        pan_slider.set(servo.pan_angle)
        tilt_slider.set(servo.tilt_angle)
        refresh_pos()

    ctk.CTkButton(btn_row, text="Home (90,90)", command=do_home).pack(side="left", padx=(0, 8))

    help_text = "Keyboard: Arrow / WASD to move, Space=Home, Esc=Quit"
    ctk.CTkLabel(frame, text=help_text).grid(row=5, column=0, padx=12, pady=(0, 12), sticky="w")

    refresh_pos()
    return frame, pan_slider, tilt_slider, refresh_pos
