from functools import wraps

def a_new_decorator(a_func):
    @wraps(a_func)            # 保存调用函数的信息
    def wrapTheFunction():
        print("I am doing some boring work before executing a_func()")

        a_func()

        print("I am doing some boring work after executing a_func()")

    return wrapTheFunction


@a_new_decorator
def a_function_requiring_decoration():
    """Hey you! Decorate me!"""
    print("I am the function which needs some decoration to "
          "remove my foul smell")


a_function_requiring_decoration()
# outputs: I am doing some boring work before executing a_func()
#         I am the function which needs some decoration to remove my foul smell
#         I am doing some boring work after executing a_func()

# # the @a_new_decorator is just a short way of saying:
# a_function_requiring_decoration = a_new_decorator(a_function_requiring_decoration)

print(a_function_requiring_decoration.__name__)