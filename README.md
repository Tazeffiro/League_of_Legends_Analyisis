# League_of_Legends_Analyisis
A Python project using publicly available api's for the purposes of analysis

# Theory of Operation
## Concerning the game of picking and banning champions

The pick/ban portion of the game can be explained as a game of (near) perfect information. As only masteries and summoner spells are convealed from the opposing team. 

If two players are playing such a game of perfect information optimally, the best decision is the one which minimizes your opponents best move. This equates to the highest minimum probability of winning across all of that champions possible matchups. example say ezreal has a 57% chance to win vs vayne and, a 49% chance to win vs Lucian. The probability that should be used in comparison to other ADC's ought be 49%. This is because,  For the sake of brevity, I will refer champions with many effective counters as champions with high counterplay and, champions without effective counters as low counterplay.

Moreover, the initial pick ban phase should then be a matter of controlling the number of champions with low counterplay. Blue wanting 1 or 5 low counter play champions, and red wanting 3. A stituation where there are 0, 2, 4 or 6 would be neutral, assuming that all of the picks were of equivalent strength. 

## Concerning the Estimation of the probability of winning a given game from historical data

If we were to assume that if a player choses a given champion, that that player has a given probability if winning, p. The probability of winning k games out of n becomes 

P(n,k) = (n choose k) * (p^k) * (1-p)^(n-k) 

or a binomial distribution. If instead, n and k are fixed and we are attempting to estimate p. The probability density function becomes the following.

Pdf(p) = (p^k) * (1-p)^(n-k) / C 

where C is some normalization factor such that the integral of Pdf(p)dp from 0 to 1 is equal to 1. 

This is a beta distrubtion B(a,b) = B(k+1, n-k+1) = B(wins + 1, losses + 1). 

The expected winrate then becomes a/(a+b) = (k+1)/(n+2) = (wins + 1)/(wins + losses + 2) rather than the standard wins/(wins + losses) reported amongst most league of legends stats sites. 

With these distributions in hand comparisons between matchups becomes feasible as only the probability that one matchups chance to win is higher than the others needs to be considered.

## Estimating the Worst-Case Matchup
For a given set of matchups with win probabilities drawn from known distributions, the expected minimum winrate will follow the distribution determined by the product of all of the distbutions survival function (1 - cdf) integrated from 0 to 1. 

NOTE:
Not all champions, played in a given role, have played against eachother in a given data-set. As such, A distribution must be chosen such that these unplayed matchups effect the worst-case matchup calculation. This process will be most helpful when there is a high degree of uncertainty in the probability of the blindly chosen champion winning.

## Counter picks in Solo Queue
For the purpose of brevity I will constrain this discussion to the realm of solo queue. As a result, I will ignore trading champions and trading pick order. 

Given a set of champions picked by the enemy team, each of those champions will have a probability of playing in your lane or somewhere else. An example may be Karma being played as either support or mid. As a result the following arrises.

P(win) = P(win|karma mid) * P(karma mid) + P(win|karma not mid) * P(karma not mid)

This can be naturally expanded to cover all 5 champions picked by your opponents should you be last pick. 

NOTE:
In the absense of statistics regarding the rate of karma mid vs karma support given there is a karma in the game, I will use the play rate for each role for the champion in question. Thus if karma playes 25% of her games mid, I will estimate P(karma mid) to be 25%. Such statisitcs may come in the future when I am able to collect data on a large number of games.

### Counter picks in Competitive
Work in progress- Need to brush up on my understading of nash 

## Possible Sources of Error

1. Saturation Effects
    * One matchups's probability to win may depend on the number of players playing each champion.
2. Synergistic Effects
    * Apart from Synnergies listed for the botlane on champion.gg no synnergies can be observed with the data collected in this manner. Such collection is feasible, albeit more involved.
3. Sub-groups
    * Different sets of players may perform differently. Perhaps, experienced Azir players perform much better than their newbie counterparts. Such analysis is outside of the initial scope of this project but may be included in the future.
4. Pick Rarity
    * Rarer picks may only be picked into specific matchups, as such they may have largely inflated matchup winrates. 
