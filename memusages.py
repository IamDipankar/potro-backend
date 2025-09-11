import psutil

mem = psutil.virtual_memory()

print(f"Total RAM: {mem.total / (1024 ** 2):.2f} MB")
print(f"Used RAM: {mem.used / (1024 ** 2):.2f} MB")
print(f"Available RAM: {mem.available / (1024 ** 2):.2f} MB")
print(f"Memory usage: {mem.percent:.2f}%")
