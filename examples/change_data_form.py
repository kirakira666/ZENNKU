
import random
# k6_file =open("./bin/k6.txt", 'r')
# k7_file =open("./bin/k7.txt", 'r')
# k8_file =open("./bin/k8.txt", 'r')
# k9_file =open("./bin/k9.txt", 'r')
# k10_file =open("./bin/k10.txt", 'r')
# k11_file =open("./bin/k11.txt", 'r')
# k12_file =open("./bin/k12.txt", 'r')
ngram_file =open("./ngram.txt",'w')
c_file =open("./c.txt",'w')
l = ['A','C','G','T']
resDict = {}
# 处理数据格式
key=[]
value=[]
with open("./ngram_k/k6.txt", "r", encoding="utf-8") as fin:
    for i, line in enumerate(fin):
        # print(i)
        # print(line)
        line = line.rstrip()
        # print(line)
        ngram, freq = line.split(" ")
        key.append(ngram)
        value.append(int(freq))

with open("./ngram_k/k7.txt", "r", encoding="utf-8") as fin:
    for i, line in enumerate(fin):
        # print(i)
        # print(line)
        line = line.rstrip()
        # print(line)
        ngram, freq = line.split(" ")
        key.append(ngram)
        value.append(int(freq))

with open("./ngram_k/k8.txt", "r", encoding="utf-8") as fin:
    for i, line in enumerate(fin):
        # print(i)
        # print(line)
        line = line.rstrip()
        # print(line)
        ngram, freq = line.split(" ")
        key.append(ngram)
        value.append(int(freq))

with open("./ngram_k/k9.txt", "r", encoding="utf-8") as fin:
    for i, line in enumerate(fin):
        # print(i)
        # print(line)
        line = line.rstrip()
        # print(line)
        ngram, freq = line.split(" ")
        key.append(ngram)
        value.append(int(freq))

with open("./ngram_k/k10.txt", "r", encoding="utf-8") as fin:
    for i, line in enumerate(fin):
        # print(i)
        # print(line)
        line = line.rstrip()
        # print(line)
        ngram, freq = line.split(" ")
        key.append(ngram)
        value.append(int(freq))

with open("./ngram_k/k11.txt", "r", encoding="utf-8") as fin:
    for i, line in enumerate(fin):
        # print(i)
        # print(line)
        line = line.rstrip()
        # print(line)
        ngram, freq = line.split(" ")
        key.append(ngram)
        value.append(int(freq))

with open("./ngram_k/k12.txt", "r", encoding="utf-8") as fin:
    for i, line in enumerate(fin):
        # print(i)
        # print(line)
        line = line.rstrip()
        # print(line)
        ngram, freq = line.split(" ")
        key.append(ngram)
        value.append(int(freq))


# print(key)
# print(value)
sortDict = sorted(zip(value, key), reverse=True)
length = len(sortDict)

i = 0
for item in sortDict:
    i = i+1
    # print(str(item[1]) + ' ' + str(item[0]) + '\n')
    ngram_file.write(item[1] + ' ' + str(item[0]) + '\n')
    if i > 0.05*length:
        print('select ngram：'+str(i))
        print('total ngram：' + str(length))
        break
# print(sortDict)

# 生成随机语料库
for i in range(1000):
    intdex = random.randint(0, 3)
    Ichar = ''
    if i%100 == 99:
        Ichar = '\n'+'\n'
    c_file.write(l[intdex] + Ichar)
#生成随机ngram
# for a in l:
#     for b in l:
#         for c in l:
#             for d in l:
#                 for e in l:
#                     for f in l:
#                         str1 = a+b+c+d+e+f
#                         print(str1)
#                         resDict[str1] = random.randint(1, 30000)
#                         # p= str(random.randint(1, 30000))
#                         # epoch_file.write(str1 +','+p+'\n')
#
# sortDict = sorted(zip(resDict.values(), resDict.keys()), reverse=True)
# for item in sortDict:
#     print(item[0])
#     ngram_file.write(item[1] + ' ' + str(item[0]) + '\n')
# print(sortDict)

# with epoch_filename.open("./ngram.txt",'w') as epoch_file:
#     epoch_file.write('instance' + '\n')