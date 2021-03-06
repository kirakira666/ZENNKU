# encoding="utf-8"
# Copyright 2019 Sinovation Ventures AI Institute
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Create data for pretrain."""

import sys
sys.path.append("..")

from argparse import ArgumentParser
from pathlib import Path
from tqdm import tqdm, trange
from tempfile import TemporaryDirectory
import shelve

from random import random, randrange, randint, shuffle, choice
from ZEN import BertTokenizer, ZenNgramDict
import numpy as np
import json
import collections


class DocumentDatabase():
    '''
    对于一篇文章：
    但是尽管马克思本人批判黑格尔的观念论，但其思想却深受黑格尔的特别是辨证论的影响。

    西方马克思主义：
    此外，比上述类型更为复杂的版本有[[路易·皮埃尔·阿尔都塞|阿尔都塞]]等人做出详尽阐述。

    之后，新马克思主义的哲学理论受到[[西格蒙德·弗洛伊德|弗洛伊德]]、存在主义、康德、[[社会科学]]以及黑格尔等思想的革新，已形成不同的发展方向。

    革新的黑格尔主义：
    20世纪开始，黑格尔主义的社会性方面在[[威廉·狄尔泰|狄尔泰]]和一些德国学者重新发展。

    一个document是一个段落（以一个空行来间隔不同的段落），document中每个元素是一个句子
    doc1=[ ['但', '是',...] ]
    doc2=[ ['西','方',...], ['此','外',...] ]
    doc3=[['之','后',...]]
    doc4=[ ['革','新',...], ['20','世',...] ]

    docs=[doc1, doc2, doc3, doc4]
    doc_lengths=[1, 2, 1, 2] , 每个元素表示相应的document中有几个句子
    '''
    def __init__(self, reduce_memory=False):
        if reduce_memory:  # 当数据量较大时，为减少内存将数据写入硬盘（文件）中
            self.temp_dir = TemporaryDirectory()  # 创建一个临时目录temp_dir
            self.working_dir = Path(self.temp_dir.name)  # 用临时目录temp_dir创建一个Path对象working_dir
            self.document_shelf_filepath = self.working_dir / 'shelf.db'  # 创建working_dir的子目录document_shelf_filepath
            self.document_shelf = shelve.open(str(self.document_shelf_filepath),
                                              flag='n', protocol=-1)
            # 创建一个shelf对象document_shelf，document_shelf_filepath为对象将写入的文件路径，
            # flag为n表示，每次调用open()都重新创建一个空的文件，可读写
            # shelf对象用来存放document
            self.documents = None
        else:  # 数据量较小时，直接写入内存
            self.documents = []  # 用来存放document
            self.document_shelf = None
            self.document_shelf_filepath = None
            self.temp_dir = None
        self.doc_lengths = []  # 数组中每个元素对应于一个document的长度，数组元素个数就是document的个数
        self.doc_cumsum = None
        self.cumsum_max = None
        self.reduce_memory = reduce_memory

    def add_document(self, document):
        if not document:
            return
        # 如果reduce_document是true，将document加到document_shelf中
        if self.reduce_memory:
            current_idx = len(self.doc_lengths)
            self.document_shelf[str(current_idx)] = document
        # 如果reduce_document是false，将document加到documents中
        else:
            self.documents.append(document)
        self.doc_lengths.append(len(document))

    def _precalculate_doc_weights(self):
        self.doc_cumsum = np.cumsum(self.doc_lengths)
        self.cumsum_max = self.doc_cumsum[-1]

    # 随机选出一个document，选出的document序号不能是current_idx，即不能和当前的document重复
    def sample_doc(self, current_idx, sentence_weighted=True):
        # Uses the current iteration counter to ensure we don't sample the same doc twice
        if sentence_weighted:
            # With sentence weighting, we sample docs proportionally to their sentence length
            if self.doc_cumsum is None or len(self.doc_cumsum) != len(self.doc_lengths):
                self._precalculate_doc_weights()
            rand_start = self.doc_cumsum[current_idx]  # 假设current_idx是5，rand_start表示第5个段落的最后一个句子在整篇文章中的index
            rand_end = rand_start + self.cumsum_max - self.doc_lengths[current_idx]
            sentence_index = randrange(rand_start, rand_end) % self.cumsum_max  # 随机得到一个句子
            sampled_doc_index = np.searchsorted(self.doc_cumsum, sentence_index, side='right')  # 随机得到的句子在第几个doc中
        else:
            # If we don't use sentence weighting, then every doc has an equal chance to be chosen
            sampled_doc_index = (current_idx + randrange(1, len(self.doc_lengths))) % len(self.doc_lengths)
        assert sampled_doc_index != current_idx
        if self.reduce_memory:
            return self.document_shelf[str(sampled_doc_index)]
        else:
            return self.documents[sampled_doc_index]

    def __len__(self):
        return len(self.doc_lengths)

    def __getitem__(self, item):
        if self.reduce_memory:
            return self.document_shelf[str(item)]
        else:
            return self.documents[item]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        if self.document_shelf is not None:
            self.document_shelf.close()
        if self.temp_dir is not None:
            self.temp_dir.cleanup()


def truncate_seq_pair(tokens_a, tokens_b, max_num_tokens):
    """Truncates a pair of sequences to a maximum sequence length. Lifted from Google's BERT repo."""
    while True:
        total_length = len(tokens_a) + len(tokens_b)
        if total_length <= max_num_tokens:
            break

        # 将tokens_a和tokens_b中包含句子数多的作为trunc_tokens
        trunc_tokens = tokens_a if len(tokens_a) > len(tokens_b) else tokens_b
        assert len(trunc_tokens) >= 1

        # We want to sometimes truncate from the front and sometimes from the
        # back to add more randomness and avoid biases.
        if random() < 0.5:
            del trunc_tokens[0]
        else:
            trunc_tokens.pop()


MaskedLmInstance = collections.namedtuple("MaskedLmInstance",
                                          ["index", "label"])


def create_masked_lm_predictions(tokens, masked_lm_prob, max_predictions_per_seq, whole_word_mask, vocab_list):
    """Creates the predictions for the masked LM objective. This is mostly copied from the Google BERT repo, but
    with several refactors to clean it up and remove a lot of unnecessary variables."""
    cand_indices = []
    # 如果tokens = ["[CLS]", "This", "is", "[SEP]", "un", "##aff", "##able", "[SEP]"]
    # cand_indices = [[1], [2], [4, 5, 6]]

    for (i, token) in enumerate(tokens):
        if token == "[CLS]" or token == "[SEP]":
            continue
        # Whole Word Masking means that if we mask all of the wordpieces
        # corresponding to an original word. When a word has been split into
        # WordPieces, the first token does not have any marker and any subsequence
        # tokens are prefixed with ##. So whenever we see the ## token, we
        # append it to the previous set of word indexes.
        #
        # Note that Whole Word Masking does *not* change the training code
        # at all -- we still predict each WordPiece independently, softmaxed
        # over the entire vocabulary.
        if (whole_word_mask and len(cand_indices) >= 1 and token.startswith("##")):
            cand_indices[-1].append(i)
        else:
            cand_indices.append([i])

    num_to_mask = min(max_predictions_per_seq,
                      max(1, int(round(len(tokens) * masked_lm_prob))))  # 要进行mask的token数目
    shuffle(cand_indices)  # 对列表中的元素进行随机排序，因为是随机mask一些tokens
    masked_lms = []
    covered_indexes = set()
    for index_set in cand_indices:
        if len(masked_lms) >= num_to_mask:
            break
        # If adding a whole-word mask would exceed the maximum number of
        # predictions, then just skip this candidate.
        # 如果mask当前的whole word会使得被mask掉的tokens数目超过num_to_mask
        # 则跳过当前的whole word
        if len(masked_lms) + len(index_set) > num_to_mask:
            continue

        # 判断当前的whole word的index_set中是否有在covered_indexes中的
        # 如果有则跳过当前的whole word
        is_any_index_covered = False
        for index in index_set:
            if index in covered_indexes:
                is_any_index_covered = True
                break
        if is_any_index_covered:
            continue

        # 如果没有，则把index_set中的每一个index加到covered_indexes中
        for index in index_set:
            covered_indexes.add(index)

            masked_token = None
            # 80% of the time, replace with [MASK]
            # 80%的概率会把当前的token用[MASK]代替
            if random() < 0.8:
                masked_token = "[MASK]"
            else:
                # 10% of the time, keep original
                # 10%的概率，当前的token不变
                if random() < 0.5:
                    masked_token = tokens[index]
                # 10% of the time, replace with random word
                # 10%的概率会用一个随机的word来代替当前的token
                else:
                    masked_token = choice(['a','c','t','g'])
            # 将当前的token以(index, token)的形式加入到masked_lms中
            # 为什么没有替换成[MASK]的token也会加入？
            masked_lms.append(MaskedLmInstance(index=index, label=tokens[index]))
            tokens[index] = masked_token

    assert len(masked_lms) <= num_to_mask
    masked_lms = sorted(masked_lms, key=lambda x: x.index)  # 将masked_lms中的token按照index排序
    mask_indices = [p.index for p in masked_lms]
    masked_token_labels = [p.label for p in masked_lms]

    # 返回已经被随机屏蔽了部分token的tokens序列，index序列和相应的原token序列
    return tokens, mask_indices, masked_token_labels


# 把一个段落中的句子分为上下句
# 将分好段的句子随机mask掉一部分token
# 挑出句子中的ngram
# 记录以上所有信息，作为一个实例
# 一个seq代表的是一个实例的seq
def create_instances_from_document(
        doc_database, doc_idx, max_seq_length,max_ngram_in_seq, short_seq_prob,
        masked_lm_prob, max_predictions_per_seq, whole_word_mask, vocab_list, ngram_dict):
    """This code is mostly a duplicate of the equivalent function from Google BERT's repo.
    However, we make some changes and improvements. Sampling is improved and no longer requires a loop in this function.
    Also, documents are sampled proportionally to the number of sentences they contain, which means each sentence
    (rather than each document) has an equal chance of being sampled as a false example for the NextSentence task."""
    document = doc_database[doc_idx]
    # Account for [CLS], [SEP], [SEP]
    max_num_tokens = max_seq_length - 3

    # We *usually* want to fill up the entire sequence since we are padding
    # to `max_seq_length` anyways, so short sequences are generally wasted
    # computation. However, we *sometimes*
    # (i.e., short_seq_prob == 0.1 == 10% of the time) want to use shorter
    # sequences to minimize the mismatch between pre-training and fine-tuning.
    # The `target_seq_length` is just a rough target however, whereas
    # `max_seq_length` is a hard limit.
    target_seq_length = max_num_tokens
    if random() < short_seq_prob:
        target_seq_length = randint(2, max_num_tokens)  # 随机生成一个2到max_num_tokens之间的数

    # We DON'T just concatenate all of the tokens from a document into a long
    # sequence and choose an arbitrary split point because this would make the
    # next sentence prediction task too easy. Instead, we split the input into
    # segments "A" and "B" based on the actual "sentences" provided by the user
    # input.
    instances = []
    current_chunk = []  # 存放句子
    current_length = 0  # current_chunk中tokens的数量
    i = 0
    while i < len(document):
        segment = document[i]  # 段落中的一个句子
        current_chunk.append(segment)
        current_length += len(segment)
        # 如果已经遍历到了最后一个句子，或者tokens的数量达到了target_seq_length
        # 当tokens的数量达到了target_seq_length，不会退出循环，而是清空current_chunk，current_length也清零
        # 将剩下的句子放到下一个实例中，因此一个段落可能会被分成多个实例，存放到instances中
        if i == len(document) - 1 or current_length >= target_seq_length:
            if current_chunk:
                # `a_end` is how many segments from `current_chunk` go into the `A`
                # (first) sentence.
                a_end = 1
                if len(current_chunk) >= 2:  # 如果当前句子个数大于等于2的话
                    a_end = randrange(1, len(current_chunk))  # 返回1到当前句子个数之间的一个随机数

                # tokens_a中存放了current_chunk的前a_end个句子中的tokens，作为next sentence任务的上句
                tokens_a = []
                for j in range(a_end):
                    tokens_a.extend(current_chunk[j])

                # tokens_b中存放了next sentence任务的下句
                tokens_b = []

                # 从另一个随机的document中选出随机的句子，将这些tokens加入tokens_b中
                # Random next
                if len(current_chunk) == 1 or random() < 0.5:
                    is_random_next = True
                    target_b_length = target_seq_length - len(tokens_a)

                    # Sample a random document, with longer docs being sampled more frequently
                    # 随机选出一个document，含有句子数量多的document被选中的几率更大
                    random_document = doc_database.sample_doc(current_idx=doc_idx, sentence_weighted=True)

                    random_start = randrange(0, len(random_document))
                    for j in range(random_start, len(random_document)):
                        tokens_b.extend(random_document[j])
                        if len(tokens_b) >= target_b_length:
                            break
                    # We didn't actually use these segments so we "put them back" so
                    # they don't go to waste.
                    num_unused_segments = len(current_chunk) - a_end
                    i -= num_unused_segments

                # 将current_chunk的剩下的句子加入到tokens_b中（真实的下句）
                # Actual next
                else:
                    is_random_next = False
                    for j in range(a_end, len(current_chunk)):
                        tokens_b.extend(current_chunk[j])
                truncate_seq_pair(tokens_a, tokens_b, max_num_tokens)  # 将tokens_a和tokens_b截取，使得它们的总长度等于max_num_tokens

                tokens = ["[CLS]"] + tokens_a + ["[SEP]"] + tokens_b + ["[SEP]"]
                # The segment IDs are 0 for the [CLS] token, the A tokens and the first [SEP]
                # They are 1 for the B tokens and the final [SEP]
                segment_ids = [0 for _ in range(len(tokens_a) + 2)] + [1 for _ in range(len(tokens_b) + 1)]

                # tokens: 随机屏蔽了num_to_mask个token后得到的tokens序列，这些tokens中有的被用[MASK]代替，有的保持原样，有的被替换成随机的word
                # masked_lm_positions：这些tokens在原来的（未进行mask之前的）tokens序列中对应的index
                # masked_lm_labels：这些tokens的原本对应的token（都未进行替换）
                tokens, masked_lm_positions, masked_lm_labels = create_masked_lm_predictions(
                    tokens, masked_lm_prob, max_predictions_per_seq, whole_word_mask, vocab_list)

                ngram_matches = []
                #  Filter the ngram segment from 2 to 7 to check whether there is a ngram
                # 挑出当前句子中所有长度在2-7之间的ngram，把它的相关信息加入到ngram_matches中
                for p in range(2, 8):
                    for q in range(0, len(tokens) - p + 1):
                        character_segment = tokens[q:q+p]
                        # q is the starting position of the ngram
                        # p is the length of the current ngram
                        character_segment = tuple(character_segment)
                        if character_segment in ngram_dict.ngram_to_id_dict:
                            ngram_index = ngram_dict.ngram_to_id_dict[character_segment]
                            ngram_matches.append([ngram_index, q, p, character_segment])
                            # ngram_index：ngram在整个ngram_dict中的index
                            # q：ngram在句子中的起始位置
                            # p: ngram的长度
                            # character_segment：ngram中的所有token（元组形式）
                shuffle(ngram_matches)  # 将ngram_matches中的元素随机排序
                if len(ngram_matches) > max_ngram_in_seq:
                    ngram_matches = ngram_matches[:max_ngram_in_seq]
                ngram_ids = [ngram[0] for ngram in ngram_matches]  # 每个ngram在整个ngram_dict中的index
                ngram_positions = [ngram[1] for ngram in ngram_matches]  # 每个ngram在句子中的起始位置
                ngram_lengths = [ngram[2] for ngram in ngram_matches]  # 每个ngram的长度
                ngram_tuples = [ngram[3] for ngram in ngram_matches]  # 每个ngram中的所有token（元组形式）
                # ngram的起始位置如果在上半句则ngram_seg_id为0，否则为1
                ngram_seg_ids = [0 if position < (len(tokens_a) + 2) else 1 for position in ngram_positions]
                instance = {
                    "tokens": tokens,
                    "segment_ids": segment_ids,
                    "is_random_next": is_random_next,
                    "masked_lm_positions": masked_lm_positions,
                    "masked_lm_labels": masked_lm_labels,
                    "ngram_ids": ngram_ids,
                    "ngram_positions": ngram_positions,
                    "ngram_lengths": ngram_lengths,
                    "ngram_tuples": ngram_tuples,
                    "ngram_segment_ids": ngram_seg_ids
                }
                instances.append(instance)
            current_chunk = []
            current_length = 0
        i += 1

    return instances

def main():
    parser = ArgumentParser()
    parser.add_argument('--train_corpus', type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    parser.add_argument("--bert_model", type=str, required=True,
                        help="Bert pre-trained model selected in the list: bert-base-uncased, "
                             "bert-large-uncased, bert-base-cased, bert-base-multilingual, bert-base-chinese.")
    parser.add_argument("--do_lower_case", action="store_true")
    parser.add_argument("--do_whole_word_mask", action="store_true",
                        help="Whether to use whole word masking rather than per-WordPiece masking.")
    parser.add_argument("--reduce_memory", action="store_true",
                        help="Reduce memory usage for large datasets by keeping data on disc rather than in memory")

    parser.add_argument("--epochs_to_generate", type=int, default=3,
                        help="Number of epochs of data to pregenerate")
    parser.add_argument("--max_seq_len", type=int, default=128)
    parser.add_argument("--short_seq_prob", type=float, default=0.1,
                        help="Probability of making a short sentence as a training example")
    parser.add_argument("--masked_lm_prob", type=float, default=0.15,
                        help="Probability of masking each token for the LM task")
    parser.add_argument("--max_predictions_per_seq", type=int, default=20,
                        help="Maximum number of tokens to mask in each sequence")
    parser.add_argument("--ngram_list", type=str, default="/data/zhwiki/ngram.txt")
    parser.add_argument("--max_ngram_in_sequence", type=int, default=20)

    args = parser.parse_args()

    tokenizer = BertTokenizer.from_pretrained(args.bert_model, do_lower_case=args.do_lower_case)  # 一个分词器
    vocab_list = list(tokenizer.vocab.keys())  # 列表中每个元素都是一个分词器分好的token
    ngram_dict = ZenNgramDict("./ngram.txt", tokenizer=tokenizer)  # 参数为什么是bert_model？

    with DocumentDatabase(reduce_memory=args.reduce_memory) as docs:
        with args.train_corpus.open(encoding='utf-8') as f:
            doc = []
            for line in tqdm(f, desc="Loading Dataset", unit=" lines"):
                line = line.strip()
                if line == "":
                    docs.add_document(doc)
                    doc = []
                else:
                    tokens = tokenizer.tokenize(line)
                    doc.append(tokens)
            if doc:
                docs.add_document(doc)  # If the last doc didn't end on a newline, make sure it still gets added
        if len(docs) <= 1:
            exit("ERROR: No document breaks were found in the input file! These are necessary to allow the script to "
                 "ensure that random NextSentences are not sampled from the same document. Please add blank lines to "
                 "indicate breaks between documents in your input file. If your dataset does not contain multiple "
                 "documents, blank lines can be inserted at any natural boundary, such as the ends of chapters, "
                 "sections or paragraphs.")

        args.output_dir.mkdir(exist_ok=True)
        # 因为create_instances_from_document方法中具有随机性，每个epoch会产生不同的训练实例，用于多次训练
        for epoch in trange(args.epochs_to_generate, desc="Epoch"):  # trange用法同range，只是输出的时候会打印进度条
            epoch_filename = args.output_dir / f"epoch_{epoch}.json"  # 以f开头表示在字符串内支持大括号内的python表达式
            num_instances = 0
            with epoch_filename.open('w') as epoch_file:
                for doc_idx in trange(len(docs), desc="Document"):  # 遍历docs中的每一个document
                    doc_instances = create_instances_from_document(
                        docs, doc_idx, max_seq_length=args.max_seq_len, max_ngram_in_seq=args.max_ngram_in_sequence,
                        short_seq_prob=args.short_seq_prob,
                        masked_lm_prob=args.masked_lm_prob, max_predictions_per_seq=args.max_predictions_per_seq,
                        whole_word_mask=args.do_whole_word_mask, vocab_list=vocab_list, ngram_dict=ngram_dict)
                    doc_instances = [json.dumps(instance) for instance in doc_instances]  # json.dumps将字典转成字符串
                    # 把每一个instance信息字符串作为一行写入epoch_file
                    for instance in doc_instances:
                        epoch_file.write(instance + '\n')
                        num_instances += 1
            metrics_file = args.output_dir / f"epoch_{epoch}_metrics.json"
            with metrics_file.open('w') as metrics_file:
                metrics = {
                    "num_training_examples": num_instances,  # 实例数目
                    "max_seq_len": args.max_seq_len,  # 一个实例中最多有多少token
                    "max_ngram_in_sequence": args.max_ngram_in_sequence  # 一个实例中最多有多少个ngram
                }
                metrics_file.write(json.dumps(metrics))


if __name__ == '__main__':
    main()
