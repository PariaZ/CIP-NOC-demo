rimport streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
st.set_page_config(page_title="CIP-NOC Benchmark", layout="wide")
st.title("CIP-NOC Benchmark Evaluation")

uploaded_file = st.file_uploader("Upload benchmark CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Normalize column names if needed
    if "Human label" in df.columns and "human_label" not in df.columns:
        df["human_label"] = df["Human label"]

    st.sidebar.header("Filters")

    for col in ["source_file", "benchmark_case_type", "label", "human_label"]:
        if col in df.columns:
            options = sorted(df[col].dropna().astype(str).unique())
            selected = st.sidebar.multiselect(col, options, default=options)
            df = df[df[col].astype(str).isin(selected)]

    st.header("Benchamrk Overview")

    summary = {
        "Statistic": [
            "Model Name",
            "Benchmark Version",
            "Total CIP–NOC Pairs",
            "Unique CIP Codes",
            "Unique NOC Codes",
            "Number of Source Files",
        ],
        "Value": [
            "Llama 3",
            "v1.0",
            len(df),
            df["cip_code"].nunique() if "cip_code" in df.columns else None,
            df["noc_code"].nunique() if "noc_code" in df.columns else None,
            df["source_file"].nunique() if "source_file" in df.columns else None,
        ],
    }
    

    summary_df = pd.DataFrame(summary)
    st.dataframe(summary_df, use_container_width=True)


    labels = ["YES", "LEAN_YES", "LEAN_NO", "NO"]

    comparison = pd.DataFrame({
        "Label": labels * 2,
        "Source": ["Model"] * 4 + ["Human"] * 4,
        "Count": [
            *(df["label"].value_counts().reindex(labels, fill_value=0).tolist()),
            *(df["human_label"].value_counts().reindex(labels, fill_value=0).tolist())
        ]
    })

    fig = px.bar(
        comparison,
        x="Label",
        y="Count",
        color="Source",
        barmode="group",
        color_discrete_map={
            "Model": "#1f77b4",   # Blue
            "Human": "#ff7f0e"    # Orange
        },
        text="Count",
        title="Model vs Human Label Distribution"
    )

    fig.update_layout(
        xaxis_title="Label",
        yaxis_title="Number of Cases",
        legend_title="",
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

    if "label" in df.columns and "human_label" in df.columns:
        correct = (df["label"].astype(str) == df["human_label"].astype(str)).sum()
        total = len(df)
        accuracy = correct / total if total > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Correct predictions", correct)
        col2.metric("Total cases", total)
        col3.metric("Accuracy", f"{accuracy:.2%}")

        st.subheader("Confusion table: Human label vs Model label")
        confusion = pd.crosstab(df["human_label"], df["label"])
        st.dataframe(confusion, use_container_width=True)

        st.subheader("Cases where human label and model label differ")
        mismatch_df = df[df["label"].astype(str) != df["human_label"].astype(str)]
        st.dataframe(mismatch_df, use_container_width=True)

    st.header("Counts and unique values")

    for col in ["source_file", "cip_title", "noc_title", "benchmark_case_type"]:
        if col in df.columns:
            st.subheader(f"{col} counts")
            counts = df[col].value_counts().reset_index()
            counts.columns = [col, "count"]
            st.dataframe(counts, use_container_width=True)

    if "label" in df.columns:
        st.header("Label distribution")

        label_counts = df["label"].value_counts()

        st.subheader("Bar chart")
        st.bar_chart(label_counts)

        st.subheader("Pie chart")
        st.plotly_chart(
            {
                "data": [
                    {
                        "type": "pie",
                        "labels": label_counts.index.tolist(),
                        "values": label_counts.values.tolist(),
                    }
                ],
                "layout": {"title": "Distribution of Labels"},
            },
            use_container_width=True,
        )

    #if "cip_title" in df.columns:
       # st.header("Top 10 CIP programs in the benchmark")
        #cip_counts = df["cip_title"].value_counts().head(10).sort_values()
       #st.bar_chart(cip_counts)
    if "cip_title" in df.columns:
        st.header("Top 10 CIP Programs in the Benchmark")

        cip_counts = (
            df["cip_title"]
            .value_counts()
            .head(10)
            .reset_index()
        )

        cip_counts.columns = ["CIP Program", "Count"]

        chart = (
            alt.Chart(cip_counts)
            .mark_bar()
            .encode(
                x=alt.X("Count:Q", title="Frequency"),
                y=alt.Y("CIP Program:N", sort="-x", title="CIP Program"),
                tooltip=["CIP Program", "Count"]
            )
        )

    st.altair_chart(chart, use_container_width=True)

    if "noc_title" in df.columns:
        st.header("Top 10 NOC Occupations in the Benchmark")

        noc_counts = (
            df["noc_title"]
            .value_counts()
            .head(10)
            .reset_index()
        )

        noc_counts.columns = ["NOC Occupation", "Count"]

        chart = (
            alt.Chart(noc_counts)
            .mark_bar()
            .encode(
                x=alt.X("Count:Q", title="Frequency"),
                y=alt.Y("NOC Occupation:N", sort="-x", title="NOC Occupation"),
                tooltip=["NOC Occupation", "Count"]
            )
        )

    st.altair_chart(chart, use_container_width=True)

    #if "noc_title" in df.columns:
        #st.header("Top 10 NOC occupations in the benchmark")
        #noc_counts = df["noc_title"].value_counts().head(10).sort_values()
        #st.bar_chart(noc_counts)

    st.header("Full filtered data")
    st.dataframe(df, use_container_width=True)

    st.header("Check a CIP-NOC pathway")

    cip_options = (
        df[["cip_code", "cip_title"]]
        .drop_duplicates()
        .assign(cip_display=lambda x: x["cip_code"].astype(str) + " — " + x["cip_title"].astype(str))
    )

    selected_cip = st.selectbox(
        "Choose a CIP program",
        cip_options["cip_display"].sort_values()
    )

    selected_cip_code = selected_cip.split(" — ")[0]

    noc_options = (
        df[df["cip_code"].astype(str) == selected_cip_code][["noc_code", "noc_title"]]
        .drop_duplicates()
        .assign(noc_display=lambda x: x["noc_code"].astype(str) + " — " + x["noc_title"].astype(str))
    )

    selected_noc = st.selectbox(
        "Choose a NOC occupation",
        noc_options["noc_display"].sort_values()
    )

    selected_noc_code = selected_noc.split(" — ")[0]

    match = df[
        (df["cip_code"].astype(str) == selected_cip_code)
        & (df["noc_code"].astype(str) == selected_noc_code)
    ]

    if not match.empty:
        row = match.iloc[0]

        st.subheader("Pathway result")

        label = row["label"]

        if label in ["YES", "LEAN_YES"]:
            st.success(f"Pathway likely exists: {label}")
        elif label in ["LEAN_NO", "NO"]:
            st.error(f"Pathway likely does not exist: {label}")
        else:
            st.info(f"Label: {label}")

        if "confidence" in row:
            st.write("Confidence:", row["confidence"])

        if "rationale" in row:
            st.write("Rationale:", row["rationale"])

        if "Human label" in row:
            st.write("Human label:", row["Human label"])

        st.dataframe(match, use_container_width=True)
    else:
        st.warning("No matching CIP-NOC pair found in the benchmark.")
