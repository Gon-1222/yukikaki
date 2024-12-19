import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import numpy as np
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/snowindex', methods=['GET'])
def get_list():
        # 対象のHTMLページURLとalt属性
    page_url = "https://www.city.sapporo.jp/kensetsu/yuki/yukikaki.html"  # HTMLページURLを指定
    alt_text = "明日朝の雪かき指数"  # 対象のalt属性
    
    try:
        # 画像を取得
        img = get_image_from_alt(page_url, alt_text)
        #img= get_image_from_file("02.gif")
        # トリミング
        cropped_img = crop_image(img, 234, 108, 297, 171)
        #cropped_img=img
        display_image(cropped_img)
        # 平均色の取得
        avg_color = get_average_color(cropped_img)
        print(f"平均色: {avg_color}")
        
        # 平均色の分類
        color_data = [(144, 169, 131), (148, 158, 115), (200, 170, 72), (190, 110, 92)]  # 赤、緑、青、グレー
        classified_index = classify_average_color(cropped_img, color_data)
        print(f"分類結果: 色データ{classified_index + 1}に最も近い")
    except Exception as e:
        print(f"エラー: {e}")
    return jsonify([int(classified_index)])

# 画像ファイルを読み込む
def get_image_from_file(file_path):
    """
    ローカルの画像ファイルを読み込む。
    入力:
        file_path (str): 画像ファイルのパス
    出力:
        PIL.Imageオブジェクト
    """
    try:
        image = Image.open(file_path)
        return image
    except Exception as e:
        raise ValueError(f"画像ファイルの読み込みに失敗しました: {e}")

# 画像を表示する
def display_image(image, title=None):
    """
    画像を表示する。
    入力:
        image (PIL.Image): 表示する画像
        title (str): タイトル（省略可能）
    """
    if title:
        print(f"画像タイトル: {title}")
    image.show()

# 1. 画像の取得 (HTMLのimgタグのalt属性に基づく)
def get_image_from_alt(url, alt_text):
    """
    HTMLから指定したalt属性を持つ画像を取得します。
    入力:
        url (str): HTMLページのURL
        alt_text (str): 対象のimgタグのalt属性
    出力:
        PIL.Imageオブジェクト
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"ページの取得に失敗しました (status code: {response.status_code})")
    response.encoding = response.apparent_encoding
    # HTMLを解析
    soup = BeautifulSoup(response.text.encode('utf-8'), 'html.parser')
    img_tag = soup.find('img', alt=alt_text)
    if not img_tag or 'src' not in img_tag.attrs:
        raise ValueError(f"alt属性が'{alt_text}'の画像が見つかりません")
    
    # 画像のURLを取得
    img_url = img_tag['src']
    if not img_url.startswith(('http://', 'https://')):
        # 絶対URLに変換 (相対URL対応)
        from urllib.parse import urljoin
        img_url = urljoin(url, img_url)
    
    # 画像データを取得
    img_response = requests.get(img_url)
    if img_response.status_code != 200:
        raise ValueError(f"画像の取得に失敗しました (status code: {img_response.status_code})")
    
    return Image.open(BytesIO(img_response.content))

# 2. 画像のトリミング (前述の関数)
def crop_image(image, left=0, top=0, right=None, bottom=None):
    right = right or image.width
    bottom = bottom or image.height
    cropped_image = image.crop((left, top, right, bottom))
    return cropped_image

# 3. 平均色の取得 (前述の関数)
def get_average_color(image):
    image = image.convert("RGB")
    np_image = np.array(image)
    avg_color = np.mean(np_image, axis=(0, 1)).astype(int)
    return tuple(avg_color)

# 4. 平均色の分類 (前述の関数)
def classify_average_color(image, color_data):
    avg_color = get_average_color(image)
    distances = [np.linalg.norm(np.array(avg_color) - np.array(color)) for color in color_data]
    print(distances)
    index = np.argmin(distances)
    if distances[index]>=50:
        return None
    return index


if __name__ == "__main__":
    app.run(host="0.0.0.0")