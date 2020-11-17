# This is for splitting big files into pieces so they're within github's file size limit.
# To unify them, just cat them together

import sys

CHUNK_SIZE = 100000000

if len(sys.argv) != 2:
    print("USAGE: ./split_model.py <model_filename>")

model_filename = sys.argv[1]
data = open(model_filename, "rb").read()

for i in range(len(data) // CHUNK_SIZE + 1):
    of = open(f"{i}.part", "wb")
    of.write(data[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE])
