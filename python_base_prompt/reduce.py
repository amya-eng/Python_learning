# 用reduce 实现阶乘
from functools import reduce
product = reduce( (lambda x, y: x * y), [1, 2, 3, 4] )
print(product)

# 元组三元条件表达式
print((1/0, 2)[True])
# 尽量不要这样写，因为元组首先是把数据先计算出来，然后根据索引去引用。

# 从函数中返回函数

