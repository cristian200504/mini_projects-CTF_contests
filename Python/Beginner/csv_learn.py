import csv

students = []

with open("csv.csv") as file:
    reader = csv.DictReader(file)
    for row in reader:
        students.append({"name": row["name"], "home": row["home"]})

for i in sorted(students, key=lambda student: student["name"]):
    print(f"{i['name']} is from {i['home']}")
