#modules/RSSFeedReaderUI.py

import os
import asyncio
import threading
from PySide6 import QtWidgets as qtw
from PySide6 import QtCore as qtc
from PySide6 import QtGui as qtg
from PySide6.QtGui import QDesktopServices
import json
import configparser
import feedparser
import webbrowser
from modules.rss_feed_reader import RSSFeedReader, RSSFeedReaderError
from modules.tooltip import ToolTip
from modules.settings import settings
from modules.settings import filter_sort_settings
from modules.logging.logger import setup_logger

logger = setup_logger('RSSFeedReaderUI')

class RSSFeedReaderUI(qtw.QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Initializing RSS Feed Reader...")
        self.setWindowTitle("RSS Feed Reader")
        self.rss_feed_reader = RSSFeedReader()
        logger.info("Loading feeds and configuration...")
        self.load_feeds()
        self.load_config()
        settings.load_settings(self)  
        filter_sort_settings.load_filter_sort_settings(self)
        self.url_cooldown = False

        width, height = 600, 700
        self.resize(width, height)

        self.create_widgets()

    def open_url(self, url):
        logger.info("Opening url...")
        if not self.url_cooldown:
            self.url_cooldown = True
            threading.Thread(target=self.open_url_thread, args=(url.toString(),)).start()
            qtc.QTimer.singleShot(5000, self.reset_url_cooldown)
        else:
            qtw.QMessageBox.information(self, "Cooldown", "Please wait before clicking the URL again.")

    def open_url_thread(self, url):
        webbrowser.open(url)

    def reset_url_cooldown(self):
        self.url_cooldown = False

    def load_config(self):
        logger.info("Loading configuration from config.ini...")
        try:
            settings_folder = "settings"
            config_path = os.path.join(settings_folder, "config.ini")
            config = configparser.ConfigParser()
            config.read(config_path)

            self.font_family = config.get("Font", "family", fallback="MS Sans Serif")
            self.font_size = config.getfloat("Font", "size", fallback=1.1)
            self.font_color = config.get("Font", "color", fallback="#ffffff")

            self.main_window_color = config.get("Colors", "main_window_color", fallback="#333333")
            self.window_bg = config.get("Colors", "window_bg", fallback="#000000")
            self.spinbox_bg = config.get("Colors", "spinbox_bg", fallback="#808080")
            self.button_bg = config.get("Colors", "button_bg", fallback="#696969")

        except Exception as e:
            logger.exception("Error occurred while loading configuration.")
            qtw.QMessageBox.critical(self, "Configuration Error", "Failed to load configuration. Using default values.")
            
    def create_widgets(self):
        logger.info("Creating UI widgets...")

        icon_size = 32
        settings_img = qtg.QPixmap("assets/icons/settings_icon.png")
        settings_img = settings_img.scaled(icon_size, icon_size)

        try:
            font_size = int(self.font_size * 10)
            font_style = f"{self.font_family}, {font_size}"

            central_widget = qtw.QWidget(self)
            central_widget.setStyleSheet(f"background-color: {self.main_window_color};")
            self.setCentralWidget(central_widget)
            layout = qtw.QVBoxLayout(central_widget)

            settings_frame = qtw.QFrame(central_widget)
            settings_frame.setStyleSheet(f"background-color: {self.window_bg};")
            settings_layout = qtw.QHBoxLayout(settings_frame)
            settings_layout.setContentsMargins(5, 5, 5, 5)
            layout.addWidget(settings_frame)

            filter_sort_button = qtw.QPushButton("Filter/Sort", settings_frame)
            filter_sort_button.setStyleSheet(f"background-color: {self.window_bg}; color: {self.font_color}; font: {font_style}; border: none;")
            filter_sort_button.clicked.connect(lambda: filter_sort_settings.open_filter_settings(self))
            settings_layout.addWidget(filter_sort_button)
            ToolTip.setToolTip(filter_sort_button, "Open Filter/Sort Settings")

            self.settings_button = qtw.QPushButton(settings_frame)
            self.settings_button.setIcon(settings_img)
            self.settings_button.setStyleSheet(f"background-color: {self.window_bg}; color: {self.font_color}; font: {font_style}; border: none;")
            self.settings_button.clicked.connect(lambda: settings.open_settings(self))
            settings_layout.addWidget(self.settings_button)
            ToolTip.setToolTip(self.settings_button, "Open Settings")

            self.feed_url_label = qtw.QLabel("Feed URL:", central_widget)
            self.feed_url_label.setStyleSheet(f"color: {self.font_color}; font: {font_style};")
            layout.addWidget(self.feed_url_label)

            self.feed_url_entry = qtw.QLineEdit(central_widget)
            self.feed_url_entry.setStyleSheet(f"background-color: #C0C0C0; color: black; font: {font_style};")
            layout.addWidget(self.feed_url_entry)
            ToolTip.setToolTip(self.feed_url_entry, "Enter the URL of the RSS feed")

            self.category_label = qtw.QLabel("Category:", central_widget)
            self.category_label.setStyleSheet(f"color: {self.font_color}; font: {font_style};")
            layout.addWidget(self.category_label)

            self.category_entry = qtw.QLineEdit(central_widget)
            self.category_entry.setStyleSheet(f"background-color: #C0C0C0; color: black; font: {font_style};")
            layout.addWidget(self.category_entry)
            ToolTip.setToolTip(self.category_entry, "Enter a category for the RSS feed")

            self.add_feed_button = qtw.QPushButton("Add Feed", central_widget)
            self.add_feed_button.setStyleSheet(f"background-color: {self.button_bg}; color: {self.font_color}; font: {font_style};")
            self.add_feed_button.clicked.connect(self.add_feed)
            layout.addWidget(self.add_feed_button)
            ToolTip.setToolTip(self.add_feed_button, "Add a new RSS feed")

            self.feeds_listbox = qtw.QListWidget(central_widget)
            self.feeds_listbox.setStyleSheet(f"background-color: {self.window_bg}; color: {self.font_color}; font: {font_style};")
            self.feeds_listbox.itemClicked.connect(self.on_feed_click)
            layout.addWidget(self.feeds_listbox)

            button_frame = qtw.QFrame(central_widget)
            button_frame.setStyleSheet(f"background-color: {self.window_bg};")
            button_layout = qtw.QHBoxLayout(button_frame)
            button_layout.setContentsMargins(5, 5, 5, 5)
            layout.addWidget(button_frame)

            self.start_feed_button = qtw.QPushButton("Start Feed", button_frame)
            self.start_feed_button.setStyleSheet(f"background-color: {self.button_bg}; color: {self.font_color}; font: {font_style};")
            self.start_feed_button.clicked.connect(self.start_feed)
            self.start_feed_button.setEnabled(False)
            button_layout.addWidget(self.start_feed_button)
            ToolTip.setToolTip(self.start_feed_button, "Start the selected RSS feed")

            self.remove_feed_button = qtw.QPushButton("Remove Feed", button_frame)
            self.remove_feed_button.setStyleSheet(f"background-color: {self.button_bg}; color: {self.font_color}; font: {font_style};")
            self.remove_feed_button.clicked.connect(self.remove_feed)
            self.remove_feed_button.setEnabled(False)
            button_layout.addWidget(self.remove_feed_button)
            ToolTip.setToolTip(self.remove_feed_button, "Remove the selected RSS feed")

            self.entries_listbox = qtw.QListWidget(central_widget)
            self.entries_listbox.setStyleSheet(f"background-color: {self.window_bg}; color: {self.font_color}; font: {font_style};")
            self.entries_listbox.itemClicked.connect(self.on_entry_click)
            layout.addWidget(self.entries_listbox)

            entry_button_frame = qtw.QFrame(central_widget)
            entry_button_frame.setStyleSheet(f"background-color: {self.window_bg};")
            entry_button_layout = qtw.QHBoxLayout(entry_button_frame)
            entry_button_layout.setContentsMargins(5, 5, 5, 5)
            layout.addWidget(entry_button_frame)

            self.show_entry_button = qtw.QPushButton("Show Entry Details", entry_button_frame)
            self.show_entry_button.setStyleSheet(f"background-color: {self.button_bg}; color: {self.font_color}; font: {font_style};")
            self.show_entry_button.clicked.connect(self.show_entry_details)
            self.show_entry_button.setEnabled(False)
            entry_button_layout.addWidget(self.show_entry_button)
            ToolTip.setToolTip(self.show_entry_button, "Show details of the selected entry")

            self.remove_entry_button = qtw.QPushButton("Remove Entry", entry_button_frame)
            self.remove_entry_button.setStyleSheet(f"background-color: {self.button_bg}; color: {self.font_color}; font: {font_style};")
            self.remove_entry_button.clicked.connect(self.remove_entry)
            self.remove_entry_button.setEnabled(False)
            entry_button_layout.addWidget(self.remove_entry_button)
            ToolTip.setToolTip(self.remove_entry_button, "Remove the selected entry")

            self.entry_details_text = qtw.QTextBrowser(central_widget)
            self.entry_details_text.setStyleSheet(f"""
                QTextBrowser {{
                    background-color: {self.window_bg};
                    color: {self.font_color};
                    font: {font_style};
                }}
                QTextBrowser a {{
                    text-decoration: none;
                    color: {self.font_color};
                }}
                QTextBrowser a:hover {{
                    text-decoration: underline;
                }}
            """)
            self.entry_details_text.setReadOnly(True)
            self.entry_details_text.setOpenExternalLinks(True)
            self.entry_details_text.setTextInteractionFlags(qtc.Qt.TextBrowserInteraction | qtc.Qt.LinksAccessibleByMouse)
            self.entry_details_text.viewport().setCursor(qtg.QCursor(qtc.Qt.PointingHandCursor))
            layout.addWidget(self.entry_details_text)

            self.refresh_feeds()
        except Exception as e:
            logger.exception("Error occurred while creating widgets.")
            qtw.QMessageBox.critical(self, "Widget Creation Error", "Failed to create widgets.")

    def on_feed_click(self, item):
        self.start_feed_button.setEnabled(True)
        self.remove_feed_button.setEnabled(True)

    def on_entry_click(self, item):
        self.show_entry_button.setEnabled(True)
        self.remove_entry_button.setEnabled(True)

    def remove_entry(self):
        selected_entry = self.entries_listbox.currentItem().text()
        if selected_entry:
            feed_url = self.feeds_listbox.currentItem().text().split(" - ")[0]
            self.rss_feed_reader.remove_entry(feed_url, selected_entry)
            self.entries_listbox.takeItem(self.entries_listbox.currentRow())
            self.entry_details_text.clear()
            self.show_entry_button.setEnabled(False)
            self.remove_entry_button.setEnabled(False)
        else:
            qtw.QMessageBox.critical(self, "Error", "Please select an entry to remove.")

    def show_entry_details(self):
        selected_entry = self.entries_listbox.currentItem().text()
        if selected_entry:
            feed_url = self.feeds_listbox.currentItem().text().split(" - ")[0]
            entries = self.rss_feed_reader.get_feed_entries(feed_url)
            for entry in entries:
                if entry.title == selected_entry:
                    entry_details = self.rss_feed_reader.get_entry_details(entry)
                    self.entry_details_text.clear()
                    self.entry_details_text.append(f"<h3>Title: {entry_details['title']}</h3>")

                    url_link = f"<a href=\"{entry_details['link']}\">{entry_details['link']}</a>"
                    self.entry_details_text.append(f"<p><strong>Link:</strong> {url_link}</p>")

                    self.entry_details_text.append(f"<p><strong>Published:</strong> {entry_details['published']}</p>")
                    self.entry_details_text.append(f"<p><strong>Summary:</strong> {entry_details['summary']}</p>")

                    break
        else:
            qtw.QMessageBox.critical(self, "Error", "Please select an entry to show details.")

    def open_url_in_browser(self, url):
        QDesktopServices.openUrl(url)

    def start_feed(self):
        selected_feed = self.feeds_listbox.currentItem().text()
        if selected_feed:
            feed_url = selected_feed.split(" - ")[0]
            entries = self.rss_feed_reader.get_feed_entries(feed_url)
            entries = self.rss_feed_reader.sort_entries(entries, self.sorting)
            self.entries_listbox.clear()
            for entry in entries:
                self.entries_listbox.addItem(entry.title)
        else:
            qtw.QMessageBox.critical(self, "Error", "Please select a feed to start.")

    def add_feed(self):
        logger.info("Adding a new feed...")
        try:
            feed_url = self.feed_url_entry.text()
            category = self.category_entry.text()

            if not feed_url:
                qtw.QMessageBox.critical(self, "Error", "Please enter a feed URL.")
                return

            self.rss_feed_reader.add_feed(feed_url, category)
            self.refresh_feeds()
            self.feed_url_entry.clear()
            self.category_entry.clear()
            self.save_feeds()
        except RSSFeedReaderError as e:
            logger.exception("Error occurred while adding feed.")
            qtw.QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            logger.exception("Unexpected error occurred while adding feed.")
            qtw.QMessageBox.critical(self, "Error", "An unexpected error occurred.")

    def remove_feed(self):
        try:
            selected_feed = self.feeds_listbox.currentItem().text()

            if not selected_feed:
                qtw.QMessageBox.critical(self, "Error", "Please select a feed to remove.")
                return

            feed_url = selected_feed.split(" - ")[0]

            self.rss_feed_reader.remove_feed(feed_url)
            self.save_feeds()
            self.refresh_feeds()
        except RSSFeedReaderError as e:
            logger.exception("Error occurred while removing feed.")
            qtw.QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            logger.exception("Unexpected error occurred while removing feed.")
            qtw.QMessageBox.critical(self, "Error", "An unexpected error occurred.")

    def refresh_feeds(self):
        logger.info("Refreshing feeds...")
        try:
            self.feeds_listbox.clear()
            self.entries_listbox.clear()
            self.entry_details_text.clear()

            feeds = self.rss_feed_reader.get_feeds()
            for feed in feeds:
                self.feeds_listbox.addItem(f"{feed.url} - {feed.category}")

            qtc.QTimer.singleShot(self.refresh_interval_mins * 60000, self.refresh_feeds)
        except Exception as e:
            logger.exception("Error occurred while refreshing feeds.")
            qtw.QMessageBox.critical(self, "Error", "An error occurred while refreshing feeds.")

    def load_feeds(self):
        logger.info("Loading feeds...")
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "feeds.json")

            if os.path.exists(config_path):
                with open(config_path, "r") as file:
                    feed_data = json.load(file)
                    self.loaded_entries = {}
                    for category, data in feed_data.items():
                        for feed in data["feeds"]:
                            self.rss_feed_reader.add_feed(feed["url"], category)
                            entries = data["entries"].get(feed["url"], [])
                            self.loaded_entries[feed["url"]] = []
                            for entry_details in entries:
                                entry = feedparser.FeedParserDict(entry_details)
                                self.loaded_entries[feed["url"]].append(entry)
        except Exception as e:
            logger.exception("Error occurred while loading feeds.")

    def on_feed_select(self, item):
        try:
            selected_feed = item.text()

            if not selected_feed:
                return

            feed_url = selected_feed.split(" - ")[0]

            entries = self.rss_feed_reader.get_feed_entries(feed_url)
            entries = self.rss_feed_reader.sort_entries(entries, self.sorting)
            self.entries_listbox.clear()

            for entry in entries:
                self.entries_listbox.addItem(entry.title)

            self.entries_listbox.itemClicked.connect(self.on_entry_select)
        except RSSFeedReaderError as e:
            logger.exception("Error occurred while selecting feed.")
            qtw.QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            logger.exception("Unexpected error occurred while selecting feed.")
            qtw.QMessageBox.critical(self, "Error", "An unexpected error occurred.")

    def on_entry_select(self, item):
        try:
            selected_entry = item.text()

            if not selected_entry:
                return

            feed_url = self.feeds_listbox.currentItem().text().split(" - ")[0]
            entries = self.rss_feed_reader.get_feed_entries(feed_url)

            for entry in entries:
                if entry.title == selected_entry:
                    entry_details = self.rss_feed_reader.get_entry_details(entry)
                    self.entry_details_text.clear()
                    self.entry_details_text.append(f"Title: {entry_details['title']}\n\n")
                    self.entry_details_text.append(f"Link: {entry_details['link']}\n\n")
                    self.entry_details_text.append(f"Published: {entry_details['published']}\n\n")
                    self.entry_details_text.append(f"Summary: {entry_details['summary']}")
                    break
        except RSSFeedReaderError as e:
            logger.exception("Error occurred while selecting entry.")
            qtw.QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            logger.exception("Unexpected error occurred while selecting entry.")
            qtw.QMessageBox.critical(self, "Error", "An unexpected error occurred.")

    def save_feeds(self):
        logger.info("Saving feeds...")
        try:
            feeds = self.rss_feed_reader.get_feeds()
            feed_data = {}

            for feed in feeds:
                category = feed.category
                if category not in feed_data:
                    feed_data[category] = {"feeds": [], "entries": {}}

                feed_data[category]["feeds"].append({"url": feed.url})

                try:
                    entries = self.rss_feed_reader.get_feed_entries(feed.url)
                    feed_data[category]["entries"][feed.url] = []

                    for entry in entries:
                        try:
                            entry_details = self.rss_feed_reader.get_entry_details(entry)
                            feed_data[category]["entries"][feed.url].append(entry_details)
                        except RSSFeedReaderError as e:
                            logger.warning(f"Skipping entry due to missing details: {str(e)}")
                except RSSFeedReaderError as e:
                    logger.warning(f"Skipping feed due to parsing error: {str(e)}")
                    continue

            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "feeds.json")
            with open(config_path, "w") as file:
                json.dump(feed_data, file, indent=2)
        except Exception as e:
            logger.exception("Error occurred while saving feeds.")

    def closeEvent(self, event):
        #self.save_feeds()
        logger.info("RSS Feed Reader closed.")
        event.accept()
