from abc import ABC, abstractmethod

class BettingCompany(ABC):
    
    @abstractmethod
    def __init__(self, teamA=None, teamB=None, amount=None, bet_category=None, bet_category1=None, bet_category2=None, bet=None, bet1=None, bet2=None, bet_builder=False, url=None):
        self.teamA = teamA
        self.teamB = teamB
        self.bet_category = bet_category
        self.bet_category1 = bet_category1
        self.bet_category2 = bet_category2
        self.bet = bet
        self.bet1 = bet1
        self.bet2 = bet2
        self.bet_builder = bet_builder
        self.amount = amount
        self.url=url
    
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def run(self):
        pass