import requests
import os
import json
from urllib.parse import urlparse
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS


def modify_image_metadata(input_path, output_path, title, copyright):
    """
    修改图片的标题和版权信息
    
    参数:
        input_path: 输入图片路径
        output_path: 输出图片路径
        title: 新的标题
        copyright: 新的版权信息
    """
    try:
        # 打开图片
        with Image.open(input_path) as img:
            # 尝试获取现有EXIF数据
            exif_data = img.getexif()

            # 创建或更新EXIF数据
            if exif_data is None:
                exif_data = {}

            # 查找标题和版权对应的标签ID
            title_tag_id = None
            copyright_tag_id = None

            for tag_id, tag_name in TAGS.items():
                if tag_name == "ImageDescription":  # 对应图片标题
                    title_tag_id = tag_id
                elif tag_name == "Copyright":  # 对应版权信息
                    copyright_tag_id = tag_id

            # 设置新的标题和版权信息
            if title_tag_id:
                exif_data[title_tag_id] = title
            if copyright_tag_id:
                exif_data[copyright_tag_id] = copyright

            # 保存修改后的图片
            img.save(output_path, exif=exif_data)

    except Exception as e:
        # 保留异常捕获但不输出信息
        pass


def get_file_extension(content_type):
    """根据Content-Type获取文件扩展名"""
    if not content_type:
        return '.jpg'  # 默认扩展名
    
    content_type = content_type.lower()
    if 'image/jpeg' in content_type:
        return '.jpg'
    elif 'image/png' in content_type:
        return '.png'
    elif 'image/gif' in content_type:
        return '.gif'
    elif 'image/webp' in content_type:
        return '.webp'
    elif 'image/svg+xml' in content_type:
        return '.svg'
    elif 'image/bmp' in content_type:
        return '.bmp'
    else:
        return '.jpg'  # 默认扩展名

def get_program_directory():
    """获取程序所在文件夹的绝对路径"""
    return Path(__file__).resolve().parent

def crawl_webpage(url):
    """爬取网页内容并返回JSON数据"""
    try:
        print(f"正在爬取网页: {url}")
        # 添加请求头模拟浏览器，避免被反爬
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        
        # 尝试解析JSON数据
        json_data = response.json()
        print("成功获取并解析JSON数据")
        return json_data
        
    except json.JSONDecodeError:
        print("网页内容不是有效的JSON格式")
        return None
    except Exception as e:
        print(f"爬取网页失败: {str(e)}")
        return None


def download_image_from_url(image_url, image_name, date):
    """从指定URL下载图片，保存到程序所在文件夹，以当天日期为文件名"""
    try:
        # 获取程序所在目录
        program_dir = get_program_directory()
        print(f"程序所在目录: {program_dir}")
        
        # 发送请求下载图片
        print(f"正在下载图片: {image_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        
        # 获取文件扩展名
        content_type = response.headers.get('Content-Type')
        extension = get_file_extension(content_type)
        
        # 生成以当天日期为基础的文件名 (格式: YYYYMMDD)
        today = date
        filename = f"{today}{extension}"

        # 检查文件是否已存在，如果存在则添加序号
        file_path = os.path.join(program_dir, filename)
        counter = 1
        while os.path.exists(file_path):
            filename = f"{today}_{counter}{extension}"
            file_path = os.path.join(program_dir, filename)
            counter += 1
        
        # 输入图片路径
        input_image = file_path  # 替换为你的图片路径

        # 设置要修改的标题和版权信息
        new_title = image_name.split(' (')[0]
        new_copyright = image_name.split('© ')[1][:-1]

        # 保存图片
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        print(f"图片已保存至: {file_path}")

        # 调用函数进行修改（移到return之前，并修正变量名）
        modify_image_metadata(input_image, input_image, new_title, new_copyright)

        return file_path
        
    except Exception as e:
        print(f"下载图片失败: {str(e)}")
        return None

def main(Index=0):
    # 要爬取的网页URL（请替换为实际的目标URL）
    # 替换为返回JSON数据的网页URL
    #"""
    target_url = f"https://bing.biturl.top/?resolution=UHD&format=json&mkt=en-US&index={Index}"

    # 1. 爬取网页获取JSON数据
    json_data = crawl_webpage(target_url)
    
    if not json_data:
        print("无法继续执行，退出程序")
        return
    #"""

    """
    json_data = {
        "start_date": "20190605",
        "end_date": "20190606",
        "url": "https://www.bing.com/th?id=OHR.MulberryArtificialHarbour_ZH-CN3973249802_1920x1080.jpg",
        "copyright": "The Mulberry Port Site after the Normandy Invasion, Arromances les Bains, Normandy, France (© Javier Gil/Alamy)",
        "copyright_link": "http://www.bing.com/search?q=%E6%A1%91%E6%A0%91%E6%B8%AF%E9%81%97%E5%9D%80&form=hpcapt&mkt=zh-cn"
    }
    """

    # 2. 从JSON数据中提取图片URL
    image_url = json_data.get('url')
    image_name = json_data.get('copyright')
    date = json_data.get('end_date')#US&CN服务区存在时差

    if image_url:
        # 3. 下载图片
        download_image_from_url(image_url, image_name, date)
        print("图片下载流程完成")
    else:
        print("JSON数据中未找到'url'字段")
    
if __name__ == "__main__":
    Index = input("请输入下载的壁纸日期0~7，0表示今日（批量下载请用英文逗号隔开）:")
    if Index:
        try:
            if ',' in Index:
                start = min(7, max(0, int(Index.split(',')[0])))
                end = min(7, max(0, int(Index.split(',')[1])))
                for i in range(start, (end + 1)):
                    main(i)
            else:main(int(Index))
        except Exception:pass
    elif Index == 'c':pass
    else:main()
    
