import streamlit as st
import pandas as pd
from PIL import Image
import os

WINE_DATA_FILE = "wines.csv"
OPENED_WINE_FILE = "opened_wines.csv"

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
    wine_year = st.selectbox("年", years, index=0 if existing_wine.empty else years.index(existing_wine['年'].values[0]))
    wine_types = ["赤", "白", "スパークリング", "デザート", "ロゼ", "オレンジ", "その他"]
    wine_type = st.selectbox("種類", wine_types, index=0 if existing_wine.empty else wine_types.index(existing_wine['種類'].values[0]))
    wine_details = st.text_area("詳細情報", existing_wine['詳細情報'].values[0] if not existing_wine.empty else "")
    wine_images = st.file_uploader("ワインの写真を最大3枚アップロード", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    purchase_date = st.date_input("購入日", existing_wine['購入日'].values[0] if not existing_wine.empty else None)
    price = st.number_input("価格", min_value=0.0, format="%.2f", value=existing_wine['価格'].values[0] if not existing_wine.empty else 0.0)
    purchase_place = st.text_input("購入場所", existing_wine['購入場所'].values[0] if not existing_wine.empty else "")
    wine_country = st.text_input("ワインの国", existing_wine['国'].values[0] if not existing_wine.empty else "")
    wine_region = st.text_input("ワインの地域", existing_wine['地域'].values[0] if not existing_wine.empty else "")
    wine_rating = st.slider("評価 (1〜5)", 1, 5, existing_wine['評価'].values[0] if not existing_wine.empty else 3)
    opening_date = st.date_input("抜栓日", None)
    
    if st.button('ワインを登録'):
        wine_info = pd.DataFrame([{**existing_wine.iloc[0].to_dict(), '抜栓日': opening_date}])
        if opening_date:
            st.session_state.opened_wines = pd.concat([st.session_state.opened_wines, wine_info], ignore_index=True)
            st.session_state.wines = st.session_state.wines[st.session_state.wines['場所'] != st.session_state.selected_location]
        save_data()
        st.rerun()

st.subheader("抜栓済みワインリスト")
if not st.session_state.opened_wines.empty:
    st.dataframe(st.session_state.opened_wines)
    wine_to_restore = st.selectbox("元に戻すワインを選択", st.session_state.opened_wines['ワイン名'].unique())
    if st.button("元に戻す"):
        wine_row = st.session_state.opened_wines[st.session_state.opened_wines['ワイン名'] == wine_to_restore].iloc[0]
        st.session_state.wines = pd.concat([st.session_state.wines, pd.DataFrame([wine_row])], ignore_index=True)
        st.session_state.opened_wines = st.session_state.opened_wines[st.session_state.opened_wines['ワイン名'] != wine_to_restore]
        save_data()
        st.success(f"{wine_to_restore}を元に戻しました。")
