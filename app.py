import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Smart Data Analyzer", layout="wide")
st.title("📊 Smart Data Analyzer")

file = st.file_uploader("Upload a CSV file", type="csv")

if file:
    try:
        df = pd.read_csv(file)
    except Exception as e:
        st.error(f"Could not read this file: {e}")
        st.stop()

    if df.empty:
        st.warning("The file is empty.")
        st.stop()

    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    st.sidebar.header("Clean data")
    action = st.sidebar.radio(
        "Missing values",
        ["Keep as is", "Drop rows with missing", "Fill numeric with mean"],
    )
    if action == "Drop rows with missing":
        df = df.dropna()
    elif action == "Fill numeric with mean":
        num = df.select_dtypes(include="number").columns
        df[num] = df[num].fillna(df[num].mean())

    st.sidebar.download_button(
        "Download cleaned CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="cleaned_data.csv",
        mime="text/csv",
    )

    st.success(f"Loaded {df.shape[0]} rows × {df.shape[1]} columns")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Preview", "Inspect", "Missing values", "Statistics", "Charts"]
    )

    with tab1:
        st.dataframe(df.head(20))

    with tab2:
        c1, c2 = st.columns(2)
        c1.metric("Rows", df.shape[0])
        c2.metric("Columns", df.shape[1])
        info = pd.DataFrame({
            "Column": df.columns,
            "Data type": df.dtypes.astype(str).values,
            "Unique values": df.nunique().values,
        })
        st.dataframe(info, width="stretch")

    with tab3:
        missing = df.isnull().sum()
        report = pd.DataFrame({
            "Column": df.columns,
            "Missing": missing.values,
            "Missing %": (missing.values / len(df) * 100).round(2),
        })
        st.dataframe(report, width="stretch")
        if missing.sum() == 0:
            st.success("No missing values 🎉")

    with tab4:
        num_cols = [c for c in df.select_dtypes(include="number").columns if df[c].notna().any()]
        if not num_cols:
            st.warning("No numeric columns found.")
        else:
            st.subheader("Summary statistics")
            st.dataframe(df[num_cols].describe().T, width="stretch")

            st.subheader("Single column")
            col = st.selectbox("Choose a column", num_cols)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Mean", round(df[col].mean(), 2))
            c2.metric("Median", round(df[col].median(), 2))
            c3.metric("Min", df[col].min())
            c4.metric("Max", df[col].max())

    with tab5:
        all_cols = df.columns.tolist()
        num_cols = df.select_dtypes(include="number").columns.tolist()

        chart = st.selectbox("Chart type", ["Histogram", "Scatter", "Bar (counts)", "Box"])

        if chart == "Histogram" and num_cols:
            x = st.selectbox("Column", num_cols, key="h")
            bins = st.slider("Bins", 10, 100, 30)
            clip = st.checkbox("Hide extreme values (keep 1st to 99th percentile)")
            data = df
            if clip:
                lo, hi = df[x].quantile([0.01, 0.99])
                data = df[(df[x] >= lo) & (df[x] <= hi)]
            st.plotly_chart(px.histogram(data, x=x, nbins=bins), width="stretch")
        elif chart == "Scatter" and len(num_cols) >= 2:
            x = st.selectbox("X axis", num_cols, key="sx")
            y = st.selectbox("Y axis", num_cols, index=1, key="sy")
            st.plotly_chart(px.scatter(df, x=x, y=y), width="stretch")
        elif chart == "Bar (counts)":
            x = st.selectbox("Column", all_cols, key="b")
            counts = df[x].value_counts().head(20).reset_index()
            counts.columns = [x, "count"]
            st.plotly_chart(px.bar(counts, x=x, y="count"), width="stretch")
        elif chart == "Box" and num_cols:
            x = st.selectbox("Column", num_cols, key="bx")
            st.plotly_chart(px.box(df, y=x), width="stretch")
        else:
            st.warning("Not enough suitable columns for this chart.")