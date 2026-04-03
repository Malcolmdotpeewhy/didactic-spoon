import py_compile
try:
    py_compile.compile('src/ui/components/draggable_list.py', doraise=True)
except Exception as e:
    print(e)
