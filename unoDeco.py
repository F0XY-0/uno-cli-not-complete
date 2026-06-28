import random
import collections
from dataclasses import dataclass


@dataclass
class Card:
    color: str
    val: str

    def __str__(self):
        return f"{self.color} {self.val}"


class Deck:
    colors = ['red', 'green', 'yellow', 'blue']
    numbers = []
    for n in range(10):
        numbers.append(str(n))
    actions = ['skip', 'reverse', 'draw2']
    values = numbers + actions

    def __init__(self):
        self.cards = []
        for color in self.colors:
            for value in self.values:
                self.cards.append(Card(color, value))
        self.discard = []

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            self.reshuffle()
        if not self.cards:
            raise Exception("No cards left!")
        return self.cards.pop()

    def reshuffle(self):
        if len(self.discard) <= 1:
            return
        top = self.discard.pop()
        self.cards = self.discard
        self.discard = [top]
        self.shuffle()
        print(">> Deck reshuffled!")


class Colorize:
    COLORS = {
        'red'    : "\033[91m",
        'green'  : "\033[92m",
        'yellow' : "\033[93m",
        'blue'   : "\033[94m",
        'reset'  : "\033[0m"
    }

    @classmethod
    def color_text(cls, card):
        color_code = cls.COLORS.get(card.color, '')
        reset = cls.COLORS['reset']
        return f"{color_code}[{card.color} {card.val}]{reset}"

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        def wrapper(*args, **kwargs):
            print(f"\n{instance.name}'s hand:")
            for i, card in enumerate(instance.hand):
                print(f"  {i} : {self.color_text(card)}")
        return wrapper


class Player:
    def __init__(self, name, is_bot=False):
        self.name = name
        self.hand = []
        self.is_bot = is_bot

    def draw(self, deck, count=1):
        for _ in range(count):
            self.hand.append(deck.draw())

    @Colorize
    def show_hand(self):
        pass

    def play(self, index, top_card):
        card = self.hand[index]
        if card.color != top_card.color and card.val != top_card.val:
            print("Invalid move")
            return None
        return self.hand.pop(index)


class Game:
    def __init__(self, players):
        self.players = players
        self.current = 0        # for the turn sys
        self.dirct = 1          # for the game direction
        self.skip_step = 0      # for the skip bug
        self.deck = Deck()
        self.deck.shuffle()

        for player in players:
            player.draw(self.deck, 7)

        self.top_card = self.deck.draw()

    def play_game(self):
        print(f"\n__unoCli__")
        print(f"First card is {Colorize.color_text(self.top_card)}")

        while True:
            self.play_turn()
            if self.game_over():
                w = self.winner()
                print(f"\nis the winner > {w.name}")
                break
            self.next_play()

    def play_turn(self):
        player = self.players[self.current]
        print(f"\n--- {player.name}'s turn | top card is {Colorize.color_text(self.top_card)}")
        self.skip_step = 0

        playable = []
        for i, card in enumerate(player.hand):
            match_color = card.color == self.top_card.color
            match_val = card.val == self.top_card.val
            if match_color or match_val:
                playable.append(i)

        if not playable:
            if player.is_bot:
                print(f"  {player.name} has no playable card — drawing until playable...")
                while True:
                    player.draw(self.deck)
                    drawn = player.hand[-1]
                    match_color = drawn.color == self.top_card.color
                    match_val = drawn.val == self.top_card.val
                    if match_color or match_val:
                        print(f"  {player.name} drew {Colorize.color_text(drawn)} — playable, playing it!")
                        player.hand.pop()
                        self.deck.discard.append(self.top_card)
                        self.top_card = drawn
                        self.handle_special()
                        return
                    print(f"  {player.name} drew {Colorize.color_text(drawn)} — not playable, drawing again...")
            else:
                print(f"  No playable card — {player.name} draws 1.")
                player.draw(self.deck)
                drawn = player.hand[-1]
                match_color = drawn.color == self.top_card.color
                match_val = drawn.val == self.top_card.val
                if match_color or match_val:
                    print(f"  Drawn card {Colorize.color_text(drawn)} is playable — playing it!")
                    player.hand.pop()
                    self.deck.discard.append(self.top_card)
                    self.top_card = drawn
                    self.handle_special()
            return

        if player.is_bot:
            choice = player.choose_card(self.top_card, self.players)
        else:
            player.show_hand()
            print(f"  Playable indices: {playable}")
            while True:
                try:
                    choice = int(input("  Pick an index: "))
                    if choice in playable:
                        break
                    print("  Not a valid playable index, try again.")
                except ValueError:
                    print("  Enter a number.")

        played = player.play(choice, self.top_card)

        if played is None:
            return

        self.deck.discard.append(self.top_card)
        self.top_card = played

        print(f"  {player.name} played {Colorize.color_text(played)}")

        if len(player.hand) == 1:
            print(f"  ** UNO! **")

        self.handle_special()

    def next_play(self):
        step = 1 + self.skip_step
        self.current = (self.current + step * self.dirct) % len(self.players)
        self.skip_step = 0

    def game_dirct(self):
        if self.dirct == 1:
            return 'clockwise'
        elif self.dirct == -1:
            return 'counter-clockwise'

    def handle_special(self):
        val = self.top_card.val
        n = len(self.players)

        if val == 'skip':
            skipped_index = (self.current + self.dirct) % n
            skip = self.players[skipped_index]
            print(f">> Skip! {skip.name} loses their turn.")
            self.skip_step = 1

        elif val == 'reverse':
            self.dirct *= -1
            print(f">> Reverse! Direction is now {self.game_dirct()}")
            if n == 2:
                self.skip_step = 1

        elif val == 'draw2':
            target_index = (self.current + self.dirct) % n
            target = self.players[target_index]
            target.draw(self.deck, 2)
            print(f">> Draw 2! {target.name} draws 2 cards and is skipped.")
            self.skip_step = 1

    def game_over(self):
        for p in self.players:
            if len(p.hand) == 0:
                return True
        return False

    def winner(self):
        for p in self.players:
            if len(p.hand) == 0:
                return p


# not very smart bot — simple priority rules bot
# uses the point system

class Bot(Player):
    def choose_card(self, top_card, players):
        playable = []
        for i, card in enumerate(self.hand):
            match_color = card.color == top_card.color
            match_val = card.val == top_card.val
            if match_color or match_val:
                playable.append(i)

        if not playable:
            return None

        someOneIsClose = False
        for p in players:
            if p is not self:
                if len(p.hand) <= 2:
                    someOneIsClose = True
                    break

        def score(index):
            card = self.hand[index]
            if card.val == 'draw2':
                base = 5
            elif card.val == 'skip':
                base = 4
            elif card.val == 'reverse':
                base = 3
            else:
                base = 1

            bonus = 0
            if card.val in ('skip', 'draw2') and someOneIsClose:
                bonus = 3
            return base + bonus

        return max(playable, key=score)


if __name__ == "__main__":
    players = [
        Player("You"),
        Bot("BotBob", is_bot=True),
        Bot("BotCat", is_bot=True),
    ]
    game = Game(players)
    game.play_game()
