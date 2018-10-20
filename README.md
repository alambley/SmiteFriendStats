# SmiteFriendStats
A python script that takes your Smite username and returns stats on you and your teammates performance using the HiRezAPISession class, a Python wrapper for the HiRez API. 

# Usage
python3 FriendStats.py [Username]

python3 FriendStats.py [Username] [Number of teammates records to print]

You will also need a credentials.txt file at C:\ProgramData\HiRezAPISession. This first line must your HiRez API DevId and the second line must be your HiRez API AuthKey. See [this](https://www.hirezstudios.com/wp-content/themes/hi-rez-studios/pdf/smite-api-developer-guide.pdf) for more information on the HiRez API and go [here](https://fs12.formsite.com/HiRez/form48/secure_index.html) to request an API key.

# Example

Data from last 50 games for player 'Lambley'

Game percentage played with at least one friend : 100%

Player Kill Split : 228-231

Player KDR : 0.99

Friend Kill Split : 363-223

Friend KDR : 1.63

Other Kill Split : 668-650

Other KDR : 1.03


Username : Lambley

NumbGames : 50

Kills : 228

Deaths : 231

Assists : 638

KD : 0.99

Best Game : 5-0 20.00

Worst Game : 0-3 0.08
