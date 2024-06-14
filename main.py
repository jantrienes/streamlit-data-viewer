import markdown
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("RAG Evaluation Overview")


@st.cache_data
def load_data(file):
    data = pd.read_json(file)
    return data


def md_to_text(md):
    html = markdown.markdown(md)
    soup = BeautifulSoup(html, features="html.parser")
    return soup.get_text()


def paginate(data_length, page_size):
    ranges = []
    labels = []
    num_pages = (data_length + page_size - 1) // page_size
    for i in range(num_pages):
        start_index = i * page_size
        end_index = min(start_index + page_size, data_length)
        ranges.append((start_index, end_index))
        labels.append(f"Questions: {start_index} -- {end_index}")
    return ranges, labels


def render(data):
    ranges, labels = paginate(len(data), 15)
    data_slice = st.selectbox(
        "Select data slice", ranges, format_func=lambda x: labels[ranges.index(x)]
    )

    col_spec = {
        "ID": 0.05,
        "Question": 0.2,
        "Answers": 0.2,
        "Contexts": 0.4,
        "Latency": 0.1,
    }
    headers = col_spec.keys()
    sizes = col_spec.values()

    data = data.iloc[data_slice[0] : data_slice[1]]
    for _, row in data.iterrows():
        cols = st.columns(sizes)
        for col, name in zip(cols, headers):
            col.write(f"**{name}**")

        cols = st.columns(sizes)

        cols[0].write(f"`{row['id']}`")
        cols[1].write(row["question"])
        cols[2].success(f"**Reference:** {row['reference_answer']}")

        if not row["generated_answer"]:
            cols[2].error("Could not generate answer.")
        else:
            cols[2].info(f"**Generated:** {row['generated_answer']}")

        with cols[3]:
            contexts = row["contexts"] if row["contexts"] else []
            for context in contexts:
                content = context["content"][:200] + "..."
                content = md_to_text(content)
                label = f"_{content}_ **Score:** `{str(round(context['score'], 1))}`"

                with st.expander(label):
                    st.write("**URL**:", context["url"])
                    st.write(context["content"])

        cols[4].write(round(row["latency"], 2))
        st.divider()


holder = st.empty()
uploaded_file = holder.file_uploader("Upload a JSON file", type="json")
# uploaded_file = 'output/synthetic_questions_responses_final.json'
if uploaded_file:
    data = load_data(uploaded_file)
    holder.empty()
    render(data)
