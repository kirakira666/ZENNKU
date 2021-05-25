# import pymysql
# db=pymysql.connect("localhost","TestUser","lyt457619283","testschema")
# cursor=db.cursor()
# cursor.execute("SELECT VERSION()")
# data =cursor.fetchone()
# print("kira:%s"%data)
# db.close()
import random
k6_file =open("./k6.txt",'r')
ngram_file =open("./ngram.txt",'w')
c_file =open("./c.txt",'w')
l = ['A','C','G','T']
resDict = {}
# 处理数据格式
key=[]
value=[]
with open("./k6.txt", "r", encoding="utf-8") as fin:
    for i, line in enumerate(fin):
        # print(i)
        # print(line)
        line = line.rstrip()
        print(line)
        ngram, freq = line.split(" ")
        key.append(ngram)
        value.append(int(freq))
print(key)
print(value)
sortDict = sorted(zip(value, key), reverse=True)
for item in sortDict:
    print(item[0])
    ngram_file.write(item[1] + ' ' + str(item[0]) + '\n')
print(sortDict)

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