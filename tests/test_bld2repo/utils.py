import json
import os


def load_test_data(filename):
    file_path = "test_data/{filename}.json".format(filename=filename)
    dirname = os.path.dirname(os.path.abspath(__file__))
    abs_file_path = os.path.join(dirname, file_path)
    with open(abs_file_path, "r") as fp:
        data = json.load(fp)

    return data
