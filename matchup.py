from scipy.special import btdtr # regularized incomplete beta function

class matchup():
  def __init__(self, games, wins):
    self.games = games
    self.wins = wins
  def expected_winrate(self):
    ''' 
    As a consequence of the probability of winning a given match being a random variable determined by the beta distribution
    the following occurs.
    '''
    alpha = self.wins + 1
    beta = self.games - self.wins + 1
    return alpha / (alpha + beta)
  
  def winrate_variance(self):
    '''
    the variance of a random variable with a beta distribution is as follows
    '''
    alpha = self.wins + 1
    beta = self.games - self.wins + 1
    returtn (alpha * beta)/(((alpha + beta)**2)*(alpha + beta + 1))
  
  def probability_losing_matchup(self):
    '''
    the probability that the next game has below a 50% chance to win given that the results of previous independent games are known
    the regularized incomplete beta function evaluated at x = .5
    '''
    alpha = self.wins + 1
    beta = self.games - self.wins + 1
    return btdtr(alpha, beta, .5)
