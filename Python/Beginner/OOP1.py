class Student:
    def __init__(self, name, house):
        if not name:
            raise ValueError("Missing name")
        if house not in ["home","school"]:
            raise ValueError("Invalid house")
        self.name = name
        self.house = house
    
    def __str__(self):
        return f"{self.name} from {self.house}"

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        if not value:
            raise ValueError("Missing name")
        self._name = value

    @property
    def house(self):
        return self._house
    
    @house.setter
    def house(self, value):
        if value not in ["home","school"]:
            raise ValueError("Invalid house")
        self._house = value
        

def main():
    student = get_student()
    print(student)

def get_student():
    name = input("name: ")
    house = input("house: ")
    student = Student(name, house)
    try:
        return student
    except ValueError:
        return None


if __name__ == "__main__":
    student = get_student()
    print(f"{student.name} from {student.house}")
