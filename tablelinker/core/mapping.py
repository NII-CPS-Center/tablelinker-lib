"""
mapping.py

2つのテーブルの項目リストを最適マッピングする

Usage: python mapping.py
"""

import copy
from logging import getLogger
import os
from typing import List

from munkres import Munkres
import numpy as np
from transformers import AutoModel, AutoTokenizer

logger = getLogger(__name__)


class StringSimilarity(object):
    """
    編集距離による文字列間の類似度を計算する strsim の実装
    by Akiko Aizawa
    """

    @classmethod
    def strsim(cls, term1, term2):
        """
        文字列 term1 と term2 の類似度を計算する

        Parameters
        ----------
        term1, term2: str

        Return
        ------
        float
            類似度（0 .. 1, 同一の場合1）
        """
        nlist1 = list(term1)
        nlist2 = list(term2)
        ulist1 = []
        for i, c in enumerate(nlist1):
            if i == 0:
                ulist1.append("^"+nlist1[i])
            else:
                ulist1.append(nlist1[i-1]+nlist1[i])

        ulist1.append(nlist1[-1]+"$")
        ulist2 = []
        for i, c in enumerate(nlist2):
            if i == 0:
                ulist2.append("^"+nlist2[i])
            else:
                ulist2.append(nlist2[i-1]+nlist2[i])

        ulist2.append(nlist2[-1]+"$")
        (match, mlist1, mlist2) = cls._match_str(ulist1, ulist2, 'char')
        size1 = len(ulist1)
        size2 = len(ulist2)
        simval = (2 * match)/(size1 + size2)
        # simval = math.exp(simval)/(math.exp(simval)+math.exp(1-simval))
        return simval

    @classmethod
    def _match_str(cls, list1, list2, flag):
        """
        strsim が呼び出すサブメソッド
        """
        _subcost = 10
        _delcost = 1
        _inscost = 1

        size1 = len(list1)
        size2 = len(list2)

        m = [[0 for i in range(size1+1)] for j in range(size2+1)]
        for i in range(1, size1+1):
            m[0][i] = i * _delcost
        for j in range(1, size2+1):
            m[j][0] = j * _inscost

        for j in range(1, size2+1):
            m[j][0] = j * _inscost
            for i in range(1, size1+1):
                v1 = m[j][i-1] + _delcost
                v2 = m[j-1][i] + _inscost

                if (list1[i-1] == list2[j-1]):
                    v3 = m[j-1][i-1]
                else:
                    subcost = _subcost
                    if flag == 'word':
                        simval = cls.strsim(list1[i-1], list2[j-1])
                        subcost = (1-simval)*2
                    v3 = m[j-1][i-1] + subcost

                minval = min(v1, v2, v3)
                m[j][i] = minval

        mlist1 = [0]*(size1)
        mlist2 = [0]*(size2)
        i = size1
        j = size2
        match = 0
        while (i > 0) and (j > 0):
            v1 = m[j][i-1]
            v2 = m[j-1][i-1]
            v3 = m[j-1][i]
            if (v2 <= v1) and (v2 <= v3):
                if (m[j-1][i-1] == m[j][i]):
                    mlist2[j-1] = 1
                    mlist1[i-1] = 1
                    match += 1

                i -= 1
                j -= 1
            elif (v1 <= v3):
                i -= 1
            else:
                j -= 1

        return (match, mlist1, mlist2)


class Similarity(object):
    """
    日本語表記のラベルから、語ベクトルを計算するクラス
    by Akiko Aizawa
    """

    def __init__(self):
        """
        トークナイザと事前学習済みモデルを取得する

        Note
        ----
        毎回ウェブからダウンロードすると遅いので、
        ``./transformer_data/{tokenizer, model}`` に保存し、
        再利用する。
        """
        tokenizer_dir = os.path.join(
            os.path.dirname(__file__), 'transformer_data/tokenizer')
        if os.path.exists(tokenizer_dir):
            logger.debug("Loading saved tokenizer from {}".format(
                tokenizer_dir))
            self.tokenizer = AutoTokenizer.from_pretrained(
                tokenizer_dir)
        else:
            logger.debug("Loading tokenizer from web")
            os.makedirs(tokenizer_dir, 0o755, exist_ok=True)
            self.tokenizer = AutoTokenizer.from_pretrained(
                "cl-tohoku/bert-base-japanese-whole-word-masking")
            self.tokenizer.save_pretrained(tokenizer_dir)
            logger.debug("Save tokenizer to {}".format(
                tokenizer_dir))

        model_dir = os.path.join(
            os.path.dirname(__file__), 'transformer_data/model')
        if os.path.exists(model_dir):
            logger.debug("Loading saved model from {}".format(
                model_dir))
            self.model = AutoModel.from_pretrained(
                model_dir)
        else:
            logger.debug("Loading model from web")
            os.makedirs(model_dir, 0o755, exist_ok=True)
            self.model = AutoModel.from_pretrained(
                "cl-tohoku/bert-base-japanese-whole-word-masking")
            self.model.save_pretrained(model_dir)
            logger.debug("Save model to {}".format(
                model_dir))

        self.get_vectors()

    def get_vectors(self):
        """
        事前計算済みベクトルをメモリに展開する
        """
        token_embeddings = self.model.get_input_embeddings().\
            weight.clone()

        vocab = self.tokenizer.get_vocab()
        self.vectors = {}
        for idx in vocab.values():
            self.vectors[idx] = token_embeddings[idx].detach().numpy().copy()

    def item2vec(self, text: str):
        """
        文字列 text をトークナイザで分解し、単語ベクトルの
        平均を計算して返す

        Parameters
        ----------
        text: str
            語ベクトルを計算したい文字列

        Returns
        -------
        np.array
            語ベクトル
        """
        ids = self.tokenizer.encode(text, add_special_tokens=False)
        embeddings = np.array([self.vectors[id] for id in ids])
        average_embeddings = np.average(embeddings, axis=0)
        assert average_embeddings.shape == (768,)
        return average_embeddings

    @staticmethod
    def cos_sim(v1, v2):
        """
        語ベクトル間のコサイン類似度を計算する

        Parameters
        ----------
        v1, v2: np.array
            2つの語ベクトル

        Returns
        -------
        float
            コサイン類似度 (0..1, 一致する場合 1)
        """
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


class ItemsPair(object):
    """
    2つテーブルの項目見出しを管理するクラス

    Attributes
    ----------
    items0, items1: List[str]
        テーブル0, 1 の項目見出しリスト
    mxsim: np.matrix
        テーブル0の見出し(m)×テーブル1の見出し(n)の
        語ベクトル間コサイン類似度を格納する行列
    mxed: np.matrix
        テーブル0の見出し(m)×テーブル1の見出し(n)の
        編集距離による類似度を格納する行列
    """
    similarity = None  # Similarity()  # 時間がかかるのでオンデマンド登録

    def __init__(self, items0: List[str], items1: List[str]):
        """
        Parameters
        ----------
        items0: List[str]
            テーブル0の項目見出しリスト
        items1: List[str]
            テーブル1の項目見出しリスト
        """
        self.items0 = [x if x != '' else 'empty' for x in items0]
        self.items1 = [x if x != '' else 'empty' for x in items1]
        self.mxsim = None
        self.mxed = None

    def get_weighted_matrix(self):
        """
        items0 と items1 の類似度を計算し、mxsim, mxed に格納する

        Note
        ----
        Munkres を利用するため、類似度をマイナスに反転してコストとする。
        mxsim, mxed の要素は [-1 .. 0] の値をとる。
        また、各行列の次元は m と n の大きい方に合わせた正方行列。
        """
        if self.mxsim is not None and self.mxed is not None:
            return self.mxsim, self.mxed

        if self.__class__.similarity is None:
            self.__class__.similarity = Similarity()

        vec0 = [
            self.__class__.similarity.item2vec(name)
            for name in self.items0]
        vec1 = [
            self.__class__.similarity.item2vec(name)
            for name in self.items1]
        dim = max(len(self.items0), len(self.items1))
        self.mxsim = np.zeros((dim, dim))
        self.mxed = np.zeros((dim, dim))

        for j in range(len(vec1)):
            for i in range(len(vec0)):
                ed = StringSimilarity.strsim(self.items0[i], self.items1[j])
                sim = Similarity.cos_sim(vec0[i], vec1[j])
                if sim < 0.0:
                    sim = 0.0

                self.mxsim[i, j] = -1.0 * sim
                self.mxed[i, j] = -1.0 * ed

        return self.mxsim, self.mxed

    def match(self):
        """
        Munkres による割り当て計算を行う

        Returns
        -------
        np.matrix
            最適割り当てを行った結果行列。
        """
        self.get_weighted_matrix()

        mtx = self.mxsim
        ansMtx = Munkres().compute(copy.copy(mtx))
        asum = sum([mtx[idx] for idx in ansMtx])

        logger.debug(ansMtx)
        logger.debug(f"Minimum sum = {asum}")
        logger.debug(mtx)

        return ansMtx

    def mapping(self):
        """
        最適割り当ての結果を人間可読な形に戻す

        Returns
        -------
        List[str, str, float]
            - テーブル0の項目見出し
            - 対応するテーブル1の項目見出し
            - 項目間の類似度（0..1）
        """
        pairs = self.match()
        results = []
        for pair in pairs:
            i, j = pair[0], pair[1]
            results.append([
                self.items0[i] if i < len(self.items0) else None,
                self.items1[j] if j < len(self.items1) else None,
                -self.mxsim[i, j]])

        return results

    def mapping_exact(self):
        """
        完全文字列一致による割り当てを行ない、
        結果を人間可読な形で返す

        Returns
        -------
        List[str, str, float]
            - テーブル0の項目見出し
            - 対応するテーブル1の項目見出し
            - 項目間の類似度（0 または 1）
        """
        results = []
        items1 = copy.copy(self.items1)
        for item in self.items0:
            if item in items1:
                items1.remove(item)
                results.append([item, item, 1.0])
            else:
                results.append([item, None, 0.0])

        for item in items1:
            results.append([None, item, 0.0])

        return results


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.WARNING)

    items_kanko = [
        '都道府県コード又は市区町村コード', 'NO', '都道府県名',
        '市区町村名', '名称', '名称_カナ', '名称_英語',
        'POIコード', '住所', '方書', '緯度', '経度',
        '利用可能曜日', '開始時間', '終了時間', '利用可能日時特記事項',
        '料金（基本）', '料金（詳細）', '説明', '説明_英語',
        'アクセス方法', '駐車場情報', 'バリアフリー情報',
        '連絡先名称', '連絡先電話番号', '連絡先内線番号',
        '画像', '画像_ライセンス', 'URL', '備考']

    items_yamaguchi = [
        '都道府県コード又は市区町村コード', 'NO', '都道府県名',
        '市区町村名', '名称', '名称_カナ', '名称_英語',
        'POIコード', '住所', '方書', '緯度', '経度',
        '利用可能曜日', '開始時間', '終了時間', '利用可能日時特記事項',
        '料金(基本)', '料金(詳細)', '説明', '説明_英語',
        'アクセス方法', '駐車場情報', 'バリアフリー情報',
        '連絡先名称', '連絡先電話番号', '連絡先内線番号',
        '画像', '画像_ライセンス', 'URL', '備考']

    items_sasebo = [
        '名称', '住所', '緯度', '経度', '電話番号', 'URL'
    ]

    items_shinjuku_bunkazai = [
        '都道府県コード又は市区町村コード', 'NO', '都道府県名',
        '市区町村名', '名称', '名称_カナ', '名称_通称', '名称_英語',
        '文化財分類', '種類', '場所名称',
        '住所', '方書', '緯度', '経度', '電話番号', '内線番号',
        '員数（数）', '員数（単位）', '法人番号', '所有者等',
        '文化財指定日',
        '利用可能曜日', '開始時間', '終了時間', '利用可能日時特記事項',
        '画像', '画像_ライセンス', '概要']

    print("山口県観光情報 - 推奨データセット（観光）")
    print("----------")
    pair = ItemsPair(items_yamaguchi, items_kanko)
    for result in pair.mapping():
        print('{}\t{}\t{:.2f}'.format(
            result[0], result[1], result[2]))

    print("佐世保観光情報 - 推奨データセット（観光）")
    print("----------")
    pair = ItemsPair(items_sasebo, items_kanko)
    for result in pair.mapping():
        print('{}\t{}\t{:.2f}'.format(
            result[0], result[1], result[2]))

    print("推奨データセット（観光） - 佐世保観光情報")
    print("----------")
    pair = ItemsPair(items_kanko, items_sasebo)
    for result in pair.mapping():
        print('{}\t{}\t{:.2f}'.format(
            result[0], result[1], result[2]))

    print("\n新宿区 文化財・史跡 - 推奨データセット（観光）")
    print("----------")
    pair = ItemsPair(items_shinjuku_bunkazai, items_kanko)
    for result in pair.mapping():
        print('{}\t{}\t{:.2f}'.format(
            result[0], result[1], result[2]))

    items_hospital = [
        '都道府県コード又は市区町村コード', 'NO', '都道府県名',
        '市区町村名', '名称', '名称_カナ', '医療機関の種類',
        '住所', '方書', '緯度', '経度', '電話番号', '内線番号',
        'FAX番号', '法人番号', '法人の名称', '医療機関コード',
        '診療曜日', '診療開始時間', '診療終了時間',
        '診療日時特記事項', '時間外における対応',
        '診療科目', '病床数', 'URL', '備考'
    ]

    items_towadashi = [
        '市区町村コード', 'NO', '都道府県名',
        '市区町村名', '名称', '名称_カナ', '医療機関の種類',
        '住所', '方書', '緯度', '経度', '電話番号',
        '法人番号', '法人の名称',
        '診療曜日', '診療開始時間', '診療終了時間',
        '診療日時特記事項', '時間外における対応',
        '診療科目', '病床数', 'URL', '備考'
    ]

    print("\n十和田市 医療機関一覧 - 推奨データセット（医療機関）")
    print("----------")
    pair = ItemsPair(items_towadashi, items_hospital)
    for result in pair.mapping():
        print('{}\t{}\t{:.2f}'.format(
            result[0], result[1], result[2]))

    items_sakaishi = [
        '都道府県コード', 'NO', '都道府県名',
        '市名', '名称', '名称_カナ', '医療機関の種類',
        '住所', '方書', '緯度', '経度', '電話番号', '内線番号',
        'FAX番号', '法人番号', '法人の名称', '医療機関コード',
        '診療曜日', '診療開始時間', '診療終了時間',
        '備考', '郵便番号', '区名',
        '救急協力診療科', '救急協力診療科',
        '救急協力診療科', '救急協力診療科',
        '救急協力診療科', '救急協力診療科',
        '救急協力診療科'
    ]

    print("\n堺市救急病院一覧 - 推奨データセット（医療機関）")
    print("----------")
    pair = ItemsPair(items_sakaishi, items_hospital)
    for result in pair.mapping():
        print('{}\t{}\t{:.2f}'.format(
            result[0], result[1], result[2]))
