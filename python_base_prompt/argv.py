# *args的用法

def test_var_args(first_arg, *argv):
    print('the first arg is:', first_arg)
    for arg in argv:
        print('the next arg is:', arg)

test_var_args('amy', 'bob', 'python', 'C', 'go', 'php')