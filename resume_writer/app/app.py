import streamlit as st
import re

st.set_page_config(layout="wide")

if "markdown_content" not in st.session_state:
    st.session_state.markdown_content = """
# My Document

This is an example of markdown content.

## Section 1

Some text in section 1.

* List item 1
* List item 2

## Section 2

More text in section 2.
    """

if "sub_page" not in st.session_state:
    st.session_state.sub_page = "Page 1"

if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Function 1"


def visualize_content(page_name, text_input, doc1, doc2):
    content = f"## {page_name} Content\n\n"
    if text_input:
        content += f"**Entered Text:** {text_input}\n\n"
    if doc1:
        content += f"**Doc 1:** {doc1.name} (Uploaded)\n\n"
    if doc2:
        content += f"**Doc 2:** {doc2.name} (Uploaded)\n\n"
    return content


def apply_function_1():
    st.session_state.markdown_content += (
        "\n\n**Function 1 Applied:** Added a new paragraph."
    )
    st.toast("Function 1 applied!", icon="✅")


def apply_function_2():
    st.session_state.markdown_content = st.session_state.markdown_content.replace(
        "Section 1", "**Modified Section 1**"
    )
    st.toast("Function 2 applied!", icon="✅")


def apply_function_3():
    st.session_state.markdown_content = st.session_state.markdown_content.replace(
        "* List item", "* **List item**"
    )
    st.toast("Function 3 applied!", icon="✅")


def apply_function_4():
    st.session_state.markdown_content = re.sub(
        r"## Section 2.*?(\n##|$)",
        r"\1",
        st.session_state.markdown_content,
        flags=re.DOTALL,
    )
    st.toast("Function 4 applied!", icon="✅")


if st.sidebar.button("Function 1", key="func1_btn", use_container_width=True):
    st.session_state.selected_page = "Function 1"
if st.sidebar.button("Function 2", key="func2_btn", use_container_width=True):
    st.session_state.selected_page = "Function 2"


if st.session_state.selected_page == "Function 1":
    st.title("Function 1: Input and Visualize")

    input_col, upload_col = st.columns([0.7, 0.3])
    with input_col:
        text_input = st.text_area("Enter Text", height=200)
    with upload_col:
        doc1 = st.file_uploader("Upload Doc 1", type=["pdf", "txt", "docx"])
        doc2 = st.file_uploader("Upload Doc 2", type=["pdf", "txt", "docx"])

    tabs = st.tabs(["Page 1", "Page 2", "Page 3", "Page 4"])
    with tabs[0]:
        if st.session_state.sub_page != "Page 1":
            st.session_state.sub_page = "Page 1"
        content = visualize_content(st.session_state.sub_page, text_input, doc1, doc2)
        st.markdown(content)
    with tabs[1]:
        if st.session_state.sub_page != "Page 2":
            st.session_state.sub_page = "Page 2"
        content = visualize_content(st.session_state.sub_page, text_input, doc1, doc2)
        st.markdown(content)
    with tabs[2]:
        if st.session_state.sub_page != "Page 3":
            st.session_state.sub_page = "Page 3"
        content = visualize_content(st.session_state.sub_page, text_input, doc1, doc2)
        st.markdown(content)
    with tabs[3]:
        if st.session_state.sub_page != "Page 4":
            st.session_state.sub_page = "Page 4"
        content = visualize_content(st.session_state.sub_page, text_input, doc1, doc2)
        st.markdown(content)


elif st.session_state.selected_page == "Function 2":
    st.title("Function 2: Markdown Editor")

    left_column, right_column = st.columns([0.7, 0.3])
    with left_column:
        st.markdown(st.session_state.markdown_content)
    with right_column:
        st.button(
            "Apply Function 1", on_click=apply_function_1, use_container_width=True
        )
        st.button(
            "Apply Function 2", on_click=apply_function_2, use_container_width=True
        )
        st.button(
            "Apply Function 3", on_click=apply_function_3, use_container_width=True
        )
        st.button(
            "Apply Function 4", on_click=apply_function_4, use_container_width=True
        )
