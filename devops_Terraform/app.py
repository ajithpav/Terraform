# import threading

# def print_number():
#     for i in range (4):
#         print(i)
# t1=threading.Thread(target=print_number)
# t1.start()
# t1.join()

import sys

x = [1, 2, 3, 4, 5]
y = (1, 2, 3, 4, 5)

print(sys.getsizeof(x))  # Size of list
print(sys.getsizeof(y))  # Size of tuple (usually smaller)
