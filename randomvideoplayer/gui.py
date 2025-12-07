from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from randomvideoplayer.app_config import AppConfig, load_config, save_config
from randomvideoplayer.file_logger import FileLogger
from randomvideoplayer.mpv_utils import find_mpv_executable, build_mpv_command
from randomvideoplayer.playlist_builder import iter_webm_files, write_playlist_file


class WebmPlayerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title('Random Video Player (mpv)')

        self.config: AppConfig = load_config()

        self.mpv_process: Optional[subprocess.Popen] = None
        self.mpv_thread: Optional[threading.Thread] = None
        self.app_logger: Optional[FileLogger] = None
        self.playback_logger: Optional[FileLogger] = None

        self.create_widgets()
        self.apply_config_to_widgets()

        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    def apply_config_to_widgets(self) -> None:
        self.dir_var.set(self.config.directory)
        self.recursive_var.set(1 if self.config.recursive else 0)
        self.fullscreen_var.set(1 if self.config.fullscreen else 0)
        self.loop_var.set(1 if self.config.loop_playlist else 0)
        self.shuffle_var.set(1 if self.config.shuffle else 0)
        self.playlist_var.set(self.config.playlist_path)
        self.mpv_var.set(self.config.mpv_path)
        self.log_enabled_var.set(1 if self.config.logging_enabled else 0)
        self.log_path_var.set(self.config.logging_path)
        self.playback_log_enabled_var.set(
            1 if self.config.playback_log_enabled else 0,
        )
        self.playback_log_path_var.set(self.config.playback_log_path)
        self.update_logging_state()
        self.update_playback_logging_state()
        self.set_status('Idle')

    def read_widgets_to_config(self) -> AppConfig:
        return AppConfig(
            directory=self.dir_var.get(),
            recursive=bool(self.recursive_var.get()),
            fullscreen=bool(self.fullscreen_var.get()),
            loop_playlist=bool(self.loop_var.get()),
            shuffle=bool(self.shuffle_var.get()),
            playlist_path=self.playlist_var.get(),
            mpv_path=self.mpv_var.get(),
            logging_enabled=bool(self.log_enabled_var.get()),
            logging_path=self.log_path_var.get(),
            playback_log_enabled=bool(self.playback_log_enabled_var.get()),
            playback_log_path=self.playback_log_path_var.get(),
        )

    def create_widgets(self) -> None:
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky='nsew')

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        row = 0

        ttk.Label(main_frame, text='Video directory:').grid(
            row=row,
            column=0,
            sticky='w',
        )
        self.dir_var = tk.StringVar()
        dir_entry = ttk.Entry(main_frame, textvariable=self.dir_var)
        dir_entry.grid(row=row, column=1, sticky='ew', padx=5)
        ttk.Button(main_frame, text='Browse', command=self.browse_directory).grid(
            row=row,
            column=2,
            padx=5,
        )
        row += 1

        self.recursive_var = tk.IntVar(value=0)
        recursive_check = ttk.Checkbutton(
            main_frame,
            text='Search recursively',
            variable=self.recursive_var,
        )
        recursive_check.grid(row=row, column=1, sticky='w')
        row += 1

        ttk.Label(main_frame, text='mpv executable:').grid(
            row=row,
            column=0,
            sticky='w',
        )
        self.mpv_var = tk.StringVar()
        mpv_entry = ttk.Entry(main_frame, textvariable=self.mpv_var)
        mpv_entry.grid(row=row, column=1, sticky='ew', padx=5)
        ttk.Button(main_frame, text='Browse', command=self.browse_mpv).grid(
            row=row,
            column=2,
            padx=5,
        )
        row += 1

        ttk.Label(main_frame, text='Playlist file:').grid(
            row=row,
            column=0,
            sticky='w',
        )
        self.playlist_var = tk.StringVar()
        playlist_entry = ttk.Entry(main_frame, textvariable=self.playlist_var)
        playlist_entry.grid(row=row, column=1, sticky='ew', padx=5)
        ttk.Button(main_frame, text='Browse', command=self.browse_playlist).grid(
            row=row,
            column=2,
            padx=5,
        )
        row += 1

        options_frame = ttk.LabelFrame(main_frame, text='Playback options', padding=5)
        options_frame.grid(row=row, column=0, columnspan=3, sticky='ew', pady=(10, 5))
        options_frame.columnconfigure(0, weight=1)

        self.fullscreen_var = tk.IntVar(value=1)
        self.loop_var = tk.IntVar(value=1)
        self.shuffle_var = tk.IntVar(value=1)

        ttk.Checkbutton(
            options_frame,
            text='Fullscreen',
            variable=self.fullscreen_var,
        ).grid(row=0, column=0, sticky='w')
        ttk.Checkbutton(
            options_frame,
            text='Loop playlist',
            variable=self.loop_var,
        ).grid(row=0, column=1, sticky='w')
        ttk.Checkbutton(
            options_frame,
            text='Shuffle',
            variable=self.shuffle_var,
        ).grid(row=0, column=2, sticky='w')

        row += 1

        logging_frame = ttk.LabelFrame(main_frame, text='Logging', padding=5)
        logging_frame.grid(row=row, column=0, columnspan=3, sticky='ew', pady=(10, 5))
        logging_frame.columnconfigure(1, weight=1)

        self.log_enabled_var = tk.IntVar(value=0)
        log_enable_check = ttk.Checkbutton(
            logging_frame,
            text='Enable app log',
            variable=self.log_enabled_var,
            command=self.update_logging_state,
        )
        log_enable_check.grid(row=0, column=0, sticky='w')

        ttk.Label(logging_frame, text='Log file:').grid(row=1, column=0, sticky='w')
        self.log_path_var = tk.StringVar()
        self.log_entry = ttk.Entry(logging_frame, textvariable=self.log_path_var)
        self.log_entry.grid(row=1, column=1, sticky='ew', padx=5)
        self.log_browse_btn = ttk.Button(
            logging_frame,
            text='Browse',
            command=self.browse_log_file,
        )
        self.log_browse_btn.grid(row=1, column=2, padx=5)

        self.playback_log_enabled_var = tk.IntVar(value=0)
        playback_log_enable_check = ttk.Checkbutton(
            logging_frame,
            text='Enable playback history log',
            variable=self.playback_log_enabled_var,
            command=self.update_playback_logging_state,
        )
        playback_log_enable_check.grid(row=2, column=0, sticky='w', pady=(10, 0))

        ttk.Label(logging_frame, text='Playback log file:').grid(
            row=3,
            column=0,
            sticky='w',
        )
        self.playback_log_path_var = tk.StringVar()
        self.playback_log_entry = ttk.Entry(
            logging_frame,
            textvariable=self.playback_log_path_var,
        )
        self.playback_log_entry.grid(row=3, column=1, sticky='ew', padx=5)
        self.playback_log_browse_btn = ttk.Button(
            logging_frame,
            text='Browse',
            command=self.browse_playback_log_file,
        )
        self.playback_log_browse_btn.grid(row=3, column=2, padx=5)

        row += 1

        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=row, column=0, columnspan=3, sticky='ew', pady=(10, 0))
        buttons_frame.columnconfigure(0, weight=1)

        self.start_button = ttk.Button(
            buttons_frame,
            text='Start playback',
            command=self.start_playback,
        )
        self.start_button.grid(row=0, column=0, padx=5, sticky='ew')

        self.stop_button = ttk.Button(
            buttons_frame,
            text='Stop playback',
            command=self.stop_playback,
            state='disabled',
        )
        self.stop_button.grid(row=0, column=1, padx=5, sticky='ew')

        row += 1

        self.status_var = tk.StringVar(value='Idle')
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=row, column=0, columnspan=3, sticky='w', pady=(10, 0))

    def update_logging_state(self) -> None:
        enabled = bool(self.log_enabled_var.get())
        state = 'normal' if enabled else 'disabled'
        self.log_entry.configure(state=state)
        self.log_browse_btn.configure(state=state)

    def update_playback_logging_state(self) -> None:
        enabled = bool(self.playback_log_enabled_var.get())
        state = 'normal' if enabled else 'disabled'
        self.playback_log_entry.configure(state=state)
        self.playback_log_browse_btn.configure(state=state)

    def browse_directory(self) -> None:
        initial = self.dir_var.get() or str(Path.home())
        directory = filedialog.askdirectory(initialdir=initial)
        if directory:
            self.dir_var.set(directory)

    def browse_mpv(self) -> None:
        initial = self.mpv_var.get() or str(Path.home())
        path = filedialog.askopenfilename(
            title='Select mpv executable',
            initialdir=initial,
        )
        if path:
            self.mpv_var.set(path)

    def browse_playlist(self) -> None:
        initial = self.playlist_var.get() or str(Path.home())
        path = filedialog.asksaveasfilename(
            title='Select playlist file',
            initialfile=Path(initial).name,
            defaultextension='.m3u',
            filetypes=[('Playlist files', '*.m3u *.txt'), ('All files', '*.*')],
        )
        if path:
            self.playlist_var.set(path)

    def browse_log_file(self) -> None:
        initial = self.log_path_var.get() or str(Path.home())
        path = filedialog.asksaveasfilename(
            title='Select log file',
            initialfile=Path(initial).name,
            defaultextension='.log',
            filetypes=[('Log files', '*.log *.txt'), ('All files', '*.*')],
        )
        if path:
            self.log_path_var.set(path)

    def browse_playback_log_file(self) -> None:
        initial = self.playback_log_path_var.get() or str(Path.home())
        path = filedialog.asksaveasfilename(
            title='Select playback log file',
            initialfile=Path(initial).name,
            defaultextension='.log',
            filetypes=[('Log files', '*.log *.txt'), ('All files', '*.*')],
        )
        if path:
            self.playback_log_path_var.set(path)

    def set_status(self, text: str) -> None:
        self.status_var.set(text)
        if self.app_logger is not None:
            self.app_logger.log(text)

    def start_playback(self) -> None:
        if self.mpv_process is not None:
            messagebox.showwarning('Already running', 'mpv is already running.')
            return

        if self.app_logger is not None:
            self.app_logger.close()
        if self.playback_logger is not None:
            self.playback_logger.close()

        self.config = self.read_widgets_to_config()
        save_config(self.config)

        directory = Path(self.config.directory).expanduser()
        if not directory.is_dir():
            messagebox.showerror('Error', f'"{directory}" is not a directory.')
            return

        playlist_path = Path(self.config.playlist_path).expanduser()

        self.app_logger = FileLogger(
            enabled=self.config.logging_enabled,
            path=Path(self.config.logging_path).expanduser()
            if self.config.logging_enabled
            else None,
        )
        self.playback_logger = FileLogger(
            enabled=self.config.playback_log_enabled,
            path=Path(self.config.playback_log_path).expanduser()
            if self.config.playback_log_enabled
            else None,
        )

        if self.app_logger is not None:
            self.app_logger.log(
                f'Start playback with dir={directory}, '
                f'recursive={self.config.recursive}, fullscreen={self.config.fullscreen}, '
                f'loop={self.config.loop_playlist}, shuffle={self.config.shuffle}',
            )

        try:
            mpv_executable = find_mpv_executable(
                self.config.mpv_path.strip() or None,
            )
        except FileNotFoundError as exc:
            if self.app_logger is not None:
                self.app_logger.log(str(exc))
            messagebox.showerror('Error', str(exc))
            return

        self.set_status('Building playlist...')
        self.root.update_idletasks()

        try:
            files_iter = iter_webm_files(directory, recursive=self.config.recursive)
            count = write_playlist_file(
                files_iter,
                playlist_path,
                logger=self.app_logger,
            )
        except Exception as exc:
            msg = f'Failed to write playlist: {exc}'
            if self.app_logger is not None:
                self.app_logger.log(msg)
            messagebox.showerror('Error', msg)
            return

        if count == 0:
            messagebox.showerror('Error', 'No .webm files found.')
            return

        cmd = build_mpv_command(
            mpv_executable=mpv_executable,
            playlist_path=playlist_path,
            fullscreen=self.config.fullscreen,
            loop_playlist=self.config.loop_playlist,
            shuffle=self.config.shuffle,
        )

        if self.app_logger is not None:
            self.app_logger.log(
                f'Starting mpv: exe={mpv_executable}, playlist={playlist_path}, count={count}',
            )

        self.set_status(f'Starting mpv with {count} files...')
        try:
            self.mpv_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore',
            )
        except Exception as exc:
            msg = f'Failed to start mpv: {exc}'
            if self.app_logger is not None:
                self.app_logger.log(msg)
            messagebox.showerror('Error', msg)
            self.mpv_process = None
            return

        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')

        self.mpv_thread = threading.Thread(
            target=self.read_mpv_output,
            daemon=True,
        )
        self.mpv_thread.start()
        self.set_status('mpv running')

    def read_mpv_output(self) -> None:
        assert self.mpv_process is not None
        proc = self.mpv_process
        if proc.stdout is None:
            return

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            if 'error' in line.lower() or 'failed' in line.lower():
                if self.app_logger is not None:
                    self.app_logger.log(f'mpv: {line}')

            if line.startswith('Playing: '):
                path_str = line[len('Playing: ') :].strip()
                if self.playback_logger is not None:
                    self.playback_logger.log(path_str)

        code = proc.wait()
        if self.app_logger is not None:
            self.app_logger.log(f'mpv exited with code {code}')
        self.root.after(0, self.on_mpv_exit)

    def on_mpv_exit(self) -> None:
        self.mpv_process = None
        self.start_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        self.set_status('mpv exited')

    def stop_playback(self) -> None:
        if self.mpv_process is None:
            return
        if self.app_logger is not None:
            self.app_logger.log('Stop playback requested by user')
        try:
            self.mpv_process.terminate()
        except Exception:
            pass

    def on_close(self) -> None:
        if self.mpv_process is not None:
            try:
                self.mpv_process.terminate()
            except Exception:
                pass
        if self.app_logger is not None:
            self.app_logger.close()
        if self.playback_logger is not None:
            self.playback_logger.close()
        self.root.destroy()


def run_app() -> None:
    root = tk.Tk()
    app = WebmPlayerApp(root)
    root.mainloop()
