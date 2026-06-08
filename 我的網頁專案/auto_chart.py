import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from google import genai  # 導入 Gemini 官方套件
import os
import toml

# 網頁基本設定
st.set_page_config(page_title="Google Sheet 智能圖表與 AI 產生器", layout="wide")
st.title("🚀 Google Sheet 智能圖表與 AI 產生器")
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
        
        # 完整數據檢視 (附帶捲軸)
        with st.expander("📋 點擊展開/收合【完整數據檢視】", expanded=True):
            st.dataframe(df, height=230, use_container_width=True)
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

            # 4. 🤖 Gemini 數據 AI 助理對話區
            st.divider()
            st.header("🤖 Gemini 數據 AI 助理")
            st.write(f"系統已將上方【{selected_x}】的圖表與數據同步給 AI。您可以直接在下方輸入框提問。")
            
            # 🌟 修正重點：不再把金鑰寫死在程式裡！改回標準安全的 Secrets 自動抓取邏輯，順利通過 GitHub 檢查
            api_key = None
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
            else:
                try:
                    secret_path = os.path.join(".streamlit", "secrets.toml")
                    if os.path.exists(secret_path):
                        with open(secret_path, "r", encoding="utf-8") as f:
                            local_secrets = toml.load(f)
                            api_key = local_secrets.get("GEMINI_API_KEY")
                except:
                    pass

            # 判斷金鑰
            if not api_key:
                st.warning("🔑 提示：請確認您的 Streamlit 雲端 Secrets 後台已填寫 `GEMINI_API_KEY` 才能開啟 AI 對話功能。")
            else:
                # 初始化 Gemini 客戶端
                client = genai.Client(api_key=api_key)
                
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []
                
                # 對話紀錄容器
                chat_container = st.container(height=300)
                with chat_container:
                    for message in st.session_state.chat_history:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])
                
                # 下方聊天文字對話框
                if user_query := st.chat_input("請輸入您想詢問 AI 的數據問題..."):
                    with chat_container:
                        with st.chat_message("user"):
                            st.markdown(user_query)
                    st.session_state.chat_history.append({"role": "user", "content": user_query})
                    
                    # 數據處理
                    chart_summary = counts_df.to_string()
                    data_summary = df.head(100).to_string()
                    
                    system_prompt = (
                        "你是一個專業的測試與數據分析專家。使用者剛剛在網頁上生成了圖表，以下是圖表與數據內容：\n\n"
                        f"【使用者當前選擇的基準軸(X軸)】: {selected_x}\n"
                        f"【圖表統計摘要 (各項目出現次數)】:\n{chart_summary}\n\n"
                        f"【詳細測試數據預覽(前100筆)】:\n{data_summary}\n\n"
                        "請根據以上資訊，精準且專業地回答使用者的問題。\n"
                        f"【使用者問題】: {user_query}"
                    )
                    
                    with chat_container:
                        with st.chat_message("assistant"):
                            message_placeholder = st.empty()
                            with st.spinner("AI 正在閱讀圖表與分析數據..."):
                                try:
                                    response = client.models.generate_content(
                                        model='gemini-2.5-flash',
                                        contents=system_prompt,
                                    )
                                    ai_response = response.text
                                    message_placeholder.markdown(ai_response)
                                    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                                    st.rerun()
                                except Exception as ai_err:
                                    st.error(f"AI 回應失敗: {ai_err}")
                                    
    except Exception as e:
        st.error(f"❌ 無法解析該網址，請確認 Google Sheet 是否已開啟「知道連結的任何人均可檢視」權限，或檢查分頁名稱是否輸入正確。")
        st.info(f"詳細錯誤訊息 (除錯用): {e}")
else:
    st.info("💡 期待您的資料！請在上方輸入框貼上 Google Sheet 網址以開始分析。")
