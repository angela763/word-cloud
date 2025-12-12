# app.py
"""
Streamlit app: Upload a PDF -> show WordCloud and frequent words table
Run:
    streamlit run app.py
"""
import streamlit as st
from io import BytesIO
import re
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd

# PDF reader (pypdf preferred, fallback to PyPDF2)
try:
    from pypdf import PdfReader
except Exception:
    try:
        from PyPDF2 import PdfReader
    except Exception:
        PdfReader = None

st.set_page_config(page_title="PDF → WordCloud & Frequent Words", layout="wide")
st.title("PDF → WordCloud & Frequent Words")
st.markdown("Upload an Annual Report (or any PDF). The app extracts text, shows a word cloud and the top frequent words (with counts).")

# Sidebar options
st.sidebar.header("Options / Upload")
uploaded_file = st.sidebar.file_uploader("Upload PDF", type=["pdf"])
top_n = st.sidebar.number_input("Top N frequent words", min_value=5, max_value=200, value=30)
min_word_len = st.sidebar.number_input("Minimum word length to count", min_value=2, max_value=20, value=3)
max_wc_words = st.sidebar.number_input("Max words in WordCloud", min_value=10, max_value=1000, value=200)
show_stopwords = st.sidebar.checkbox("Exclude common stopwords", value=True)

# Basic stopword set (extend as needed)
COMMON_STOPWORDS = {
    "the","and","for","that","this","with","are","was","were","from","have","has","will",
    "company","companies","may","also","their","its","they","which","been","there","but",
    "not","all","our","we","in","on","at","by","to","of","a","an","is","be","as","or","if",
    "such","these","more","other","into","about"
}

def extract_text_from_pdf(file_like):
    if PdfReader is None:
        st.error("No PDF reader found. Install 'pypdf' or 'PyPDF2'.")
        return ""
    try:
        reader = PdfReader(file_like)
        pages = []
        for p in reader.pages:
            pages.append(p.extract_text() or "")
        return "\n".join(pages)
    except Exception as e:
        st.error(f"Error extracting PDF text: {e}")
        return ""

def preprocess_text(text):
    text = text.replace("\r\n", " ").replace("\n", " ")
    text = text.lower()
    # remove punctuation (keep alnum and spaces)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def make_wordcloud(text_blob, max_words=200):
    if not text_blob or not text_blob.strip():
        return None
    wc = WordCloud(width=900, height=450, max_words=max_words, background_color="white")
    wc.generate(text_blob)
    return wc

# Main
if not uploaded_file:
    st.info("Upload a PDF from the sidebar to begin.")
    st.stop()

raw_bytes = uploaded_file.read()
text = extract_text_from_pdf(BytesIO(raw_bytes))
if not text or not text.strip():
    st.error("No text extracted from PDF. The PDF might be scanned images (OCR required).")
    st.stop()

clean = preprocess_text(text)

# Tokenize and count
tokens = [w for w in clean.split() if len(w) >= int(min_word_len)]
if show_stopwords:
    tokens = [w for w in tokens if w not in COMMON_STOPWORDS]

freq = Counter(tokens)
if not freq:
    st.warning("No words found after preprocessing and filters. Adjust options (min word length / stopwords).")
    st.stop()

# Display WordCloud
st.header("Word Cloud (Full Document)")
wc = make_wordcloud(" ".join(tokens), max_words=int(max_wc_words))
if wc:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)
else:
    st.write("Unable to generate word cloud (not enough text).")

# Display frequent words table
st.header(f"Top {top_n} frequent words")
top_items = freq.most_common(int(top_n))
df_top = pd.DataFrame(top_items, columns=["word", "count"])
st.dataframe(df_top)

# Download CSV
csv_bytes = df_top.to_csv(index=False).encode("utf-8")
st.download_button("Download top words (.csv)", data=csv_bytes, file_name="top_words.csv", mime="text/csv")

# Optionally show raw extracted text preview
with st.expander("Preview extracted text (first 1000 chars)"):
    st.write(text[:1000] + ("..." if len(text) > 1000 else ""))

st.success("Done — adjust options in the sidebar and re-upload to re-run.")
