# bat2web

Ever wanted to turn a Windows batch file into a webapp running on a Linux server? Now you can.

# [Play Funtimes.bat on my website](https://tassaron.com/game/funtimes)

# Requirements

See [requirements.txt](/requirements.txt)

- Python 3.13.11
- Flask 3.1.2
- python-dotenv 1.2.1
- [Batchfile.py](https://github.com/tassaron/batchfile.py) 0.7 (my library, installed from git)
- lower Python versions down to 3.8 probably work if you also use an older Flask version

# Backstory

When I was 16 I used to write text adventure games using batch files. See the [Batchfile.py](https://github.com/tassaron/batchfile.py) readme for more information. I wrote Batchfile.py so I could play my old batch file games without Windows, and turning that into a website seemed like a fun extension of the idea.
