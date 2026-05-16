name = {}

with open("name.csv") as file:
    for line in file:
        name[line.split(",")[0].strip().title()] = line.split(",")[1].strip().title()

for i in sorted(name,key = lambda x: name[x]):
    print(f"Hello {i} , your favourite colour is {name[i]}!")

name2=[]

with open("name.csv") as file:
    for line in file:
        x , y = line.rstrip().split(",")
        name2.append(f"{x.strip().title()} likes {y.strip().title()}!")

for i in sorted(name2):
    print(i)