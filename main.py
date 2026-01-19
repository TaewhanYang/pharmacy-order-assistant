import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="약품 주문 지원 시스템", layout="wide")

st.title("💊 약품 월 주문 자동 계산 시스템")

st.header("1️⃣ 포장단위 셋업파일 업로드 (약품 기본정보)")
setup_file = st.file_uploader("💾 포장단위 셋업 엑셀 업로드 (.xlsx)", type=["xlsx"], key="setup")

if setup_file:
    df_setup = pd.read_excel(setup_file)
    required_cols = {"약품명", "제약사", "단위", "청구코드"}
    if not required_cols.issubset(df_setup.columns):
        st.error(f"❌ 필수 컬럼 누락: {required_cols}")
    else:
        df_setup = df_setup.drop_duplicates(subset=["청구코드", "단위"])
        st.success("✅ 포장단위 셋업 불러오기 성공")
        st.dataframe(df_setup)

st.header("2️⃣ 지난달 약품 사용량 파일 업로드")

usage_file = st.file_uploader("💾 사용량 엑셀 파일 업로드 (.xlsx)", type=["xlsx"], key="usage")

if usage_file:
    try:
        df_raw = pd.read_excel(usage_file)

        # Unnamed 인덱스 컬럼 제거
        df_raw = df_raw.loc[:, ~df_raw.columns.str.contains("^Unnamed")]

        # 청구코드 컬럼 찾기
        code_col = None
        for col in df_raw.columns:
            if "청구" in col and "코드" in col:
                code_col = col
                break

        # 소모량 or 사용량 컬럼 찾기
        usage_col = None
        for col in df_raw.columns:
            if "소모" in col or "사용" in col:
                usage_col = col
                break

        if not code_col or not usage_col:
            st.error("❌ '청구코드' 또는 '소모량/사용량' 컬럼을 찾을 수 없습니다.")
        else:
            df_usage = df_raw[[code_col, usage_col]].copy()
            df_usage.columns = ["청구코드", "소모량"]
            df_usage = df_usage.dropna()
            st.success("✅ 사용량 파일 자동 정제 완료")
            st.dataframe(df_usage)

    except Exception as e:
        st.error(f"❌ 파일 처리 중 오류 발생: {e}")

st.header("3️⃣ 직원용 주문 계산기")

if setup_file and usage_file:
    drug_input = st.text_input("🔍 약품명 또는 청구코드를 입력하세요")

    if drug_input:
        df_match = df_setup[
            df_setup["약품명"].str.contains(drug_input, case=False, na=False) |
            df_setup["청구코드"].astype(str).str.contains(drug_input)
        ]

        if df_match.empty:
            st.warning("검색된 약품이 없습니다.")
        else:
            for _, row in df_match.iterrows():
                st.subheader(f"💊 {row['약품명']} ({row['단위']}정)")

                code = row["청구코드"]
                unit_size = int(row["단위"])
                usage = df_usage[df_usage["청구코드"] == code]["소모량"]
                last_month_used = float(usage.iloc[0]) if not usage.empty else 0
                target_stock = math.ceil(last_month_used * 1.2)
                needed_qty = max(target_stock - last_month_used, 0)
                suggested_units = math.ceil(needed_qty / unit_size) if unit_size > 0 else 0

                col1, col2, col3 = st.columns(3)
                col1.metric("지난달 사용량", f"{last_month_used:.0f} 정")
                col2.metric("1.2배 재고 목표", f"{target_stock} 정")
                col3.metric("제안 발주량", f"{suggested_units} 통 (단위: {unit_size}정)")

                st.divider()
else:
    st.info("📂 먼저 셋업 파일과 사용량 파일을 업로드하세요.")
