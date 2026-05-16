name = input("Whats your name?").strip().title()
print("hello , \"friend\"")
print(f"hello ,{name}")

first , second , last = name.split(" ")

print(f"first name: {first}\n second name: {second} \nlast name: {last}")