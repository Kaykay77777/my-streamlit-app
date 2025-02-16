import streamlit as st
import pandas as pd
from PIL import Image
import os

WINE_DATA_FILE = "wines.csv"
OPENED_WINE_FILE = "opened_wines.csv"

os.makedirs("images", exist_ok=True)

def load_data():
    if os.path.exists(WINE_DATA_FILE):
        wines = pd.read_csv(WINE_DATA_FILE)
    else:
        wines = pd.DataFrame(columns=[
            'ワイン名', '年', '種類', '場所', '詳細情報', '写真',
            '購入日', '価格', '購入場所', '国', '地域', '評価', '抜栓日'
        ])
    
    if os.path.exists(OPENED_WINE_FILE):
        opened_wines = pd.read_csv(OPENED_WINE_FILE)
    else:
        opened_wines = pd.DataFrame(columns=wines.columns)
    return wines, opened_wines

def save_data():
    st.session_state.wines.to_csv(WINE_DATA_FILE, index=False)
    st.session_state.opened_wines.to_csv(OPENED_WINE_FILE, index=False)

def update_wine_locations():
    st.session_state.wine_locations = {row: None for row in st.session_state.wines['場所'].unique()}
    for _, wine in st.session_state.wines.iterrows():
        st.session_state.wine_locations[wine['場所']] = wine['ワイン名']

if "rows" not in st.session_state:
    st.session_state.rows = 5
    st.session_state.bottles_per_row = 6
    wines, opened_wines = load_data()
    st.session_state.wines = wines
    st.session_state.opened_wines = opened_wines
    update_wine_locations()

if "selected_location" not in st.session_state:
    st.session_state.selected_location = None

def display_wine_cellar():
    st.subheader('ワインセラーの状態')
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
                        st.markdown('<div style="height:80px;"></div>', unsafe_allow_html=True)

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
    wine_rating = st.slider("評価 (1〜5)", 1, 5, int(existing_wine['評価'].values[0]) if not existing_wine.empty else 3)
    

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

    # Streamlitのdate_inputで表示
    opening_date = st.date_input("抜栓日", opening_date)

    # 画像の保存処理の前に、photo_pathsを初期化
    photo_paths = existing_wine['写真'].values[0] if not existing_wine.empty else ""

    
    existing_photos = existing_wine['写真'].values[0] if not existing_wine.empty else ""
    existing_photo_list = existing_photos.split(';') if existing_photos else []

    if existing_photo_list:
        st.write("既存の写真:")
        st.image(existing_photo_list, width=160)

    # 画像アップロード
    wine_images = st.file_uploader("ワインの写真を最大3枚アップロード", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    
    if wine_images:  
        new_photos = []
        if wine_images:
            for i, wine_image in enumerate(wine_images[:3]):
                image_path = f"images/{wine_name}_{st.session_state.selected_location}_photo_{i+1}.png"

                try:
                    image = Image.open(wine_image).convert("RGB")  # RGB変換して保存互換性を確保
                    image.load()  # 画像を完全に読み込む
                    image.verify()  # 破損していないかチェック
                    image = Image.open(wine_image).convert("RGB")  # verifyの後は再オープンが必要
                    image.save(image_path, format="JPEG", quality=85, optimize=True)

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
            img_tags = "".join([f'<img src="file://{os.path.abspath(photo)}" width="160">' for photo in photos])
            return img_tags
        return ""

    # 画像の表示用にフォーマット
    df_display["写真"] = df_display["写真"].apply(image_formatter)

    # HTMLを利用してデータフレームを表示
    st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.write("抜栓済みワインはありません。")
