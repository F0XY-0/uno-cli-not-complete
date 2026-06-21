import random
import collections

# ---------------- CARD ----------------
Card = collections.namedtuple('Card', ['color', 'value'])


# ---------------- DECORATOR ----------------
class Deco:
    """
    FIX: `count` now increments AFTER the wrapped function actually
    succeeds (i.e. after validation passes and the function runs),
    instead of before. Previously, failed/invalid plays were still
    counted as "moves".
    """
    def __init__(self, *, validate=False, count=False):
        self.validate = validate
        self.count = count

    def __call__(self, func):
        self.func = func
        return self

    def __get__(self, instance, owner):
        def wrapper(*args, **kwargs):
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

            result = self.func(instance, *args, **kwargs)

            if self.count:
                if not hasattr(instance, "moves"):
                    instance.moves = 0
                instance.moves += 1

            return result

        return wrapper


# ---------------- DECK ----------------
class UnoDeck:
    colors = ['red', 'green', 'blue', 'yellow']
    values = [str(n) for n in range(10)] + ['skip', 'reverse', 'draw2']

    def __init__(self):
        self._cards = [Card(color, value) for color in self.colors for value in self.values]
        self.discard = []  # FIX: track played cards so we can reshuffle when the draw pile runs out

    def shuffle(self):
        random.shuffle(self._cards)

    def draw(self):
        if not self._cards:
            self._reshuffle_discard()
        if not self._cards:
            raise Exception("No cards left to draw, even after reshuffling the discard pile!")
        return self._cards.pop()

    def _reshuffle_discard(self):
        """FIX: when the draw pile is empty, recycle the discard pile
        (keeping only the current top card out) instead of crashing."""
        if len(self.discard) <= 1:
            return  # nothing usable to reshuffle yet
        top = self.discard.pop()
        self._cards = self.discard
        self.discard = [top]
        self.shuffle()
        print(">> Deck reshuffled from the discard pile!")


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
    def __init__(self, name, is_bot=False):
        self.name = name
        self.hand = []
        self.is_bot = is_bot

    @Deco(count=True)
    def draw(self, deck, count=1):
        for _ in range(count):
            self.hand.append(deck.draw())

    @Colorize
    def show_hand(self):
        pass

    @Deco(validate=True, count=True)
    def play(self, index, top_card):
        return self.hand.pop(index)


# ---------------- HELPERS ----------------
def safe_draw(player, deck, count=1):
    """FIX: wraps player.draw() so a fully-exhausted deck (draw pile +
    discard pile both empty) ends the game gracefully instead of crashing
    with an uncaught exception."""
    try:
        player.draw(deck, count)
        return True
    except Exception as e:
        print(f">> {e}")
        return False


# ---------------- GAME LOOP ----------------
def play_uno():
    deck = UnoDeck()
    deck.shuffle()

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

    # FIX: don't start the game on an action card (skip/reverse/draw2) —
    # redraw until we get a plain number card to open with.
    top_card = deck.draw()
    while top_card.value in ('skip', 'reverse', 'draw2'):
        deck.discard.append(top_card)
        top_card = deck.draw()

    while True:
        print("\n====================")
        print("Top card:", Colorize.color_text(top_card))

        player = players[current_index]

        if not player.is_bot:
            player.show_hand()
        else:
            print(f"{player.name} has {len(player.hand)} cards")

        played = None

        # ---------- BOT ----------
        if player.is_bot:
            print(f"\n{player.name} is playing...")

            for i, card in enumerate(player.hand):
                if card.color == top_card.color or card.value == top_card.value:
                    played = player.play(i, top_card)
                    break

            if played:
                print(f"{player.name} played:", Colorize.color_text(played))
            else:
                print(f"{player.name} draws")
                if not safe_draw(player, deck):
                    print(">> No cards left anywhere. Game ends in a draw.")
                    break
                current_index = (current_index + direction) % len(players)
                continue

        # ---------- HUMAN ----------
        else:
            choice = input("Choose index or 'd' to draw: ")

            if choice == 'd':
                if not safe_draw(player, deck):
                    print(">> No cards left anywhere. Game ends in a draw.")
                    break
                current_index = (current_index + direction) % len(players)
                continue

            try:
                choice = int(choice)
            except ValueError:
                print("Invalid input")
                continue

            played = player.play(choice, top_card)

            if played is None:
                continue  # invalid move — same player tries again

        # ---------- CARD WAS SUCCESSFULLY PLAYED ----------
        deck.discard.append(top_card)
        top_card = played

        # ---------- WIN ----------
        # FIX: this now runs for every successful play, including skip/
        # reverse/draw2 cards. Previously, winning with a 'skip' card
        # skipped this check entirely because of the `continue` below.
        if len(player.hand) == 0:
            print(f"\n>> {player.name} wins!")
            break

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
            if len(players) == 2:
                # FIX: with only 2 players, reverse plays like a skip —
                # the opponent's turn is skipped and you go again.
                print(">> Only 2 players, reverse acts like a skip!")
                continue

        elif top_card.value == 'draw2':
            # FIX: the player who draws 2 also loses their turn now,
            # matching standard Uno rules.
            next_index = (current_index + direction) % len(players)
            print(f">> {players[next_index].name} draws 2 cards and is skipped!")
            if not safe_draw(players[next_index], deck, 2):
                print(">> No cards left anywhere. Game ends in a draw.")
                break
            current_index = (next_index + direction) % len(players)
            continue

        # next turn
        current_index = (current_index + direction) % len(players)


# ---------------- RUN ----------------
if __name__ == "__main__":
    play_uno()
