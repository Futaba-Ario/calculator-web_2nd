from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional

from .logic import CalculatorEngine

BUTTON_LAYOUT = [
    ["CE", "C", "⌫", "%"],
    ["7", "8", "9", "÷"],
    ["4", "5", "6", "×"],
    ["1", "2", "3", "-"],
    ["±", "0", ".", "+"],
]

COMMAND_MAP: Dict[str, str] = {
    "÷": "/",
    "×": "*",
}

KEY_COMMANDS: Dict[str, str] = {
    "Return": "=",
    "KP_Enter": "=",
    "plus": "+",
    "KP_Add": "+",
    "minus": "-",
    "KP_Subtract": "-",
    "asterisk": "*",
    "KP_Multiply": "*",
    "slash": "/",
    "KP_Divide": "/",
    "BackSpace": "⌫",
    "Delete": "CE",
    "Escape": "C",
    "F9": "±",
    "percent": "%",
}


class CalculatorUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.engine = CalculatorEngine()
        self.expression_var = tk.StringVar()
        self.display_var = tk.StringVar(value="0")
        self.status_var = tk.StringVar()

        self._configure_root()
        self._build_layout()
        self._bind_keys()
        self._update_display(*self.engine.get_display())

    def _configure_root(self) -> None:
        self.root.title("Python Tkinter Calculator")
        self.root.resizable(False, False)
        self.root.columnconfigure(0, weight=1)

    def _build_layout(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        container = ttk.Frame(self.root, padding=12)
        container.grid(row=0, column=0, sticky="nsew")

        self.expression_label = ttk.Label(
            container,
            textvariable=self.expression_var,
            anchor="e",
            font=("Segoe UI", 12),
            foreground="#555555",
        )
        self.expression_label.grid(row=0, column=0, columnspan=4, sticky="ew")

        self.display_label = tk.Label(
            container,
            textvariable=self.display_var,
            anchor="e",
            font=("Segoe UI", 28, "bold"),
            bg="#ffffff",
            fg="#202020",
            relief="groove",
            padx=12,
            pady=8,
        )
        self.display_label.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(4, 8))

        self.status_label = ttk.Label(
            container,
            textvariable=self.status_var,
            anchor="e",
            font=("Segoe UI", 10),
            foreground="#c53030",
        )
        self.status_label.grid(row=2, column=0, columnspan=4, sticky="ew")

        button_frame = ttk.Frame(container)
        button_frame.grid(row=3, column=0, columnspan=4, sticky="nsew")
        for col in range(4):
            button_frame.columnconfigure(col, weight=1)
        for idx in range(len(BUTTON_LAYOUT) + 1):
            button_frame.rowconfigure(idx, weight=1)

        for r, row in enumerate(BUTTON_LAYOUT):
            for c, label in enumerate(row):
                self._create_button(button_frame, label, r, c)

        equal_button = ttk.Button(
            button_frame,
            text="=",
            command=lambda: self._handle_command("="),
            style="Accent.TButton",
        )
        equal_button.grid(
            row=len(BUTTON_LAYOUT), column=0, columnspan=4, sticky="nsew", pady=(6, 0)
        )

    def _create_button(
        self, parent: ttk.Frame, label: str, row: int, column: int
    ) -> None:
        button = ttk.Button(
            parent,
            text=label,
            command=lambda lbl=label: self._handle_command(lbl),
        )
        button.grid(row=row, column=column, sticky="nsew", padx=2, pady=2)

    def _bind_keys(self) -> None:
        self.root.bind("<Key>", self._on_key_press)

    def _on_key_press(self, event: tk.Event) -> None:
        if event.char and event.char.isdigit():
            self._handle_command(event.char)
            return
        if event.char == ".":
            self._handle_command(".")
            return
        if event.char == "%":
            self._handle_command("%")
            return
        command = KEY_COMMANDS.get(event.keysym)
        if command:
            self._handle_command(command)

    def _handle_command(self, label: str) -> None:
        command = COMMAND_MAP.get(label, label)
        expression, current, error = self.engine.process(command)
        self._update_display(expression, current, error)

    def _update_display(
        self, expression: str, current: str, error: Optional[str]
    ) -> None:
        self.expression_var.set(expression)
        self.display_var.set(current)
        if error:
            self.status_var.set(error)
            self.display_label.configure(fg="#c53030")
        else:
            self.status_var.set("")
            self.display_label.configure(fg="#202020")


def launch() -> None:
    root = tk.Tk()
    CalculatorUI(root)
    root.mainloop()
