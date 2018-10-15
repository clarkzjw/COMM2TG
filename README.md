# [Deprecated] COMM2TG
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fclarkzjw%2FCOMM2TG.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2Fclarkzjw%2FCOMM2TG?ref=badge_shield)


A bot that catches Ingress comm messages and forwardes them to Telegram channel.

## Dependencies

+ *nix like OS, tested on Ubuntu

+ Python3

+ [Python-Telegram-Bot](https://github.com/python-telegram-bot/python-telegram-bot)

+ selenium

```bash
sudo pip3 install selenium
```

+ [Phantomjs](http://phantomjs.org/)

## Usage

+ Make sure your OS support coresponding locales based on your comm range.

  e.g. zh_CN.UTF-8

```bash
sudo locale-gen zh_CN.UTF-8
sudo dpkg-reconfigure locales
```

+ Copy `config.json.example` to `config.json` first, and remember to modify `config.json` and `PhantomjsPath` in `bot.py`

  To run, just type

```bash
python3 bot.py
```


## License
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fclarkzjw%2FCOMM2TG.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2Fclarkzjw%2FCOMM2TG?ref=badge_large)
