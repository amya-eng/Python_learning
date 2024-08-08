# 回答range()遍历同时减去元素的解决方案
lis = [1,2,3,4,5]
for i in range(len(lis)):
    if i == 1:
        del lis[i]
    if i < len(lis):                  # 可以增加一个判断
        print(lis[i])


# lis = [1, 2, 3, 4, 5]
# lis = iter(lis)
# while True:
#     try:
#         print(next(lis))
#     except:
#         break