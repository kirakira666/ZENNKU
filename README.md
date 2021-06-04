# 数据集及代码文件含义

**examples/ngram.txt**

​	ngram数据集，包括ngram和对应频数（取k6-k12中频数最高的5%）见：https://6865-hello-cloudbase-0g101nj6c726535b-1305329525.tcb.qcloud.la/ngram.txt?sign=b2be62dc937f081e551455d55b166a13&t=1622794187

**examples/ngram_k***

​	原始ngram及其频数，k代表ngram长度，共有k6-k12

**examples/change_ngram_form.py**

​	生成ngram.txt和随机小语料库c.txt（测试用）的脚本

**examples/create_pre_train_data.py**

​	生成预训练的数据集

**ZEN/tokenization.py**

​	被create_pre_train_data.py调用处理数据

**examples/run_pre_train.py**

​	预训练，读入create_pre_train_data.py生成的数据生成预训练模型

# 命令

在examples目录下：

```python
python create_pre_train_data.py --train_corpus c.txt --output_dir result --bert_model bert-base-cased --max_ngram_in_sequence 200
```

​	 其中c.txt为语料库地址，output_dir输出目录

```python
CUDA_VISIBLE_DEVICES=2,5 python run_pre_train.py --pregenerated_data result --output_dir fin --bert_model bert-base-cased
```

​	其中CUDA_VISIBLE_DEVICES指定gpu号，pregenerated_data为上一步输出目录，output_dir为模型输出目录