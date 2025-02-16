import random

adventurers = ["Indiana", "Lara", "Dora", "Bear Grylls", "Jack Sparrow"]
couch_potatoes = ["Homer", "Jerry", "Patrick", "Chandler", "Garfield"]

isPawanAdventurous = True if random.randint(1, 2) == 1 else False

def main_function(is_adventurous):
    buddy = adventurers.pop(adventurers.index(random.choice(adventurers))) if is_adventurous else couch_potatoes.pop(couch_potatoes.index(random.choice(couch_potatoes)))
    print(f"Pawan chooses {buddy} as a travel buddy ✈️")

    extras = adventurers if random.randint(1, 2) == 1 else couch_potatoes
    no = random.randint(1, len(extras))
    for i in range(no):
        name = random.choice(extras)
        print(f"And {name} tags along for the ride! 🚀")
        extras.remove(name)

main_function(isPawanAdventurous)
