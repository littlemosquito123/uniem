import csv
import logging
import os
import sys
from collections import defaultdict
from itertools import islice
from typing import Generator, Iterable, TypeVar, cast

from mteb.abstasks import AbsTaskClassification, AbsTaskReranking, AbsTaskRetrieval
from tqdm import tqdm

from datasets import Dataset, DatasetDict, load_dataset

os.environ['TOKENIZERS_PARALLELISM'] = 'false'
logging.basicConfig(level=logging.INFO)
T = TypeVar('T')
DEFAULT_T2_REL_THRESHOLD = 2
csv.field_size_limit(sys.maxsize)


def generate_batch(data: Iterable[T], batch_size: int = 32) -> Generator[list[T], None, None]:
    iterator = iter(data)
    while batch := list(islice(iterator, batch_size)):
        yield batch


def load_t2ranking_for_reranking(rel_threshold: int | None = None):
    rel_threshold = rel_threshold or DEFAULT_T2_REL_THRESHOLD
    assert rel_threshold >= 1

    collection_dataset = load_dataset('THUIR/T2Ranking', 'collection')['train']  # type: ignore
    dev_queries_dataset = load_dataset('THUIR/T2Ranking', 'queries.dev')['train']  # type: ignore
    dev_rels_dataset = load_dataset('THUIR/T2Ranking', 'qrels.dev')['train']  # type: ignore
    dev_rels_dataset = cast(Iterable[dict], dev_rels_dataset)
    records = defaultdict(lambda: [[], []])
    query_map = {record['qid']: record['text'] for record in dev_queries_dataset}  # type: ignore

    for rel_record in tqdm(dev_rels_dataset):
        rel_record = cast(dict, rel_record)
        qid = rel_record['qid']
        pid = rel_record['pid']
        rel_score = rel_record['rel']
        query_text = query_map[qid]
        passage_record = collection_dataset[pid]
        assert passage_record['pid'] == pid
        if rel_score >= rel_threshold:
            records[query_text][0].append(passage_record['text'])
        else:
            records[query_text][1].append(passage_record['text'])

    data = [{'query': k, 'positive': v[0], 'negative': v[1]} for k, v in records.items()]
    dataset = Dataset.from_list(data)
    dataset_dict = DatasetDict(dev=dataset)
    return dataset_dict


class T2RReranking(AbsTaskReranking):
    @property
    def description(self):
        return {
            'name': 'T2Reranking',
            'reference': 'https://huggingface.co/datasets/THUIR/T2Ranking',
            'type': 'Reranking',
            'category': 's2s',
            'eval_splits': ['dev'],
            'eval_langs': ['zh'],
            'main_score': 'map',
        }

    def load_data(self, **kwargs):
        dataset = load_t2ranking_for_reranking()
        self.dataset = dataset
        self.data_loaded = True


class TNews(AbsTaskClassification):
    @property
    def description(self):
        return {
            'name': 'TNews',
            'hf_hub_name': 'clue',
            'description': 'clue tnews dataset',
            'category': 's2s',
            'type': 'Classification',
            'eval_splits': ['validation'],
            'eval_langs': ['zh'],
            'main_score': 'accuracy',
            'samples_per_label': 32,
            'n_experiments': 5,
        }

    def load_data(self, **kwargs):
        dataset = load_dataset('clue', 'tnews')
        dataset = dataset.rename_column('sentence', 'text')
        self.dataset = dataset
        self.data_loaded = True


class TYQSentiment(AbsTaskClassification):
    @property
    def description(self):
        return {
            'name': 'TYQSentiment',
            'hf_hub_name': 'tyqiangz/multilingual-sentiments',
            'description': 'multilingual sentiments datasets grouped into 3 classes -- positive, neutral, negative.',
            'category': 's2s',
            'type': 'Classification',
            'eval_splits': ['validation'],
            'eval_langs': ['zh'],
            'main_score': 'accuracy',
            'samples_per_label': 32,
        }

    def load_data(self, **kwargs):
        dataset = load_dataset('tyqiangz/multilingual-sentiments', 'chinese')
        self.dataset = dataset
        self.data_loaded = True


class IFlyTek(AbsTaskClassification):
    @property
    def description(self):
        return {
            'name': 'IFlyTek',
            'hf_hub_name': 'clue',
            'description': 'clue iflytek',
            'category': 's2s',
            'type': 'Classification',
            'eval_splits': ['validation'],
            'eval_langs': ['zh'],
            'main_score': 'accuracy',
            'samples_per_label': 32,
            'n_experiments': 3,
        }

    def load_data(self, **kwargs):
        dataset = load_dataset('clue', 'iflytek')
        dataset = dataset.rename_column('sentence', 'text')
        self.dataset = dataset
        self.data_loaded = True


class JDIphone(AbsTaskClassification):
    @property
    def description(self):
        return {
            'name': 'JDIphone',
            'hf_hub_name': 'kuroneko5943/jd21',
            'description': 'kuroneko5943/jd21 iphone',
            'category': 's2s',
            'type': 'Classification',
            'eval_splits': ['validation'],
            'eval_langs': ['zh'],
            'main_score': 'accuracy',
            'samples_per_label': 32,
        }

    def load_data(self, **kwargs):
        dataset = load_dataset('kuroneko5943/jd21', 'iPhone')
        dataset = dataset.rename_column('sentence', 'text')
        self.dataset = dataset
        self.data_loaded = True


class StockComSentiment(AbsTaskClassification):
    @property
    def description(self):
        return {
            'name': 'StockComSentiment',
            'hf_hub_name': 'kuroneko5943/stock11',
            'description': 'kuroneko5943/stock11 communication',
            'category': 's2s',
            'type': 'Classification',
            'eval_splits': ['validation'],
            'eval_langs': ['zh'],
            'main_score': 'accuracy',
            'samples_per_label': 32,
        }

    def load_data(self, **kwargs):
        dataset = load_dataset('kuroneko5943/stock11', 'communication')
        dataset = dataset.rename_column('sentence', 'text')
        self.dataset = dataset
        self.data_loaded = True


class GubaEastmony(AbsTaskClassification):
    @property
    def description(self):
        return {
            'name': 'GubaEastmony',
            'hf_hub_name': 'Fearao/guba_eastmoney',
            'description': '数据来自东方财富股吧的评论，经过人工label',
            'category': 's2s',
            'type': 'Classification',
            'eval_splits': ['test'],
            'eval_langs': ['zh'],
            'main_score': 'accuracy',
            'samples_per_label': 32,
        }

    def load_data(self, **kwargs):
        dataset = load_dataset('Fearao/guba_eastmoney')
        self.dataset = dataset
        self.data_loaded = True


def load_t2ranking_for_retraviel():
    collection_dataset = load_dataset('THUIR/T2Ranking', 'collection')['train']  # type: ignore
    dev_queries_dataset = load_dataset('THUIR/T2Ranking', 'queries.dev')['train']  # type: ignore
    dev_rels_dataset = load_dataset('THUIR/T2Ranking', 'qrels.dev')['train']  # type: ignore
    corpus = {}
    for record in collection_dataset:
        corpus[str(record['pid'])] = {'text': record['text']}   # type: ignore
    queries = {}
    for record in dev_queries_dataset:
        queries[str(record['qid'])] = record['text']  # type: ignore
    qrels = {}
    for record in dev_rels_dataset:
        qrels[str(record['qid'])] = {str(record['pid']): record['rel']}  # type: ignore
    return corpus, queries, qrels


class T2RRetrieval(AbsTaskRetrieval):
    @property
    def description(self):
        return {
            'name': 'T2RankingRetrieval',
            'reference': 'https://huggingface.co/datasets/THUIR/T2Ranking',
            'type': 'Retrieval',
            'category': 's2p',
            'eval_splits': ['dev'],
            'eval_langs': ['zh'],
            'main_score': 'ndcg_at_10',
        }

    def load_data(self, **kwargs):
        corpus, queries, qrels = load_t2ranking_for_retraviel()
        self.corpus, self.queries, self.relevant_docs = {}, {}, {}
        self.corpus['dev'] = corpus
        self.queries['dev'] = queries
        self.relevant_docs['dev'] = qrels
        self.data_loaded = True