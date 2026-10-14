from pathlib import Path
import os
import csv
import textwrap
import webbrowser
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import qrcode
from PIL import Image, ImageDraw, ImageFont


# CustomTkinter Dark Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class CertiCraftStudio(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CertiCraft - Studio Pro")

        # Maximize window while keeping normal title-bar controls.
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{screen_w}x{screen_h}+0+0")
        self.minsize(1050, 720)
        self.after(100, lambda: self.state("zoomed"))

        # Output folder and combined participant CSV
        self.output_dir = Path("generated_certificates")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.output_dir / "participants.csv"

        # Reuse the same ID/date during preview updates; refresh them after saving.
        self.current_cert_id = self.make_certificate_id()
        self.current_issue_date = datetime.now().strftime("%d %B %Y")

        # Assets
        self.canva_bg_img = None
        self.logo_img = None

        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_panel()
        self.after(200, self.update_preview)

    @staticmethod
    def make_certificate_id():
        # Microseconds help reduce the chance of duplicate IDs.
        return f"CERT-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    def create_sidebar(self):
        """Scrollable control sidebar."""
        sidebar = ctk.CTkScrollableFrame(self, width=450, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        ctk.CTkLabel(
            sidebar,
            text="CertiCraft Studio",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FFD700",
        ).pack(padx=15, pady=(15, 2))

        ctk.CTkLabel(
            sidebar, text="Certificate Studio",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(padx=15, pady=(0, 10))

        # 1. Canva and logo uploads
        sec1 = ctk.CTkFrame(sidebar)
        sec1.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            sec1, text="1. Canva & Logo Uploads",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(8, 4))

        btn_box = ctk.CTkFrame(sec1, fg_color="transparent")
        btn_box.pack(fill="x", padx=5, pady=2)

        self.btn_open_canva = ctk.CTkButton(
            btn_box, text="🎨 Open Canva",
            fg_color="#00C4CC", hover_color="#008080",
            text_color="black", font=ctk.CTkFont(weight="bold"),
            command=self.open_canva,
        )
        self.btn_open_canva.pack(side="left", expand=True, padx=2)

        self.btn_upload_bg = ctk.CTkButton(
            btn_box, text="🖼️ Upload Canva BG",
            fg_color="#3B82F6", hover_color="#2563EB",
            command=self.load_canva_bg,
        )
        self.btn_upload_bg.pack(side="right", expand=True, padx=2)

        self.btn_upload_logo = ctk.CTkButton(
            sec1, text="📌 Upload Logo (.png/.jpg)",
            fg_color="#8B5CF6", hover_color="#7C3AED",
            command=self.load_logo,
        )
        self.btn_upload_logo.pack(fill="x", padx=10, pady=(6, 8))

        # 2. Certificate fields
        sec2 = ctk.CTkFrame(sidebar)
        sec2.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            sec2, text="2. Certificate Details",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            sec2, text="Certificate Title (Supports Multiline)",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=10)
        self.entry_title = ctk.CTkEntry(sec2)
        self.entry_title.insert(0, "CERTIFICATE OF ACHIEVEMENT")
        self.entry_title.pack(fill="x", padx=10, pady=(0, 4))
        self.entry_title.bind("<KeyRelease>", self.update_preview)

        ctk.CTkLabel(
            sec2, text="Declaration Line (Editable)", font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=10)
        self.entry_fixed = ctk.CTkEntry(sec2)
        self.entry_fixed.insert(0, "THIS IS TO CERTIFY THAT")
        self.entry_fixed.pack(fill="x", padx=10, pady=(0, 4))
        self.entry_fixed.bind("<KeyRelease>", self.update_preview)

        ctk.CTkLabel(
            sec2, text="Participant Name (Cursive Styled)", font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=10)
        self.entry_name = ctk.CTkEntry(sec2)
        self.entry_name.insert(0, "")
        self.entry_name.pack(fill="x", padx=10, pady=(0, 4))
        self.entry_name.bind("<KeyRelease>", self.update_preview)

        ctk.CTkLabel(sec2, text="Participant Email ID", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10)
        self.entry_email = ctk.CTkEntry(sec2)
        self.entry_email.insert(0, "")
        self.entry_email.pack(fill="x", padx=10, pady=(0, 4))
        self.entry_email.bind("<KeyRelease>", self.update_preview)

        ctk.CTkLabel(sec2, text="Topic / Event Title", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10)
        self.entry_topic = ctk.CTkEntry(sec2)
        self.entry_topic.insert(0, "")
        self.entry_topic.pack(fill="x", padx=10, pady=(0, 4))
        self.entry_topic.bind("<KeyRelease>", self.update_preview)

        ctk.CTkLabel(
            sec2, text="Department / Organization Name", font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=10)
        self.entry_dept = ctk.CTkEntry(sec2)
        self.entry_dept.insert(0, "")
        self.entry_dept.pack(fill="x", padx=10, pady=(0, 8))
        self.entry_dept.bind("<KeyRelease>", self.update_preview)

        # 3. Logo controls
        sec3 = ctk.CTkFrame(sidebar)
        sec3.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            sec3, text="3. Logo Adjustment Controls",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(sec3, text="Logo X Position (%)", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10)
        self.slider_logo_x = ctk.CTkSlider(sec3, from_=2, to=80, command=self.update_preview)
        self.slider_logo_x.set(6)
        self.slider_logo_x.pack(fill="x", padx=10, pady=1)

        ctk.CTkLabel(sec3, text="Logo Y Position (%)", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10)
        self.slider_logo_y = ctk.CTkSlider(sec3, from_=2, to=80, command=self.update_preview)
        self.slider_logo_y.set(6)
        self.slider_logo_y.pack(fill="x", padx=10, pady=1)

        ctk.CTkLabel(sec3, text="Logo Size Scale", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10)
        self.slider_logo_scale = ctk.CTkSlider(sec3, from_=40, to=300, command=self.update_preview)
        self.slider_logo_scale.set(130)
        self.slider_logo_scale.pack(fill="x", padx=10, pady=(1, 8))

        # 4. Text position controls
        sec4 = ctk.CTkFrame(sidebar)
        sec4.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            sec4, text="4. Text Position Controls (%)",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(sec4, text="Title Y Position", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10)
        self.slider_title_y = ctk.CTkSlider(sec4, from_=5, to=40, command=self.update_preview)
        self.slider_title_y.set(15)
        self.slider_title_y.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(sec4, text="Declaration Line Y Position", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10)
        self.slider_decl_y = ctk.CTkSlider(sec4, from_=15, to=50, command=self.update_preview)
        self.slider_decl_y.set(28)
        self.slider_decl_y.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(sec4, text="Name Y Position", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10)
        self.slider_name_y = ctk.CTkSlider(sec4, from_=30, to=65, command=self.update_preview)
        self.slider_name_y.set(44)
        self.slider_name_y.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(sec4, text="Topic Y Position", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10)
        self.slider_topic_y = ctk.CTkSlider(sec4, from_=55, to=85, command=self.update_preview)
        self.slider_topic_y.set(64)
        self.slider_topic_y.pack(fill="x", padx=10, pady=(2, 8))

        # Actions
        self.btn_generate = ctk.CTkButton(
            sidebar,
            text="Generate & Save Final Certificate",
            fg_color="#10B981", hover_color="#059669",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.save_certificate,
        )
        self.btn_generate.pack(fill="x", padx=10, pady=(15, 5))

        self.btn_open_folder = ctk.CTkButton(
            sidebar, text="📁 Open Saved Folder",
            fg_color="transparent", border_width=1,
            text_color="white", command=self.open_generated_folder,
        )
        self.btn_open_folder.pack(fill="x", padx=10, pady=(0, 15))

    def create_main_panel(self):
        """Right-side live preview panel."""
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(
            top_bar, text="Live Canvas Preview Studio",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        self.preview_canvas = ctk.CTkLabel(main_frame, text="Loading Canvas...")
        self.preview_canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.lbl_status = ctk.CTkLabel(
            main_frame, text="Status: Ready",
            font=ctk.CTkFont(size=12), text_color="#10B981"
        )
        self.lbl_status.grid(row=2, column=0, padx=20, pady=(0, 10))

    def open_canva(self):
        webbrowser.open("https://www.canva.com/templates/?query=blank-landscape-certificate")

    def load_canva_bg(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            try:
                self.canva_bg_img = Image.open(file_path).convert("RGB")
                self.update_preview()
            except Exception as exc:
                messagebox.showerror("Image Error", f"Could not open background:\n{exc}")

    def load_logo(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            try:
                self.logo_img = Image.open(file_path).convert("RGBA")
                self.update_preview()
            except Exception as exc:
                messagebox.showerror("Logo Error", f"Could not open logo:\n{exc}")

    @staticmethod
    def get_cursive_font(size):
        font_candidates = ["brushscript.ttf", "BRUSHSCI.TTF", "corsiva.ttf", "edward.ttf", "arial.ttf"]
        for font_name in font_candidates:
            try:
                return ImageFont.truetype(font_name, size)
            except OSError:
                continue
        return ImageFont.load_default()

    @staticmethod
    def get_regular_font(size):
        for font_name in ["arial.ttf", "Arial.ttf"]:
            try:
                return ImageFont.truetype(font_name, size)
            except OSError:
                pass
        return ImageFont.load_default()

    def get_participant_details(self, cert_id, issue_date):
        """Collect details currently entered in the GUI."""
        return {
            "Participant Name": self.entry_name.get().strip(),
            "Participant Email": self.entry_email.get().strip(),
            "Event / Topic": self.entry_topic.get().strip(),
            "Department / Organization": self.entry_dept.get().strip(),
            "Certificate ID": cert_id,
            "Issue Date": issue_date,
            "Certificate Title": self.entry_title.get().strip(),
        }

    @staticmethod
    def make_qr_image(details, size=190):
        """Create a scannable QR whose payload is plain text, not a web link."""
        qr_text = "\n".join(f"{key}: {value or 'Not provided'}" for key, value in details.items())
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=4,
        )
        qr.add_data(qr_text)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        return qr_img.resize((size, size), Image.Resampling.NEAREST), qr_text

    def generate_certificate_image(self, cert_id=None, issue_date=None):
        w, h = 1920, 1080

        bg_color = (15, 23, 42)
        gold_color = (255, 215, 0)
        white_color = (248, 250, 252)
        sub_color = (148, 163, 184)

        if cert_id is None:
            cert_id = self.current_cert_id
        if issue_date is None:
            issue_date = self.current_issue_date

        if self.canva_bg_img:
            img = self.canva_bg_img.copy().resize((w, h), Image.Resampling.LANCZOS)
        else:
            img = Image.new("RGB", (w, h), bg_color)
            draw = ImageDraw.Draw(img)
            draw.rectangle([35, 35, w - 35, h - 35], outline=gold_color, width=5)
            draw.rectangle([50, 50, w - 50, h - 50], outline=gold_color, width=2)

        draw = ImageDraw.Draw(img)

        font_title = self.get_regular_font(64)
        font_fixed = self.get_regular_font(58)
        font_topic = self.get_regular_font(48)
        font_dept = self.get_regular_font(24)
        font_meta = self.get_regular_font(18)
        font_name_cursive = self.get_cursive_font(78)
        font_qr_label = self.get_regular_font(18)

        raw_title = self.entry_title.get().strip().upper() or "CERTIFICATE OF ACHIEVEMENT"
        fixed_text = self.entry_fixed.get().strip().upper() or "THIS IS TO CERTIFY THAT"
        name_text = self.entry_name.get().strip() or "Participant Name"
        topic_text = self.entry_topic.get().strip() or "Event / Workshop"
        dept_text = self.entry_dept.get().strip() or "Department / Organization"

        title_y = int((self.slider_title_y.get() / 100) * h)
        decl_y = int((self.slider_decl_y.get() / 100) * h)
        name_y = int((self.slider_name_y.get() / 100) * h)
        topic_y = int((self.slider_topic_y.get() / 100) * h)

        wrapped_title = "\n".join(textwrap.wrap(raw_title, width=32))
        draw.multiline_text(
            (w / 2, title_y), wrapped_title, fill=gold_color,
            font=font_title, anchor="mm", align="center", spacing=10
        )
        draw.text((w / 2, decl_y), fixed_text, fill=sub_color, font=font_fixed, anchor="mm")

        draw.text((w / 2, name_y), name_text, fill=white_color, font=font_name_cursive, anchor="mm")
        name_bbox = draw.textbbox((w / 2, name_y), name_text, font=font_name_cursive, anchor="mm")
        draw.line(
            [name_bbox[0] - 20, name_bbox[3] + 8, name_bbox[2] + 20, name_bbox[3] + 8],
            fill=gold_color, width=3
        )

        topic_full = f"For active participation in: {topic_text}"
        wrapped_topic = "\n".join(textwrap.wrap(topic_full, width=45))
        draw.multiline_text(
            (w / 2, topic_y), wrapped_topic, fill=white_color,
            font=font_topic, anchor="mm", align="center", spacing=8
        )

        # QR contains the participant details directly, so scanning works offline.
        details = self.get_participant_details(cert_id, issue_date)
        qr_img, _ = self.make_qr_image(details, size=190)
        qr_x = w - 245
        qr_y = h - 260
        img.paste(qr_img, (qr_x, qr_y))

        # Label directly above the QR code.
        draw = ImageDraw.Draw(img)
        draw.text(
            (qr_x + 95, qr_y - 14), "SCAN FOR DETAILS",
            fill=gold_color, font=font_qr_label, anchor="ms"
        )

        # Footer text is kept left of the QR to avoid overlap.
        footer_center_x = (w - 280) // 2
        draw.text(
            (footer_center_x, h - 110), dept_text,
            fill=gold_color, font=font_dept, anchor="mm"
        )
        meta_str = f"Issued to: {self.entry_email.get().strip() or 'Not provided'}   |   Date: {issue_date}   |   ID: {cert_id}"
        # Shorten exceptionally long footer text so it stays clear of the QR.
        meta_str = textwrap.shorten(meta_str, width=105, placeholder="...")
        draw.text(
            (footer_center_x, h - 70), meta_str,
            fill=sub_color, font=font_meta, anchor="mm"
        )

        # Logo overlay
        if self.logo_img:
            logo_x = int((self.slider_logo_x.get() / 100) * w)
            logo_y = int((self.slider_logo_y.get() / 100) * h)
            logo_scale = int(self.slider_logo_scale.get())
            aspect = self.logo_img.height / self.logo_img.width
            resized_logo = self.logo_img.resize(
                (logo_scale, max(1, int(logo_scale * aspect))),
                Image.Resampling.LANCZOS
            )
            img.paste(resized_logo, (logo_x, logo_y), resized_logo)

        return img, cert_id, issue_date

    def update_preview(self, *args):
        try:
            img, _, _ = self.generate_certificate_image()
            w, h = img.size
            preview_w = 880
            preview_h = int(preview_w * h / w)
            resized_img = img.resize((preview_w, preview_h), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(
                light_image=resized_img, dark_image=resized_img,
                size=(preview_w, preview_h)
            )
            self.preview_canvas.configure(image=ctk_img, text="")
            self.preview_canvas.image = ctk_img
        except Exception as exc:
            self.lbl_status.configure(text=f"Preview Error: {exc}", text_color="red")

    def append_participant_to_csv(self, details, certificate_filename):
        """Append a saved participant record to the combined CSV file."""
        fieldnames = [
            "Participant Name",
            "Participant Email",
            "Event / Topic",
            "Department / Organization",
            "Certificate ID",
            "Issue Date",
            "Certificate Title",
            "Certificate PDF",
        ]
        file_exists = self.csv_path.exists() and self.csv_path.stat().st_size > 0

        with self.csv_path.open("a", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            row = dict(details)
            row["Certificate PDF"] = certificate_filename
            writer.writerow(row)

    def save_certificate(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Participant Name Required", "Please enter the participant's name before generating the certificate.")
            return

        try:
            # Keep ID/date identical across the certificate, QR and CSV record.
            cert_id = self.current_cert_id
            issue_date = self.current_issue_date
            details = self.get_participant_details(cert_id, issue_date)

            img, _, _ = self.generate_certificate_image(cert_id, issue_date)
            name_slug = "".join(
                char for char in name if char.isalnum() or char in (" ", "_", "-")
            ).strip().replace(" ", "_") or "Participant"

            filename = f"{cert_id}_{name_slug}.pdf"
            save_path = self.output_dir / filename
            img.save(save_path, "PDF", resolution=100.0)

            # Save combined participant record after the certificate is written.
            self.append_participant_to_csv(details, filename)

            self.lbl_status.configure(
                text=f"Saved: {filename} | Participant record added to CSV",
                text_color="#10B981"
            )
            messagebox.showinfo(
                "Saved Successfully",
                f"Certificate PDF saved to:\n{save_path}\n\n"
                f"Participant record saved in:\n{self.csv_path.resolve()}\n\n"
                "The QR code stores participant details as text. Scan it with a phone camera/QR scanner."
            )

            # Prepare a fresh ID/date for the next participant.
            self.current_cert_id = self.make_certificate_id()
            self.current_issue_date = datetime.now().strftime("%d %B %Y")
            self.update_preview()

        except Exception as exc:
            messagebox.showerror("Error", f"Could not save certificate:\n{exc}")

    def open_generated_folder(self):
        abs_path = self.output_dir.resolve()
        try:
            if os.name == "nt":
                os.startfile(abs_path)
            elif os.uname().sysname == "Darwin":
                os.system(f'open "{abs_path}"')
            else:
                os.system(f'xdg-open "{abs_path}"')
        except Exception as exc:
            messagebox.showerror("Folder Error", f"Could not open the saved folder:\n{exc}")


if __name__ == "__main__":
    app = CertiCraftStudio()
    app.mainloop()

path = Path("/mnt/data/CertiCraft_Studio_QR_Updated.py")
path.write_text(code, encoding="utf-8")
print(f"Created: {path}")
