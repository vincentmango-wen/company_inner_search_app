"""
このファイルは、画面表示に特化した関数定義のファイルです。
"""

############################################################
import streamlit as st
import utils
import constants as ct
import os


def display_app_title():
    """ページタイトルとスタイルを表示する簡易関数"""
    css_path = os.path.join(os.path.dirname(__file__), "static", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.markdown("<link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'>", unsafe_allow_html=True)
    st.markdown('<div class="main-title">社内情報特化型生成AI検索アプリ</div>', unsafe_allow_html=True)


def display_initial_ai_message():
    """AIメッセージの初期表示（中央の案内ボックス）"""
    with st.chat_message("assistant"):
        st.markdown('<div class=info-box>こんにちは。私は社内文書の情報をもとに回答する生成AIチャットボットです。サイドバーで利用目的を選択し、画面下部のチャット欄からメッセージを送信してください。</div>', unsafe_allow_html=True)
        warn_icon = getattr(ct, "WARNING_ICON", "⚠️ ")
        st.markdown(f"<div class=warn-box>{warn_icon}具体的に入力したほうが的確通りの回答を得やすいです。</div>", unsafe_allow_html=True)


def display_select_mode():
    """
    回答モードのラジオボタンを表示
    """
    # サイドバーに利用目的と説明を表示（画面下の入力欄が見えるようにメイン領域の高さを圧迫しない）
    st.sidebar.markdown('<div class="side-purpose">利用目的</div>', unsafe_allow_html=True)
    st.session_state.mode = st.sidebar.radio(
        label="",
        options=[ct.ANSWER_MODE_1, ct.ANSWER_MODE_2],
        label_visibility="collapsed"
    )

    st.sidebar.markdown('<div class="side-label"><b>【「社内文書検索」を選択した場合】</b></div>', unsafe_allow_html=True)
    st.sidebar.info('入力内容と関連性が高い社内文書のありかを検索できます。')
    st.sidebar.code('【入力例}\n社員の育成方針に関するMTGの議事録', wrap_lines=True, language=None)

    st.sidebar.markdown('<div class="side-label"><b>【「社内問い合わせ」を選択した場合】</b></div>', unsafe_allow_html=True)
    st.sidebar.info('質問・要望に対して、社内文書をもとに回答を得られます。')
    st.sidebar.code('【入力例}\n人事に所属している従業員情報を一覧化して', wrap_lines=True, language=None)



def display_conversation_log():
    """
    会話ログの一覧表示
    """
    # 会話ログのループ処理
    for message in st.session_state.messages:
        with st.chat_message(message.get("role", "user")):
            # user の場合はそのまま文字列表示
            if message.get("role") == "user":
                st.markdown(message.get("content", ""))
                continue

            # assistant の場合: content が dict であることを期待しているが、
            # 異なる型 (例: str) が入ることがあるため正規化して安全に扱う
            content = message.get("content")

            # content が文字列やその他の非辞書型の場合は辞書に変換して扱う
            if isinstance(content, str):
                content = {"mode": ct.ANSWER_MODE_2, "answer": content}

            if not isinstance(content, dict):
                # 想定外の型はそのまま表示して続行
                st.markdown(str(content))
                continue

            mode = content.get("mode", ct.ANSWER_MODE_2)

            # 社内文書検索モード
            if mode == ct.ANSWER_MODE_1:
                if not content.get("no_file_path_flg"):
                    st.markdown(content.get("main_message", ""))
                    main_file_path = content.get("main_file_path")
                    if main_file_path:
                        icon = utils.get_source_icon(main_file_path)
                        if "main_page_number" in content:
                            st.success(f"{main_file_path}(ページNo.{content['main_page_number']+1})", icon=icon)
                        else:
                            st.success(f"{main_file_path}", icon=icon)

                    if "sub_message" in content:
                        st.markdown(content.get("sub_message", ""))
                        for sub_choice in content.get("sub_choices", []):
                            icon = utils.get_source_icon(sub_choice.get('source', ''))
                            if "page_number" in sub_choice:
                                st.info(f"{sub_choice['source']}(ページNo.{sub_choice['page_number']+1})", icon=icon)
                            else:
                                st.info(f"{sub_choice.get('source', '')}", icon=icon)
                else:
                    st.markdown(content.get("answer", ""))

            # 社内問い合わせモード
            else:
                st.markdown(content.get("answer", ""))
                if "file_info_list" in content:
                    st.divider()
                    st.markdown(f"##### {content.get('message', '情報源')}")
                    for file_info in content.get('file_info_list', []):
                        icon = utils.get_source_icon(file_info)
                        st.info(file_info, icon=icon)
                        if content.get("main_file_path"):
                            st.success(f"{content.get('main_file_path')}", icon=icon)

                    if "sub_message" in content:
                        st.markdown(content.get("sub_message", ""))
                        for sub_choice in content.get("sub_choices", []):
                            icon = utils.get_source_icon(sub_choice.get('source', ''))
                            if "page_number" in sub_choice:
                                st.info(f"{sub_choice['source']}(ページNo.{sub_choice['page_number']+1})", icon=icon)
                            else:
                                st.info(f"{sub_choice.get('source', '')}", icon=icon)
                else:
                    st.markdown(content.get("answer", ""))


def display_search_llm_response(llm_response):
    """
    「社内文書検索」モードにおけるLLMレスポンスを表示

    Args:
        llm_response: LLMからの回答

    Returns:
        LLMからの回答を画面表示用に整形した辞書データ
    """
    # LLMからのレスポンスに参照元情報が入っており、かつ「該当資料なし」が回答として返された場合
    if llm_response["context"] and llm_response["answer"] != ct.NO_DOC_MATCH_ANSWER:

        # ==========================================
        # ユーザー入力値と最も関連性が高いメインドキュメントのありかを表示
        # ==========================================
        # LLMからのレスポンス（辞書）の「context」属性の中の「0」に、最も関連性が高いドキュメント情報が入っている
        main_file_path = llm_response["context"][0].metadata["source"]

        # 補足メッセージの表示
        main_message = "入力内容に関する情報は、以下のファイルに含まれている可能性があります。"
        st.markdown(main_message)
        
        # 参照元のありかに応じて、適したアイコンを取得
        icon = utils.get_source_icon(main_file_path)
        # ページ番号が取得できた場合のみ、ページ番号を表示（ドキュメントによっては取得できない場合がある）
        if "page" in llm_response["context"][0].metadata:
            # ページ番号を取得
            main_page_number = llm_response["context"][0].metadata["page"]
            # 「メインドキュメントのファイルパス」と「ページ番号」を表示
            st.success(f"{main_file_path}(ページNo.{main_page_number+1})", icon=icon)
        else:
            # 「メインドキュメントのファイルパス」を表示
            st.success(f"{main_file_path}", icon=icon)

        # ==========================================
        # ユーザー入力値と関連性が高いサブドキュメントのありかを表示
        # ==========================================
        # メインドキュメント以外で、関連性が高いサブドキュメントを格納する用のリストを用意
        sub_choices = []
        # 重複チェック用のリストを用意
        duplicate_check_list = []

        # ドキュメントが2件以上検索できた場合（サブドキュメントが存在する場合）のみ、サブドキュメントのありかを一覧表示
        # 「source_documents」内のリストの2番目以降をスライスで参照（2番目以降がなければfor文内の処理は実行されない）
        for document in llm_response["context"][1:]:
            # ドキュメントのファイルパスを取得
            sub_file_path = document.metadata["source"]

            # メインドキュメントのファイルパスと重複している場合、処理をスキップ（表示しない）
            if sub_file_path == main_file_path:
                continue
            
            # 同じファイル内の異なる箇所を参照した場合、2件目以降のファイルパスに重複が発生する可能性があるため、重複を除去
            if sub_file_path in duplicate_check_list:
                continue

            # 重複チェック用のリストにファイルパスを順次追加
            duplicate_check_list.append(sub_file_path)
            
            # ページ番号が取得できない場合のための分岐処理
            if "page" in document.metadata:
                # ページ番号を取得
                sub_page_number = document.metadata["page"]
                # 「サブドキュメントのファイルパス」と「ページ番号」の辞書を作成
                sub_choice = {"source": sub_file_path, "page_number": sub_page_number}
            else:
                # 「サブドキュメントのファイルパス」の辞書を作成
                sub_choice = {"source": sub_file_path}
            
            # 後ほど一覧表示するため、サブドキュメントに関する情報を順次リストに追加
            sub_choices.append(sub_choice)
        
        # サブドキュメントが存在する場合のみの処理
        if sub_choices:
            # 補足メッセージの表示
            sub_message = "その他、ファイルありかの候補を提示します。"
            st.markdown(sub_message)

            # サブドキュメントに対してのループ処理
            for sub_choice in sub_choices:
                # 参照元のありかに応じて、適したアイコンを取得
                icon = utils.get_source_icon(sub_choice['source'])
                # ページ番号が取得できない場合のための分岐処理
                if "page_number" in sub_choice:
                    # 「サブドキュメントのファイルパス」と「ページ番号」を表示
                    st.info(f"{sub_choice['source']}(ページNo.{sub_choice['page_number']+1})", icon=icon)
                else:
                    # 「サブドキュメントのファイルパス」を表示
                    st.info(f"{sub_choice['source']}", icon=icon)
        
        # 表示用の会話ログに格納するためのデータを用意
        # - 「mode」: モード（「社内文書検索」or「社内問い合わせ」）
        # - 「main_message」: メインドキュメントの補足メッセージ
        # - 「main_file_path」: メインドキュメントのファイルパス
        # - 「main_page_number」: メインドキュメントのページ番号
        # - 「sub_message」: サブドキュメントの補足メッセージ
        # - 「sub_choices」: サブドキュメントの情報リスト
        content = {}
        content["mode"] = ct.ANSWER_MODE_1
        content["main_message"] = main_message
        content["main_file_path"] = main_file_path
        # メインドキュメントのページ番号は、取得できた場合にのみ追加
        if "page" in llm_response["context"][0].metadata:
            content["main_page_number"] = main_page_number
        # サブドキュメントの情報は、取得できた場合にのみ追加
        if sub_choices:
            content["sub_message"] = sub_message
            content["sub_choices"] = sub_choices
    
    # LLMからのレスポンスに、ユーザー入力値と関連性の高いドキュメント情報が入って「いない」場合
    else:
        # 関連ドキュメントが取得できなかった場合のメッセージ表示
        st.markdown(ct.NO_DOC_MATCH_MESSAGE)

        # 表示用の会話ログに格納するためのデータを用意
        # - 「mode」: モード（「社内文書検索」or「社内問い合わせ」）
        # - 「answer」: LLMからの回答
        # - 「no_file_path_flg」: ファイルパスが取得できなかったことを示すフラグ（画面を再描画時の分岐に使用）
        content = {}
        content["mode"] = ct.ANSWER_MODE_1
        content["answer"] = ct.NO_DOC_MATCH_MESSAGE
        content["no_file_path_flg"] = True
    
    return content


def display_contact_llm_response(llm_response):
    """
    「社内問い合わせ」モードにおけるLLMレスポンスを表示

    Args:
        llm_response: LLMからの回答

    Returns:
        LLMからの回答を画面表示用に整形した辞書データ
    """
    # LLMからの回答を表示
    st.markdown(llm_response["answer"])

    # ユーザーの質問・要望に適切な回答を行うための情報が、社内文書のデータベースに存在しなかった場合
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        # 区切り線を表示
        st.divider()

        # 補足メッセージを表示
        message = "情報源"
        st.markdown(f"##### {message}")

        # 参照元のファイルパスの一覧を格納するためのリストを用意
        file_path_list = []
        file_info_list = []

        # LLMが回答生成の参照元として使ったドキュメントの一覧が「context」内のリストの中に入っているため、ループ処理
        for document in llm_response["context"]:
            # ファイルパスを取得
            file_path = document.metadata["source"]
            # ファイルパスの重複は除去
            if file_path in file_path_list:
                continue

            # ページ番号が取得できた場合のみ、ページ番号を表示（ドキュメントによっては取得できない場合がある）
            if "page" in document.metadata:
                # ページ番号を取得
                page_number = document.metadata["page"]
                # 「ファイルパス」と「ページ番号」
                file_info = f"{file_path} (ページNo.{page_number+1})"
            else:
                # 「ファイルパス」のみ
                file_info = f"{file_path}"

            # 参照元のありかに応じて、適したアイコンを取得
            icon = utils.get_source_icon(file_path)
            # ファイル情報を表示
            st.info(file_info, icon=icon)

            # 重複チェック用に、ファイルパスをリストに順次追加
            file_path_list.append(file_path)
            # ファイル情報をリストに順次追加
            file_info_list.append(file_info)

    # 表示用の会話ログに格納するためのデータを用意
    # - 「mode」: モード（「社内文書検索」or「社内問い合わせ」）
    # - 「answer」: LLMからの回答
    # - 「message」: 補足メッセージ
    # - 「file_path_list」: ファイルパスの一覧リスト
    content = {}
    content["mode"] = ct.ANSWER_MODE_2
    content["answer"] = llm_response["answer"]
    # 参照元のドキュメントが取得できた場合のみ
    if llm_response["answer"] != ct.INQUIRY_NO_MATCH_ANSWER:
        content["message"] = message
        content["file_info_list"] = file_info_list

    return content