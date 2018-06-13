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

## Possible Sources of Error

1. Saturation Effects
    * One matchups's probability to win may depend on the number of players playing each champion.
2. Synergistic Effects
    * Apart from Synnergies listed for the botlane on champion.gg no synnergies can be observed with the data collected. Such collection is feasible, albeit more involved.
3. Sub-groups
    * Different sets of players may perform differently. Perhaps, experienced Azir players perform much better than their newbie counterparts. Such analysis is outside of the initial scope of this project but may be included in the future.
