# CnCNet Discord Bot
A single-server-per-instance bot to forward messages back and forth between CnCNet v5 IRC game channels, announce and list games in dedicated Discord channels. Will work with any game that uses [XNA CnCNet Client](https://github.com/CnCNet/xna-cncnet-client).


Features
--------

- Announce public games in a set announcement channel
- List games in a set list channel via rich embeds
- Forward messages between set game lobby IRC channel and set IRC channel
- Configure channels and announce message from Discord via `!config variable_name`
  - Available variables are `discord_message_channel`, `discord_list_channel`


Setting up
----------

1. Go to [Discord developer portal](https://discord.com/developers/applications/), create and configure your bot application, then invite it to your server.
2. Clone this repo via `git clone` or just download it via zip archive and unpack to the folder of your choice.
3. With **Python 3.7** or newer installed run `setup.bat` (Windows) / `setup.sh` (\*nix with Bash) from `Scripts` folder to create a virtual environment where all the needed packages and the interpreter for the bot will be located.
4. Run `run.bat` (Windows) / `run.sh` (\*nix with Bash) which activates the installed virtual environment, installs packages and runs the bot. The bot should terminate and generate an example `config.json` file.
5. Open the generated `config.json`, enter your bot application token (see step 1), change other config variables to accomodate your IRC channels and preferences (channel variables are set from Discord, don't try to change them manually.)
6. Run the script again (see step 4). The bot should connect to IRC and Discord.
7. Set the needed channels via `!config` command.


Credits
-------

- **Kerbiter** aka **Metadorius** - project author
- **Rampastring** and **CnCNet** team - XNA CnCNet Client without which this bot probably wouldn't exist



