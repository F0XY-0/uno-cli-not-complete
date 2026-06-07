import random
import collections
# ---------------- CARD ----------------
Card = collections.namedtuple('Card', ['color', 'value'])
# ---------------- DECORATOR ----------------
class Deco:
    def __init__(self, *, validate=False , count=False):
        self.validate = validate
        self.count = count
        
    def __call__(self, func):
        self.func = func 
        return self

    def __get__(self, instance, owner):
        def wrapper(*args, **kwargs):

            if self.count:
                if not hasattr(instance, "moves"):
                    instance.moves = 0
                instance.moves += 1

            if self.validate:
                index = args[0] if args else kwargs.get("index")
                top_card = args[1] if len(args) > 1 else kwargs.get("top_card")

                if index is None or top_card is None:
                    print("invalid arguments")
                    return None

                if index < 0 or index >= len(instance.hand):
                    print("invalid index")
                    return None

                card = instance.hand[index]

                if not (card.color == top_card.color or card.value == top_card.value):
                    print("invalid move")
                    return None

            return self.func(instance, *args, **kwargs)

        return wrapper
# ---------------- DECK ----------------
class UnoDeck:
    colors = ['red', 'green', 'blue', 'yellow']
    values = [str(n) for n in range(10)] + ['skip', 'reverse', 'draw2']

    def __init__(self):
        self._cards = [Card(color, value) for color in self.colors for value in self.values]

    def shuffle(self):
        random.shuffle(self._cards)

    def draw(self):
        if not self._cards:
            raise Exception("Deck is empty!")
        return self._cards.pop()

# --- ima use this until i make an actual ui --- 
class Colorize:
    COLORS = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m"
    }

    @classmethod
    def color_text(cls, card):
        color_code = cls.COLORS.get(card.color, "")
        reset = cls.COLORS["reset"]
        return f"{color_code}[{card.color} {card.value}]{reset}"    
    
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        def wrapper(*args, **kwargs):
            print(f"\n{instance.name}'s hand:")
            for i, card in enumerate(instance.hand):
                print(f"{i}: {self.color_text(card)}")
        return wrapper

# ---------------- PLAYER ----------------
class Player:
    def __init__(self, name , is_bot=False):
        self.name = name
        self.hand = []
        self.is_bot = is_bot

    @Deco(count=True)
    def draw(self, deck, count=1):
        for _ in range(count):
            self.hand.append(deck.draw())

    # be here for later 
    @Colorize
    def show_hand(self):
        pass
        #print(f"\n{self.name}'s hand:")
        #for i, card in enumerate(self.hand):
        #    print(f"{i}: {card}")

    @Deco(validate=True , count=True)
    def play(self, index, top_card):
        return self.hand.pop(index)


# ---------------- GAME LOOP ----------------
def play_uno():
    deck = UnoDeck()
    deck.shuffle()
    # im trying to make the game dynamic , help !
    players = [
        Player("You"),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True)
    ]

    current_index = 0
    direction = 1

    # deal cards
    for _ in range(5):
        for p in players:
            p.draw(deck)

    top_card = deck.draw()

    while True:
        print("\n====================")
        print("Top card:", Colorize.color_text(top_card))

        player = players[current_index]
        #player.show_hand()
        if not player.is_bot : 
            player.show_hand()
        else : 
            print(f"{player.name} has {len(player.hand)} cards")

        # ---------- BOT ----------
        if player.is_bot :
            print(f"\n{player.name} is playing...")
            played = None

            for i, card in enumerate(player.hand):
                if card.color == top_card.color or card.value == top_card.value:
                    played = player.play(i, top_card)
                    break

            if played:
                print(f"{player.name} played:", Colorize.color_text(played))
                top_card = played
            else:
                print(f"{player.name} draws")
                player.draw(deck)

        # ---------- HUMAN ----------
        else:
            choice = input("Choose index or 'd' to draw: ")

            if choice == 'd':
                player.draw(deck)
                current_index = (current_index + direction) % len(players)
                continue

            try:
                choice = int(choice)
            except:
                print("Invalid input")
                continue

            played = player.play(choice, top_card)

            if played:
                top_card = played
            else:
                continue

        # ---------- SPECIAL RULES ----------
        if top_card.value == 'skip':
            print(">> Skip!")
            skipped_index = (current_index + direction) % len(players)
            print(f">> {players[skipped_index].name} skipped!")
            current_index = (skipped_index + direction) % len(players)
            continue

        elif top_card.value == 'reverse':
            print(">> Reverse!")
            direction *= -1

        elif top_card.value == 'draw2':
            next_index = (current_index + direction) % len(players)
            print(f">> {players[next_index].name} draws 2 cards!")
            players[next_index].draw(deck, 2)

        # ---------- WIN ----------
        if len(player.hand) == 0:
            print(f"\n>> {player.name} wins!")
            break

        # next turn
        current_index = (current_index + direction) % len(players)

# ---------------- RUN ----------------
play_uno()
