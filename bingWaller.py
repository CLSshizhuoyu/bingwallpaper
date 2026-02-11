import sys
import requests
import os
import json
import random
from urllib.parse import urlparse
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout,
                             QMessageBox, QProgressBar, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import (QFont, QPalette, QColor, QPixmap, QBrush,
                         QImage, QIcon)  # 新增QIcon导入


# 原有功能函数保持不变
def modify_image_metadata(input_path, output_path, title, copyright):
    try:
        with Image.open(input_path) as img:
            exif_data = img.getexif() or {}
            title_tag_id = next(
                (tid for tid, tname in TAGS.items() if tname == "ImageDescription"), None)
            copyright_tag_id = next(
                (tid for tid, tname in TAGS.items() if tname == "Copyright"), None)
            if title_tag_id:
                exif_data[title_tag_id] = title
            if copyright_tag_id:
                exif_data[copyright_tag_id] = copyright
            img.save(output_path, exif=exif_data)
    except Exception as e:
        pass


def get_file_extension(content_type):
    if not content_type:
        return '.jpg'
    content_type = content_type.lower()
    ext_map = {
        'image/jpeg': '.jpg', 'image/png': '.png', 'image/gif': '.gif',
        'image/webp': '.webp', 'image/svg+xml': '.svg', 'image/bmp': '.bmp'
    }
    return ext_map.get(content_type, '.jpg')


def get_program_directory():
    """获取程序所在文件夹的绝对路径（适配PyInstaller打包）"""
    import sys
    if getattr(sys, 'frozen', False):
        # 打包后的EXE运行环境
        return Path(sys.executable).resolve().parent
    else:
        # 开发环境（普通Python运行）
        return Path(__file__).resolve().parent


def crawl_webpage(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except (json.JSONDecodeError, Exception):
        return None


def download_image_from_url(image_url, image_name, date):
    try:
        program_dir = get_program_directory()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(
            image_url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type')
        extension = get_file_extension(content_type)
        today = date
        filename = f"{today}{extension}"
        file_path = os.path.join(program_dir, filename)
        counter = 1
        while os.path.exists(file_path):
            filename = f"{today}_{counter}{extension}"
            file_path = os.path.join(program_dir, filename)
            counter += 1
        new_title = image_name.split(
            ' (')[0] if ' (' in image_name else image_name
        new_copyright = image_name.split(
            '© ')[1][:-1] if '© ' in image_name else ""
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        modify_image_metadata(file_path, file_path, new_title, new_copyright)
        return file_path
    except Exception:
        return None


def main_logic(Index=0):
    target_url = f"https://bing.biturl.top/?resolution=UHD&format=json&mkt=en-US&index={Index}"
    json_data = crawl_webpage(target_url)
    if not json_data:
        return "无法继续执行，JSON数据获取失败"
    image_url = json_data.get('url')
    image_name = json_data.get('copyright')
    date = json_data.get('end_date')
    if image_url:
        file_path = download_image_from_url(image_url, image_name, date)
        return f"图片下载完成，保存路径：{file_path}" if file_path else "图片下载失败"
    else:
        return "JSON数据中未找到'url'字段"


class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(str)

    def __init__(self, index_str):
        super().__init__()
        self.index_str = index_str

    def run(self):
        try:
            if ',' in self.index_str:
                start = min(7, max(0, int(self.index_str.split(',')[0])))
                end = min(7, max(0, int(self.index_str.split(',')[1])))
                total = end - start + 1
                current = 0
                for i in range(start, end + 1):
                    current += 1
                    self.progress_signal.emit(int(current / total * 100))
                    result = main_logic(i)
                self.result_signal.emit(f"批量下载完成！最后结果：{result}")
            else:
                self.progress_signal.emit(50)
                result = main_logic(int(self.index_str))
                self.progress_signal.emit(100)
                self.result_signal.emit(result)
        except Exception as e:
            self.result_signal.emit(f"执行出错：{str(e)}")
            self.progress_signal.emit(0)


class BingWallpaperDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.init_background()
        self.init_ui()

    def init_background(self):
        program_dir = get_program_directory()
        bg_files = ["bj1.jpg", "bj2.jpg", "bj3.jpg"]
        bg_paths = [os.path.join(program_dir, file) for file in bg_files]
        valid_bg_paths = [path for path in bg_paths if os.path.exists(path)]
        self.bg_pixmap = None
        if valid_bg_paths:
            selected_bg = random.choice(valid_bg_paths)
            self.bg_pixmap = QPixmap(selected_bg)
            if not self.bg_pixmap.isNull():
                self.bg_width = self.bg_pixmap.width()
                self.bg_height = self.bg_pixmap.height()

    def init_ui(self):
        self.setWindowTitle('Bing壁纸下载器')

        # ========== 新增：设置窗口图标 ==========
        program_dir = get_program_directory()
        icon_path = os.path.join(program_dir, "icon.ico")
        if os.path.exists(icon_path):  # 检查图标文件是否存在
            self.setWindowIcon(QIcon(icon_path))

        # 设置窗口尺寸
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            self.setFixedSize(self.bg_width, self.bg_height)
        else:
            self.setFixedSize(500, 300)

        # 全局字体调整：主字体楷体12，提示文字缩小为楷体10
        main_font = QFont("楷体", 12)
        tip_font = QFont("楷体", 10)
        self.setFont(main_font)

        if self.bg_pixmap and not self.bg_pixmap.isNull():
            self.bg_label = QLabel(self)
            self.bg_label.setGeometry(0, 0, self.bg_width, self.bg_height)
            self.bg_label.setPixmap(self.bg_pixmap.scaled(
                self.bg_width, self.bg_height,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            ))
            self.bg_label.lower()

        palette = QPalette()
        palette.setColor(QPalette.WindowText, QColor(102, 0, 204))
        palette.setColor(QPalette.Button, QColor(153, 51, 255))
        palette.setColor(QPalette.ButtonText, Qt.white)
        self.setPalette(palette)

        # 文字提示优化
        label = QLabel('请输入下载的壁纸日期0~7（0表示今日，批量用英文逗号隔开）：', self)
        label.setFont(tip_font)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(
            "background-color: rgba(255, 255, 255, 120); padding: 5px; border-radius: 5px;")

        self.index_input = QLineEdit(self)
        self.index_input.setPlaceholderText('例如：0 或 0,3')
        self.index_input.setStyleSheet("""
            QLineEdit {
                padding: 8px; 
                border: 2px solid #9933ff; 
                border-radius: 5px;
                background-color: rgba(255, 255, 255, 180);
                color: #6600cc;
            }
        """)

        download_btn = QPushButton('开始下载', self)
        download_btn.setStyleSheet("""
            QPushButton {
                padding: 10px; 
                border-radius: 8px;
                background-color: #9933ff;
                color: white;
            }
            QPushButton:hover {
                background-color: #aa55ff;
            }
            QPushButton:pressed {
                background-color: #8822ee;
            }
        """)
        download_btn.clicked.connect(self.start_download)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #9933ff;
                border-radius: 8px;
                text-align: center;
                color: #6600cc;
                background-color: rgba(255, 255, 255, 180);
            }
            QProgressBar::chunk {
                background-color: #9933ff;
                border-radius: 6px;
            }
        """)

        self.result_label = QLabel('', self)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet(
            "background-color: rgba(255, 255, 255, 120); padding: 5px; border-radius: 5px;")

        # 布局调整
        v_layout = QVBoxLayout()
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.index_input)
        h_layout.addWidget(download_btn)

        v_layout.addStretch()
        v_layout.addWidget(label)
        v_layout.addSpacing(5)
        v_layout.addLayout(h_layout)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.progress_bar)
        v_layout.addSpacing(10)
        v_layout.addWidget(self.result_label)
        v_layout.addStretch()

        main_container = QWidget(self)
        main_container.setLayout(v_layout)
        main_container.setFixedWidth(int(self.width() * 0.9))
        main_container.move(int(self.width() * 0.05), int(self.height() * 0.1))
        main_container.setStyleSheet("background-color: transparent;")

    def start_download(self):
        index_str = self.index_input.text().strip() or '0'
        self.progress_bar.setValue(0)
        self.result_label.setText('')
        self.download_thread = DownloadThread(index_str)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.result_signal.connect(self.show_result)
        self.download_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def show_result(self, result):
        self.result_label.setText(result)
        QMessageBox.information(self, '执行结果', result)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("楷体", 12))

    # ========== 可选：设置应用全局图标（任务栏也显示） ==========
    program_dir = get_program_directory()
    icon_path = os.path.join(program_dir, "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = BingWallpaperDownloader()
    window.show()
    sys.exit(app.exec_())
