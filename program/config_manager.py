import json

class DiscordConfig:
    def __init__(self, channel_id, bot_token, keywords, image_download_path):
        self.channel_id = channel_id
        self.bot_token = bot_token
        self.keywords = keywords
        self.image_download_path = image_download_path

class BettingCompanyConfig:
    def __init__(self, urls, username=None, password=None, bet_amounts=None):
        self.urls = urls
        self.username = username
        self.password = password
        self.bet_amounts = bet_amounts or {}

class BettingConfig:
    def __init__(self, betting_companies):
        self.betting_companies = betting_companies

class GeneralConfig:
    def __init__(self, path_to_model, google_credentials):
        self.path_to_model = path_to_model
        self.google_credentials = google_credentials

class ConfigManager:
    def __init__(self, config_file):
        with open(config_file, 'r', encoding='utf-8') as file:
            config_data = json.load(file)
        
        # Create Discord config
        discord_config = config_data.get('discord', {})
        self.discord = DiscordConfig(
            discord_config.get('channel_id'),
            discord_config.get('bot_token'),
            discord_config.get('keywords', []),
            discord_config.get('image_download_path')
        )

        # Create betting company configs
        betting_companies_config = config_data.get('betting_companies', {})
        betting_companies = {}
        for company_name, company_data in betting_companies_config.items():
            betting_companies[company_name] = BettingCompanyConfig(
                company_data.get('urls', []),
                company_data.get('username'),
                company_data.get('password'),
                company_data.get('bet_amounts')
            )

        self.betting = BettingConfig(betting_companies)

        # Create general config
        general_config = config_data.get('general', {})
        self.general = GeneralConfig(
            general_config.get('path_to_model'),
            general_config.get('google_credentials')
        )

    def get_discord_config(self):
        return self.discord

    def get_betting_config(self):
        return self.betting

    def get_general_config(self):
        return self.general
