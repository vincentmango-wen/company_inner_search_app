# 概要
# 会社内検索アプリの回答精度評価し、改善するためのスクリプト
# 評価方法：chunk_sizeやtop_kの値を変えて、回答の質がどう変化するかを確認する
# 実行方法：streamlit run test_evalution.py
# 注意点：main.pyと同じディレクトリで実行すること

# 必要ライブラリの読み込み
import components as cn # 画面表示系の関数が定義されているモジュール
import utils # 画面表示以外の様々な関数が定義されているモジュール
import initialize as init # アプリ起動時に実行される初期化処理が記述された関数
import streamlit as st # streamlitアプリの表示を担当するモジュール
import constants as ct # 変数（定数）がまとめて定義・管理されているモジュール
import logging
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.retrievers import BM25Retriever as BM25
from langchain.retrievers import EnsembleRetriever
from langchain.schema import Document as LcDocument
import os
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

path = ct.RAG_TOP_FOLDER_PATH
file_extension = os.path.splitext(path)[1]
    # ファイル名（拡張子を含む）を取得
file_name = os.path.basename(path)

# 想定していたファイル形式の場合のみ読み込む
if file_extension in ct.SUPPORTED_EXTENSIONS:
    # ファイルの拡張子に合ったdata loaderを使ってデータ読み込み
    loader = ct.SUPPORTED_EXTENSIONS[file_extension](path)
    docs = loader.load()

    # CSV の場合、読み込まれた各行（Document）を10件ずつまとめて1つの Document にする
    if file_extension == ".csv":
        grouped_docs = []
        # docs は各行を表す Document のリストを想定
        for i in range(0, len(docs), 5):
            group = docs[i:i+5]
            # 各行のテキストを改行で連結して 1 件の Document にまとめる
            combined_content = "\n".join([getattr(d, 'page_content', str(d)) for d in group])
            # メタデータには元ファイル名と行範囲を記録
            start_row = i + 1
            end_row = i + len(group)
            metadata = {"source": file_name, "row_range": f"{start_row}-{end_row}"}
            new_doc = LcDocument(page_content=combined_content, metadata=metadata)
            grouped_docs.append(new_doc)
            st.write("grouped_docs:", grouped_docs)
# ドキュメント読み込み
pages = init.load_data_sources(path=ct.RAG_TOP_FOLDER_PATH)

st.write(pages)

# 埋め込みモデルの初期化
embedding_model = OpenAIEmbeddings()

# チャットモデルの初期化
llm = ChatOpenAI(model=ct.MODEL, temperature=ct.TEMPERATURE)



# テキスト分割設定: chunk_overlap は重複トークンを確保してコンテキスト切れを緩和
text_splitter = CharacterTextSplitter(
    chunk_size=ct.CHUNK_SIZE,
    chunk_overlap=ct.CHUNK_OVERLAP
)

# pages (Document のリスト) をチャンク化して、Document のリストを返す
splitted_pages = text_splitter.split_documents(pages)
st.write(splitted_pages)