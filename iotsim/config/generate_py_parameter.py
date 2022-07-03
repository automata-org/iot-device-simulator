#!/usr/bin/env python
from jsonschemacodegen import python as pygen
import json
import os


def generate_parameters():
    json_model_path = os.path.dirname(os.path.abspath(__file__)) + '/config_model.json'
    root = os.path.normpath(os.path.dirname(os.path.abspath(__file__)) + '/../src')
    fp = open(json_model_path)
    generator = pygen.GeneratorFromSchema(root)
    generator.Generate(json.load(fp), root=root,
                       class_name='Parameters', filename_base='generated_parameters')
    print("***** parameters.py generated in:", root)

def main():
    print("*****Generating python model class from json schema*****")
    print("\n")
    generate_parameters()
    print("\n")
    print("*************************Done***************************")

if __name__ == "__main__":
    main()
