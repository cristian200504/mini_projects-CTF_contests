students = ["Harry", "Hermione", "Ron"
            ,"Draco", "Neville", "Luna"]
print("Normal for loop")
for i in range(len(students)):
    print(students[i])
print("\nEnhanced for loop")
for i in students:
    print(i)


students = {
    "Harry": "Gryffindor",
    "Hermione": "Gryffindor",
    "Ron": "Gryffindor",
    "Draco": "Slytherin",
    "Neville": "Gryffindor",
    "Luna": "Ravenclaw"
}

print("\nIterating through dictionary keys")
for student in students:
    print(student + ":", students[student])
print("\nIterating through dictionary items")
for i in range(len(students)):
    print(list(students.keys())[i] + ":", list(students.values())[i])

students = [
    {"name": "Harry", "house": "Gryffindor", "patronus": "Stag"},
    {"name": "Hermione", "house": "Gryffindor", "patronus": "Otter"},
    {"name": "Ron", "house": "Gryffindor", "patronus": "Jack Russell Terrier"},
    {"name": "Draco", "house": "Slytherin", "patronus": None},
    {"name": "Neville", "house": "Gryffindor", "patronus": None},
    {"name": "Luna", "house": "Ravenclaw", "patronus": "Hare"}
]
print("\nIterating through list of dictionaries")
for student in students:
    print(student["name"] + " is in " + student["house"] + " and their patronus is " + str(student["patronus"]))
print("\nIterating through list of dictionaries with index")
for i in range(len(students)):
    print(students[i]["name"] + " is in " + students[i]["house"] + " and their patronus is " + str(students[i]["patronus"]))