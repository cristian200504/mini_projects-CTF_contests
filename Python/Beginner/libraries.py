import random
import sys

deck = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "Jack", "Queen", "King", "Ace"] * 4
def random_deck_combination():
    for i in range(len(deck)):
        random.shuffle(deck)
        print(deck[0])
        deck.pop(0)

def coin_flip():
    flip = random.choice(["Heads", "Tails"])
    print(flip)

def main():
    coin_flip()
    random_deck_combination()
    for arg in sys.argv[1:]:
        print("hello my name is ", arg)
        
main()