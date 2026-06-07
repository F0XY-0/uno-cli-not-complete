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

            # count moves (fix)
            if self.count:
                if not hasattr(instance, "moves"):
                    instance.moves = 0
                instance.moves += 1

            # validate (safe args fix)
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


# ---------------- PLAYER ----------------
class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []

    @Deco(count=True)
    def draw(self, deck, count=1):
        for _ in range(count):
            self.hand.append(deck.draw())

    def show_hand(self):
        print(f"\n{self.name}'s hand:")
        for i, card in enumerate(self.hand):
            print(f"{i}: {card}")

    @Deco(validate=True , count=True)
    def play(self, index, top_card):
        return self.hand.pop(index)


# ---------------- GAME LOOP ----------------
def play_uno():
    deck = UnoDeck()
    deck.shuffle()

    p1 = Player("You")
    p2 = Player("Bot")

    for _ in range(5):
        p1.draw(deck)
        p2.draw(deck)

    top_card = deck.draw()
    current_player = p1

    while True:
        print("\n====================")
        print("Top card:", top_card)

        current_player.show_hand()

        # ---------- BOT ----------
        if current_player == p2:
            print("\nBot is playing...")
            played = None

            for i, card in enumerate(p2.hand):
                if card.color == top_card.color or card.value == top_card.value:
                    played = p2.play(i, top_card)
                    break

            if played:
                print("Bot played:", played)
                top_card = played
            else:
                print("Bot draws a card")
                p2.draw(deck)

        # ---------- PLAYER ----------
        else:
            choice = input("Choose index or 'd' to draw: ")

            if choice == 'd':
                p1.draw(deck)
                continue

            try:
                choice = int(choice)
            except:
                print("Invalid input")
                continue

            played = p1.play(choice, top_card)

            if played:
                top_card = played
            else:
                continue

        # ---------- SPECIAL RULES ----------
        if top_card.value == 'skip':
            print(">> Skip!")
            current_player = p1 if current_player == p2 else p2
            continue

        elif top_card.value == 'reverse':
            print(">> Reverse (ignored in 2 players2)")

        elif top_card.value == 'draw2':
            print(">> Draw 2!")
            next_player = p1 if current_player == p2 else p2
            next_player.draw(deck, 2)

        # ---------- WIN ----------
        if len(current_player.hand) == 0:
            print(f"\n>> {current_player.name} wins!")
            break

        current_player = p1 if current_player == p2 else p2


# ---------------- RUN ----------------
play_uno()
