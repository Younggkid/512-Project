import os
import sys
import pickle

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    else:
        pass
        # print(f"Directory '{directory}' already exists!")

def save_pickle(data, filename):
    directory = os.path.dirname(filename)
    create_directory(directory)
    with open(filename, 'wb') as file:
        pickle.dump(data, file)
        print(f"Data saved to '{filename}'")

def load_pickle(filename):
    with open(filename, 'rb') as file:
        data = pickle.load(file)
        print(f"Data loaded from '{filename}'")
        return data