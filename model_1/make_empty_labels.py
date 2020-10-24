import os

preexisting_labels = set(os.listdir("labels"))

for file in os.listdir("images"):
    file = file[:file.index(".")]
    if file + ".txt" not in preexisting_labels:
        label_file = open("labels/" + file + ".txt", "w")
        label_file.write("\n")
        label_file.close()