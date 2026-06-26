from utils import JSONFile

moh_list = JSONFile("data/ent/moh.json").read()

print(len(moh_list))
