import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 網頁基本設定
st.set_page_config(page_title="Google Sheet 智能圖表產生器", layout="wide")
st.title("🚀 Google Sheet 智能圖表產生器")
st.write("請直接在下方貼上網址，系統將為您自動辨識並生成圖表。")

# 1. 網址輸入框
sheet_url = st.text_input(
    "請在下方貼上您的 Google Sheet 網址：",
    placeholder="https://google.com"
)

# 只有當使用者貼上網址後，才跳出後續設定
if sheet_url:
    sheet_name = st.text_input(
        "💬 想要分析特定工作表（分頁）嗎？請輸入名稱（留空則預設讀取第一頁）：",
        value="",
        placeholder="例如：Sheet2、測試數據（若讀取第一頁則不用填寫）",
        help="如需讀取特定頁籤，請務必與您的 Google Sheet 左下角名稱完全一模一樣。"
    )
    
    try:
        # 讀取雲端資料
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 判斷使用者有沒有輸入分頁名稱
        if sheet_name.strip() != "":
            df = conn.read(spreadsheet=sheet_url, worksheet=sheet_name.strip())
        else:
            df = conn.read(spreadsheet=sheet_url)
        
        # 資料基本清理
        df = df.dropna(how='all')
        df.columns = df.columns.astype(str).str.strip()
        all_cols = df.columns.tolist()
        
        st.success("✅ 成功精準讀取雲端資料！")
        
        # 🌟 修正重點：完整列出全部資料，並在資料量大時自動開啟捲軸
        with st.expander("📋 點擊展開/收合【完整數據檢視】", expanded=True):
            # 設定 height=230 大約就是 5 列資料的高度。大於 5 列時，右側與下方會自動跑出漂亮的捲軸！
            # use_container_width=True 讓表格填滿網頁寬度
            st.dataframe(df, height=230, use_container_width=True)
            # 額外小提示：顯示總共有幾列、幾欄
            st.caption(f"📊 目前表格總計：{df.shape[0]} 列 (Rows) ｜ {df.shape[1]} 欄 (Columns)")
        
        # 2. 欄位設定區
        st.divider()
        st.subheader("🛠️ 請選擇基準軸 (X軸)")
        
        col_setting1, col_setting2 = st.columns(2)
        with col_setting1:
            x_options = ["-- 請選擇基準軸 (X軸) --"] + all_cols
            selected_x = st.selectbox("📌 選擇基準軸 (X軸)：", options=x_options, index=0)
            
        with col_setting2:
            selected_y_cols = st.multiselect(
                "🎯 進階：手動選擇要加入對比的 Y 軸數據欄位（非必填）：",
                options=all_cols,
                default=[],
                help="這會用於第二個分頁標籤以後的綜合數據對比。若不需要對比，直接留空即可。"
            )
        
        # 3. 當選好基準軸後，立刻開始畫圖
        if selected_x == "-- 請選擇基準軸 (X軸) --":
            st.info("💡 提示：請在上方選好 **X軸**，系統就會立刻為您生成專屬內容分析圖表。")
        else:
            st.divider()
            st.header(f"📊 視覺化圖表結果 (基準軸: {selected_x})")
            
            # 建立分頁標籤
            tab1, tab2, tab3 = st.tabs([f"🎯 【{selected_x}】純內容分析 (免Y軸)", "📈 趨勢折線圖 (結合Y軸)", "📊 數值比較圖 (結合Y軸)"])
            
            with tab1:
                st.subheader(f"➡️ 針對欄位【{selected_x}】內容進行自動統計")
                
                counts_df = df[selected_x].value_counts().reset_index()
                counts_df.columns = [selected_x, '出現次數']
                
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    fig_x_pie = px.pie(counts_df, names=selected_x, values='出現次數', title=f"欄位【{selected_x}】各內容佔比分佈")
                    st.plotly_chart(fig_x_pie, use_container_width=True)
                with sub_col2:
                    fig_x_bar = px.bar(counts_df, x=selected_x, y='出現次數', color=selected_x, text='出現次數', title=f"欄位【{selected_x}】各內容數量統計")
                    st.plotly_chart(fig_x_bar, use_container_width=True)
            
            with tab2:
                if not selected_y_cols:
                    st.info("💡 提示：如需查看數據趨勢圖，請在上方選取您想要對比的 **Y 軸欄位**。")
                else:
                    st.subheader("➡️ 趨勢變化對比")
                    fig_line = px.line(df, x=selected_x, y=selected_y_cols, markers=True, title="數據趨勢圖")
                    st.plotly_chart(fig_line, use_container_width=True)
                    
            with tab3:
                if not selected_y_cols:
                    st.info("💡 提示：如需查看綜合數值比較，請在上方選取您想要對比的 **Y 軸欄位**。")
                else:
                    st.subheader("➡️ 綜合數值比較")
                    fig_bar = px.bar(df, x=selected_x, y=selected_y_cols, barmode="group", title="數據比較圖")
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
    except Exception as e:
        st.error(f"❌ 無法解析該網址，請確認 Google Sheet 是否已開啟「知道連結的任何人均可檢視」權限，或檢查分頁名稱是否輸入正確。")
        st.info(f"詳細錯誤訊息 (除錯用): {e}")
else:
    st.info("💡 期待您的資料！請在上方輸入框貼上 Google Sheet 網址以開始分析。")
