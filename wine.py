# cd ワイン
# git add wine.py
# git commit -m "Update Python script"
# git push origin main


import streamlit as st
import pandas as pd
from PIL import Image, ExifTags
import numpy as np
import json
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload
import tempfile

# Streamlit のキャッシュクリア
st.cache_data.clear()

# ページのレイアウトをワイドモードに変更
st.set_page_config(layout="wide")


        
# 認証設定
def authenticate():
    try:
        credentials_info = json.loads(st.secrets["google_drive"]["service_account_info"])
        
        # サービスアカウントの認証情報から資格情報を作成
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/drive']
        )

        # Google Drive API クライアントを構築
        drive_service = build('drive', 'v3', credentials=credentials)
        return drive_service
    
    except json.JSONDecodeError as e:
        st.error(f"JSON の解析に失敗しました: {e}")
        return None
    


# 認証処理
# gauth = authenticate()
drive = authenticate()

if drive:
    st.success("Google Drive 認証成功！")
else:
    st.error("Google Drive 認証に失敗しました。")
    

WINE_DATA_FILE = "wines.csv"
OPENED_WINE_FILE = "opened_wines.csv"
DRIVE_FOLDER_ID = "1Ve1xvaJki-px7N81uuxcwJ5VgAWNb1bj"  # Google DriveのフォルダIDを指定



login_mode = None
#ログイン機能あり=1
#login_mode = 1

if login_mode == 1:
    # ユーザー名とパスワードの設定
    USER = "kay_wine1"
    PASSWORD = "kay_p@ssw0rd*"

    # セッション状態の初期化（最初に実行）
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # ログアウト機能
    def logout():
        st.session_state["authenticated"] = False
        st.rerun()

    # ログイン画面の表示
    if not st.session_state["authenticated"]:
        st.title("ログイン")
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", key="password", help="パスワードを入力してください", type="password")

        if st.button("ログイン"):
            if username == USER and password == PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("ユーザー名またはパスワードが間違っています")
        st.stop()

    # ログイン後のメインコンテンツ
    if st.session_state["authenticated"]:
        st.title("ワインセラー管理")
        #st.write("ログイン成功！このページは認証済みユーザーのみが見られます。")

        if st.button("ログアウト"):
            logout()


# ファイルのアップロード処理（Google Drive APIを使用）
def save_to_drive_pic(file_path, file_name):
    file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(file_path, mimetype='image/jpeg', resumable=True)
    file = drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
    st.write(f'File ID: {file.get("id")}')

"""
def save_to_drive_csv(file_path, file_name):
    file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(file_path, mimetype='text/csv', resumable=True)
    try:
        file = drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
        st.write(f'File ID: {file.get("id")}')
    except Exception as e:
        st.error(f"ファイルのアップロード中にエラーが発生しました: {e}")
"""

def save_to_drive_csv(file_name, dataframe):
    # dataframeの型を確認し、データフレームであればcsv変換
    if isinstance(dataframe, str): # すでにCSVファイルならそのまま返す
         # 何もしない
        csv_data = dataframe
    elif isinstance(dataframe, pd.DataFrame):  # DataFrameならCSVに変換
        # DataFrameをCSV形式に変換
        csv_data = dataframe.to_csv(index=False, encoding='utf-8')
    else:
        st.write(f"渡されたデータはCSVファイルのパスでもDataFrameでもありません。")


    # メモリ上のバイナリストリームとして扱う
    file_stream = io.BytesIO(csv_data.encode('utf-8'))

    # 一時ファイルを作成してCSVデータを書き込む
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
        temp_file.write(file_stream.getvalue())
        temp_file_path = temp_file.name  # 一時ファイルのパス


    # Google Drive内に同じ名前のファイルが存在するか検索
    query = f"name = '{file_name}' and '{DRIVE_FOLDER_ID}' in parents and trashed = false"
    response = drive.files().list(q=query, fields="files(id)").execute()
    files = response.get("files", [])

    if files:
        # 既存のファイルがある場合、上書き（更新）
        file_id = files[0]["id"]
        media = MediaFileUpload(temp_file_path, mimetype='text/csv', resumable=True)
        try:
            drive.files().update(fileId=file_id, media_body=media).execute()
            st.write(f"Google Driveのファイルを上書き保存しました。File ID: {file_id}")
        except Exception as e:
            st.error(f"Google Driveへの上書き保存中にエラーが発生しました: {e}")
    else:
        # 新規ファイル作成
        file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
        media = MediaFileUpload(temp_file_path, mimetype='text/csv', resumable=True)
        try:
            file = drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
            st.write(f"Google Driveにファイルをアップロードしました。File ID: {file.get('id')}")
        except Exception as e:
            st.error(f"Google Driveへのアップロード中にエラーが発生しました: {e}")



def list_drive_files():
    """Google Drive 内のファイルをリスト表示"""
    if not drive:
        st.error("Google Drive 認証が必要です")
        return

    results = drive.files().list(
        #q="'1Ve1xvaJki-px7N81uuxcwJ5VgAWNb1bj' in parents and trashed = false",
        q=f"'{DRIVE_FOLDER_ID}' in parents and trashed = false",
                                         pageSize=1000,
                                         fields="files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        st.write("ファイルが見つかりませんでした。")
    else:
        st.write("Google Drive のファイル:")
        for file in files:
            st.write(f"{file['name']} (ID: {file['id']})")
    return files

    
# Google Driveからファイルを読み込む
def load_from_drive(file_name):
    """指定した Google Drive のファイルを取得"""
    file_list = list_drive_files()

    # ファイルリストの中から file_name に一致するファイルを探す
    file_id = None
    for file in file_list:
        if file["name"] == file_name:
            file_id = file["id"]
            break  # 該当ファイルが見つかったらループを抜ける
    
    # file_id が見つかった場合のみファイルをダウンロード
    if file_id:
        try:
            # ファイルをダウンロード
            request = drive.files().get_media(fileId=file_id)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_stream.seek(0)  # ポインタを先頭に戻す
            return file_stream
    
        except Exception as e:
            st.error(f"{file_name} が見つかりませんでした。")
            # return None


def load_data():
    """Google Drive からデータを読み込む"""
    wines_csv = load_from_drive(WINE_DATA_FILE)
    opened_wines_csv = load_from_drive(OPENED_WINE_FILE)
    
    # `wines.csv` の読み込み
    if wines_csv:
        try:
            wines_csv.seek(0)  # ポインタを先頭に戻す
            wines = pd.read_csv(wines_csv)
        except Exception as e:
            st.error(f"wines.csv の読み込みに失敗しました: {e}")
            wines = pd.DataFrame(columns=[
                'ワイン名', '年', '種類', '場所', '詳細情報', '写真',
                '購入日', '価格', '購入場所', '国', '地域', '評価', '抜栓日'
            ])
    else:
        wines = pd.DataFrame(columns=[
            'ワイン名', '年', '種類', '場所', '詳細情報', '写真',
            '購入日', '価格', '購入場所', '国', '地域', '評価', '抜栓日'
        ])

        # csvファイルがない場合は空のcsvファイルを保存する
        save_to_drive_csv(WINE_DATA_FILE, wines)

    # `opened_wines.csv` の読み込み
    if opened_wines_csv:
        try:
            opened_wines_csv.seek(0)  # ポインタを先頭に戻す
            opened_wines = pd.read_csv(opened_wines_csv)
        except Exception as e:
            st.error(f"opened_wines.csv の読み込みに失敗しました: {e}")
            opened_wines = pd.DataFrame(columns=wines.columns)
    else:
        opened_wines = pd.DataFrame(columns=wines.columns)

        # csvファイルがない場合は空のcsvファイルを保存する
        save_to_drive_csv(OPENED_WINE_FILE, opened_wines)

    return wines, opened_wines


def save_data():
    """Google Drive にデータを保存"""
    wines_csv = st.session_state.wines.to_csv(index=False)
    opened_wines_csv = st.session_state.opened_wines.to_csv(index=False)
    save_to_drive_csv(WINE_DATA_FILE, wines_csv)
    save_to_drive_csv(OPENED_WINE_FILE, opened_wines_csv)


def update_wine_locations():
    st.session_state.wine_locations = {row: None for row in st.session_state.wines['場所'].unique()}
    for _, wine in st.session_state.wines.iterrows():
        st.session_state.wine_locations[wine['場所']] = wine['ワイン名']

st.subheader('確認用')
st.subheader('ここまでは実行_1')



# 初期化コードを追加
if "rows" not in st.session_state:
    st.session_state.rows = 9
    st.session_state.bottles_per_row = 6
    wines, opened_wines = load_data()
    st.session_state.wines = wines
    st.session_state.opened_wines = opened_wines
    update_wine_locations()

if "selected_location" not in st.session_state:
    st.session_state.selected_location = None

if "wine_locations" not in st.session_state:
    st.session_state.wine_locations = {}


st.write("wines:")    # 確認用
st.write(st.session_state.wines)    # 確認用
st.write("opened_wines:")    # 確認用
st.write(st.session_state.opened_wines)    # 確認用

st.subheader('ここまでは実行2')

def display_wine_cellar():
    st.markdown("""
        <style>
            .wine-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
                gap: 10px;
            }
            .wine-container {
                text-align: center;
                border: 1px solid #ccc;
                padding: 10px;
                border-radius: 5px;
            }

            /* スマホ向けの調整 */
            @media (max-width: 768px) {
                .wine-grid {
                    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); /* スマホでは幅を縮小 */
                }
            }
        </style>

    """, unsafe_allow_html=True)
        
    st.subheader('ワインセラー_2/18')
    st.markdown('<div class="wine-grid">', unsafe_allow_html=True)

    for row in range(st.session_state.rows):
        cols = st.columns(st.session_state.bottles_per_row)
        for bottle in range(st.session_state.bottles_per_row):
            loc = f"段{row+1} 本{bottle+1}"
            wine_name = st.session_state.wine_locations.get(loc, "空") or "空"
            
            wine_info = st.session_state.wines[st.session_state.wines['場所'] == loc]
            img_path = None
            if not wine_info.empty:
                wine_name = wine_info.iloc[0]['ワイン名']
                photos = wine_info.iloc[0]['写真']
                if isinstance(photos, str) and photos:
                    img_path = photos.split(';')[0]
            
            with cols[bottle]:
                with st.container(border=True):
                    if st.button(str(wine_name), key=loc):
                        st.session_state.selected_location = loc
                    if img_path:
                        st.image(img_path, width=80, use_container_width=True)
                    else:
                        st.markdown('<div style="height:135px;"></div>', unsafe_allow_html=True)

display_wine_cellar()

st.subheader('ワイン登録')
if st.session_state.selected_location:
    st.write(f"選択中の場所: {st.session_state.selected_location}")
    existing_wine = st.session_state.wines[st.session_state.wines['場所'] == st.session_state.selected_location]
    
    wine_name = st.text_input("ワイン名", existing_wine['ワイン名'].values[0] if not existing_wine.empty else "")
    years = list(range(pd.Timestamp.now().year, 1969, -1))
    wine_year = st.selectbox("年", years, index=years.index(existing_wine['年'].values[0]) if not existing_wine.empty else 0)
    wine_types = ["赤", "白", "スパークリング", "デザート", "ロゼ", "オレンジ", "その他"]
    wine_type = st.selectbox("種類", wine_types, index=wine_types.index(existing_wine['種類'].values[0]) if not existing_wine.empty else 0)
    wine_details = st.text_area("詳細情報", existing_wine['詳細情報'].values[0] if not existing_wine.empty else "")
    
    purchase_date = pd.to_datetime(existing_wine['購入日'].values[0]) if not existing_wine.empty and pd.notna(existing_wine['購入日'].values[0]) else None
    purchase_date = st.date_input("購入日", purchase_date)
    
    price = st.number_input("価格", min_value=0.0, format="%.2f", value=float(existing_wine['価格'].values[0]) if not existing_wine.empty else 0.0)
    purchase_place = st.text_input("購入場所", existing_wine['購入場所'].values[0] if not existing_wine.empty else "")
    wine_country = st.text_input("ワインの国", existing_wine['国'].values[0] if not existing_wine.empty else "")
    wine_region = st.text_input("ワインの地域", existing_wine['地域'].values[0] if not existing_wine.empty else "")
    #wine_rating = st.slider("評価 (1〜5)", 1, 5, int(existing_wine['評価'].values[0]) if not existing_wine.empty else 3)
    wine_rating_options = [None, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
    wine_rating = st.selectbox("評価 (1〜5)", wine_rating_options, index=0, format_func=lambda x: "選択なし" if x is None else str(x))


    # 抜栓日を取得し、NaTまたはNoneを適切に処理
    opening_date = None
    if not existing_wine.empty and '抜栓日' in existing_wine.columns:
        raw_date = existing_wine['抜栓日'].values[0]
        if pd.notna(raw_date):  # NaTではないことを確認
            if isinstance(raw_date, str):  # 文字列なら日付型に変換
                try:
                    #opening_date = pd.to_datetime(raw_date).date()
                    opening_date = pd.to_datetime(raw_date, errors='coerce').date()

                except Exception:
                    opening_date = None  # 変換失敗時はNoneにする
            elif isinstance(raw_date, pd.Timestamp):  # Timestampならdateに変換
                opening_date = raw_date.date()

    # NaT を None に変換
    if isinstance(opening_date, pd.Timestamp) and pd.isna(opening_date):
        opening_date = None
    elif isinstance(opening_date, pd.Timestamp):
        opening_date = opening_date.date()
    
    # NaT を None に変換
    opening_date = None if pd.isna(opening_date) else opening_date


    # Streamlitのdate_inputで表示
    opening_date = st.date_input("抜栓日", opening_date)


    """
    # 画像の保存処理の前に、photo_pathsを初期化
    photo_paths = existing_wine['写真'].values[0] if not existing_wine.empty else ""

    
    existing_photos = existing_wine['写真'].values[0] if not existing_wine.empty else ""
    existing_photo_list = existing_photos.split(';') if existing_photos else []
    """

    # existing_wineが空でないことを確認し、'写真'列の値を取得
    photo_paths = existing_wine['写真'].values[0] if not existing_wine.empty and isinstance(existing_wine['写真'].values[0], str) else ""

    # 既存の写真を取得して、空文字列またはNaNの場合は空リストにする
    existing_photos = existing_wine['写真'].values[0] if not existing_wine.empty else ""

    # NaNやNoneが含まれている場合に備えて空文字列に変換
    existing_photos = "" if isinstance(existing_photos, float) and np.isnan(existing_photos) else existing_photos

    # 文字列が存在すれば ';' で分割、なければ空リスト
    existing_photo_list = existing_photos.split(';') if existing_photos else []


    if existing_photo_list:
        st.write("既存の写真:")
        updated_photo_list = existing_photo_list[:]  # 元のリストをコピー
        cols = st.columns(len(existing_photo_list))
        for i, photo in enumerate(existing_photo_list):
            with cols[i]:  # 横並びに配置
                st.image(photo, width=160)
                if st.button(f"削除", key=f"delete_{photo}"):
                    existing_photo_list.remove(photo)

        # 更新後のリストを反映
        existing_photo_list = updated_photo_list

    # 画像アップロード
    wine_images = st.file_uploader("ワインの写真を最大3枚アップロード", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
        
    if wine_images:  
        new_photos = []
        if wine_images:
            for i, wine_image in enumerate(wine_images[:3]):
                image_path = f"images/{wine_image.name}"

                try:
                    image = Image.open(wine_image).convert("RGB")  # RGB変換して保存互換性を確保
                    image.load()  # 画像を完全に読み込む
                    image.verify()  # 破損していないかチェック
                    image = Image.open(wine_image).convert("RGB")  # verifyの後は再オープンが必要
                    
                    
                    try:
                        exif = image._getexif()
                        if exif:
                            for tag, value in exif.items():
                                tag_name = ExifTags.TAGS.get(tag, tag)
                                if tag_name == 'Orientation':
                                    if value == 3:
                                        image = image.rotate(180, expand=True)
                                    elif value == 6:
                                        image = image.rotate(270, expand=True)
                                    elif value == 8:
                                        image = image.rotate(90, expand=True)
                                    break
                    except (AttributeError, KeyError, IndexError):
                        pass                 

                    # 画像をローカル保存
                    image.save(image_path, format="JPEG", quality=85, optimize=True)

                    # Google Driveにアップロード
                    save_to_drive_pic(image_path, wine_image.name)

                    new_photos.append(image_path)
                except OSError as e:
                    st.error(f"画像の保存中にエラーが発生しました: {e}")
        
        photo_paths = ';'.join(existing_photo_list + new_photos) if new_photos else existing_wine["写真"].values[0] if not existing_wine.empty else ""



    if st.button('ワインを登録'):
        if not existing_wine.empty:
            existing_data = existing_wine.iloc[0].fillna('').to_dict()
        else:
            existing_data = {}

        wine_info = pd.DataFrame([{
    **existing_data,
    'ワイン名': wine_name,
    '年': wine_year,
    '種類': wine_type,
    '場所': st.session_state.selected_location,
    '詳細情報': wine_details,
    '写真': photo_paths,
    '購入日': str(purchase_date) if purchase_date else '',
    '価格': price,
    '購入場所': purchase_place,
    '国': wine_country,
    '地域': wine_region,
    '評価': wine_rating,
    '抜栓日': str(opening_date) if opening_date else ''
}])        
        
        if pd.notna(opening_date):
            st.session_state.opened_wines = pd.concat([st.session_state.opened_wines, wine_info], ignore_index=True)
            st.session_state.wines = st.session_state.wines[st.session_state.wines['場所'] != st.session_state.selected_location]
        else:
            st.session_state.wines = pd.concat([st.session_state.wines, wine_info], ignore_index=True)
        
        save_data()
        st.rerun()



st.subheader("抜栓済みワインリスト")
if not st.session_state.opened_wines.empty:
    df_display = st.session_state.opened_wines.copy()

    # 画像をHTMLで表示する関数
    def image_formatter(photo_str):
        if isinstance(photo_str, str) and photo_str:
            photos = photo_str.split(';')
            img_tags = ""
            for photo in photos:
                file_list = drive.list_drive_files()
                if file_list:
                    file_id = file_list[0]['id']
                    img_url = f"https://drive.google.com/uc?id={file_id}"
                    img_tags += f'<img src="{img_url}" width="160">'
            return img_tags
        return ""




    # 画像の表示用にフォーマット
    df_display["写真"] = df_display["写真"].apply(image_formatter)

    # HTMLを利用してデータフレームを表示
    st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.write("抜栓済みワインはありません。")



# メモ
# 追加機能候補

# 抜栓済みの写真表示修正
# 抜栓済みの各記録をグラフ化など

