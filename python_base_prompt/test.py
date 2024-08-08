def test_var_args(*argv):
    # print("first normal arg:", f_arg)
    for arg in argv:
        print("another arg through *argv:", arg)


test_var_args('python', 'eggs', 'test')
