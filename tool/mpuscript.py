"""
图床
"""
import hashlib
import io
import random
import re
import os
import uuid
import requests
from loguru import logger
from werkzeug.utils import secure_filename
from PIL import Image, ImageChops
import boto3
from werkzeug.utils import secure_filename

from setting import R2_ENDPOINT_URL, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET_NAME

# R2_ENDPOINT_URL = "https://819cc5c82aeb77dcbe9002c23c026748.r2.cloudflarestorage.com"
# R2_BUCKET_NAME = 'ai-toolify'
# R2_ACCESS_KEY = 'ba6a870f1cebf9218e64fd8b1714695c'
# R2_SECRET_KEY = '9e9fc05b98938e744720bca777c1dd8bdbebf34ca4ed55a18c08ac1c7e6206d2'

# 初始化 S3 客户端 - 只有在配置了R2时才初始化
s3_client = None
if R2_ENDPOINT_URL and R2_ACCESS_KEY and R2_SECRET_KEY:
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            region_name='auto'
        )
    except Exception as e:
        logger.warning(f"Failed to initialize S3 client: {e}")
        s3_client = None
"""
根据图片的内容重新命名
所有图片类型都webp类型
压缩后的webp类型的
"""


def compress_image(image_stream, quality=75, resize_factor=0.8):
    with Image.open(image_stream) as img:
        # 调整图像尺寸
        new_dimensions = (int(img.width * resize_factor), int(img.height * resize_factor))
        img = img.resize(new_dimensions, Image.Resampling.LANCZOS)

        # 转换为 RGB（如果需要），并去除元数据
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 使用优化和渐进式压缩
        output_stream = io.BytesIO()
        img.save(output_stream, format="WEBP", quality=quality, optimize=True, progressive=True)
        output_stream.seek(0)
        return output_stream


def compress_images(image_stream, quality=75, max_width=800, max_height=800):
    with Image.open(image_stream) as img:
        # 获取原始图像尺寸
        original_width, original_height = img.size

        # 计算缩放比例
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        scale_ratio = min(width_ratio, height_ratio)

        # 确定新的图像尺寸
        if scale_ratio < 1:
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
        else:
            new_width = original_width
            new_height = original_height

        # 调整图像尺寸
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 转换为 RGB（如果需要），并去除元数据
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 使用优化和渐进式压缩
        output_stream = io.BytesIO()
        img.save(output_stream, format="WEBP", quality=quality, optimize=True, progressive=True)
        output_stream.seek(0)
        return output_stream


# 获取首页中的图标信息
def get_icon_binary(url):
    resp = requests.get(url)
    if resp.status_code == 200:
        text = resp.text
        try:
            icon_url = re.findall(r'<link rel.*?icon.*?href="(.*?)"', text, re.S)[0]
            if "http" not in icon_url:
                if url[-1] == "/":
                    icon_url = url + icon_url
                else:
                    icon_url = url + "/" + icon_url
        except Exception as e:
            logger.error(e)
            icon_url = None
    else:
        icon_url = None
    return icon_url


# 上传接口到图床
def upload_file(file):
    """
    上传的文件对象
    :param file:
    :return:
    """
    # img = Image.open(file.stream)
    # img_data = img.tobytes()
    # img_hash = hashlib.md5(img_data).hexdigest()
    random_number = random.randint(1000, 9999)
    filename,_ = os.path.splitext(file.filename)
    safe_filename = secure_filename(filename)
    filename = f"{safe_filename}{random_number}.webp"  # 根据需要修改扩展名
    # 压缩图像
    compressed_image = compress_image(file, quality=75, resize_factor=0.8)
    # 上传压缩后的图像到 Cloudflare R2
    try:
        s3_client.upload_fileobj(compressed_image, "image", filename)
        file_url = f'https://{R2_BUCKET_NAME}/image/{filename}'
        return file_url
    except Exception as e:
        logger.error(e)
        return None


def upload_files(image_bytes):
    # 检查S3客户端是否可用
    if s3_client is None:
        logger.warning("S3 client not configured, skipping upload")
        return None
        
    # 创建 BytesIO 对象
    image_stream = io.BytesIO(image_bytes)
    compressed_image = compress_image(image_stream, quality=75, resize_factor=0.8)
    # 生成文件名
    filename = secure_filename(f"image_{uuid.uuid4().hex}.webp")

    try:
        # 上传到 Cloudflare R2
        s3_client.upload_fileobj(compressed_image, R2_BUCKET_NAME, filename)
        # 获取新 URL
        file_url = f'https://{R2_BUCKET_NAME}/image/{filename}'
    except Exception as e:
        logger.error(e)
        file_url = None
    return file_url


def generate_image_name(image_path):
    # 打开图片
    with Image.open(image_path) as img:
        # 读取图片内容并生成哈希
        img_data = img.tobytes()
        img_hash = hashlib.md5(img_data).hexdigest()

    return f"{img_hash}.jpg"  # 或根据需要修改扩展名


# 本地上传图床
def local_upload_files(file_path):
    # 检查S3客户端是否可用
    if s3_client is None:
        logger.warning("S3 client not configured, skipping upload")
        return None
        
    with Image.open(file_path) as img:
        # 读取图片内容并生成哈希
        img_data = img.tobytes()
        img_hash = hashlib.md5(img_data).hexdigest()
    file_name = f"{img_hash}.webp"
    with open(file_path, 'rb') as image_file:
        binary_data = image_file.read()
    # os.remove(filename)
    original_image_stream = io.BytesIO(binary_data)
    compressed_image = compress_image(original_image_stream, quality=75, resize_factor=0.8)
    try:
        logger.info("上传图床")
        # 上传到 Cloudflare R2
        s3_client.upload_fileobj(compressed_image, R2_BUCKET_NAME, file_name)
        # 获取新 URL
        file_url = f'https://{R2_BUCKET_NAME}/image/{file_name}'
    except Exception as e:
        logger.error(e)
        file_url = None
    return file_url

# image_binary = get_icon_binary('https://moshiai.org/')
# print(image_binary)

# file_url = get_image_binary("https://product.supertone.ai/")
# print(file_url)
