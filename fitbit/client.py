import json
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

class FitbitClient:
    # ---------------------------------------------------------
    # Constants
    # ---------------------------------------------------------
    class Dates:
        TODAY = datetime.now().strftime('%Y-%m-%d')
        YESTERDAY = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        TWO_DAYS_AGO = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        THREE_DAYS_AGO = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        FOUR_DAYS_AGO = (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d')
        FIVE_DAYS_AGO = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        SIX_DAYS_AGO = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
        PAST_WEEK = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        PAST_MONTH = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        PAST_QUARTER = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        PAST_HALF_YEAR = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        PAST_YEAR = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    class AZMPeriod:
        DAY = '1d'
        WEEK = '1w'
        MONTH = '1m'
        QUARTER = '3m'
        HALF_YEAR = '6m'
        YEAR = '1y'
    
    class ActivityGoalPeriod:
        DAY = 'daily'
        WEEK = 'weekly'
    
    class ActivityPeriod:
        DAY = '1d'
        WEEK = '1w'
        MONTH = '1m'
        QUARTER = '3m'
        HALF_YEAR = '6m'
        YEAR = '1y'
        
    class ActivityResource:
        ACTIVITY_CALORIES = 'activityCalories'
        CALORIES = 'calories'
        CALORIES_BMR = 'caloriesBMR'
        DISTANCE = 'distance'
        ELEVATION = 'elevation'
        FLOORS = 'floors'
        MINUTES_SEDENTARY = 'minutesSedentary'
        MINUTES_LIGHTLY_ACTIVE = 'minutesLightlyActive'
        MINUTES_FAIRLY_ACTIVE = 'minutesFairlyActive'
        MINUTES_VERY_ACTIVE = 'minutesVeryActive'
        STEPS = 'steps'
        SWIMMING_STROKES = 'swimming-strokes'
    
    class BodyGoalType:
        WEIGHT = 'weight'
        FAT = 'fat'
    
    class BodyResource:
        BMI = 'bmi'
        FAT = 'fat'
        WEIGHT = 'weight'
        
    class BodyPeriod(ActivityPeriod):
        # same as ActivityPeriod except for 
        MAX = 'max'
        
    class IntradayDetailLevel:
        SECOND_1 = '1sec'
        MINUTE_1 = '1min'
        MINUTE_5 = '5min'
        MINUTE_15 = '15min'
    
    class NutritionResource:
        CALORIES_IN = 'caloriesIn'
        WATER = 'water'
    
    # ---------------------------------------------------------
    # Initialization & Token Handling
    # ---------------------------------------------------------
    def __init__(self):
        self.api_version = '1'
        self.api_url = 'https://api.fitbit.com'
        self.client_id = os.getenv('FITBIT_CLIENT_ID')
        self.client_secret = os.getenv('FITBIT_CLIENT_SECRET')
        self.token_url = os.getenv('FITBIT_TOKEN_URL')
        self.token_data = self.__load_token()
        self.access_token = self.token_data['access_token']

    def __load_token(self):
        try:
            with open('token.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            try:
                from fitbit.auth_server import FitbitOAuth2Server
                server = FitbitOAuth2Server(self.client_id, self.client_secret)
                server.browser_authorize()
                self.token_data = server.fitbit.session.token
                self.__save_token(self.token_data)
                return self.token_data
            except Exception as e:
                print(f"Error loading token: {e}")

    def __save_token(self, token_data):
        with open('token.json', 'w') as file:
            json.dump(token_data, file)

    def __refresh_access_token(self):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.token_data['refresh_token'],
            'client_id': self.client_id,
        }

        response = requests.post(self.token_url, headers=headers, data=data)
        response.raise_for_status()
        new_token_data = response.json()
        self.__save_token(new_token_data)
        self.token_data = new_token_data

    def __get_access_token(self):
        expires_in = self.token_data['expires_in']
        token_expiry_time = datetime.now() + timedelta(seconds=expires_in)

        if datetime.now() >= token_expiry_time:
            print("Token expired, refreshing...")
            self.__refresh_access_token()

        return self.token_data['access_token']
    
    def __make_request(self, url, params=None, method='GET', data=None):
        access_token = self.__get_access_token()
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.request(method, url, headers=headers, params=params, data=data)
        response.raise_for_status()
        return response.json()
    
    # ------------------------------------------------------------
    # Active Zone Mintues
    # https://dev.fitbit.com/build/reference/web-api/active-zone-minutes-timeseries/
    # ------------------------------------------------------------
    def get_azm_time_series_by_period(self, date, period=AZMPeriod.DAY):
        """
        Get AZM Time Series by Period
        Retrieves a user's active zone minutes time series data for a specific date and period.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/active-zone-minutes/date/{date}/{period}.json'
        return self.__make_request(api_url, method='GET')

    def get_azm_time_series_by_interval(self, start_date, end_date):
        """
        Get AZM Time Series by Interval
        Retrieves a user's active zone minutes time series data for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/active-zone-minutes/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')
    
    # ------------------------------------------------------------
    # Activity
    # https://dev.fitbit.com/build/reference/web-api/activity/
    # ------------------------------------------------------------
    def get_activity_goals(self, period=ActivityGoalPeriod.DAY):
        """
        Create Activity Goals
        Creates or updates a user's daily or weekly activity goals.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/goals/{period}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_activity_log_list(self, before_date=Dates.TODAY, after_date=Dates.TODAY, sort='asc', limit=10, offset=0):
        """
        Get Activity Log List
        Retrieves a list of a user's activity log entries before or after a given day.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/list.json'
        params = {
            'sort': sort,
            'limit': limit,
            'offset': offset
        }
        
        if before_date:
            params['beforeDate'] = before_date
        elif after_date:
            params['afterDate'] = after_date

        return self.__make_request(api_url, params=params, method='GET')
    
    def get_activity_tcx(self, log_id, include_partial_tcx=False):
        """
        Get Activity TCX
        Retrieves the TCX data for a specific activity log.
        The Training Center XML (TCX) is a data exchange format that contains GPS, heart rate, and lap data. This endpoint retrieves the details of a user's location using GPS and heart rate data during a logged exercise.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/{log_id}.tcx'
        params = {
            'includePartialTCX': str(include_partial_tcx).lower()
        }
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/vnd.garmin.tcx+xml'
        }
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        return response.content
    
    def get_activity_type(self, activity_id):
        """
        Get Activity Type
        Retrieves the activity type for a specific activity log.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/{activity_id}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_all_activity_types(self): # TODO: This isnt working
        """
        Get All Activity Types
        Retrieves a list of all valid Fitbit public activities and the private, user-created activities.
        """
        return 'Not implemented yet'
    
    def get_daily_activity_summary(self, date=Dates.TODAY):
        """
        Get Daily Activity Summary
        Retrieves the user's daily activity summary for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/date/{date}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_favorite_activities(self):
        """
        Get Favorite Activities
        Retrieves the user's favorite activities.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/favorite.json'
        return self.__make_request(api_url, method='GET')
    
    def get_frequent_activities(self):
        """
        Get Frequent Activities
        Retrieves the user's frequent activities.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/frequent.json'
        return self.__make_request(api_url, method='GET')
    
    def get_lifetime_activity_stats(self):
        """
        Get Lifetime Activity Stats
        Retrieves the user's lifetime activity stats.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities.json'
        return self.__make_request(api_url, method='GET')
    
    def get_recent_activities(self):
        """
        Get Recent Activities
        Retrieves the user's recent activities.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/recent.json'
        return self.__make_request(api_url, method='GET')
        
    def get_activity_time_series_by_date(self, resource=ActivityResource.STEPS, date=Dates.TODAY, period=ActivityPeriod.DAY, timezone='UTC'):
        """
        Get Activity Time Series by Date
        Retrieves the user's activity time series data for a specific date and period.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/{resource}/date/{date}/{period}.json'
        params = {  
            'timezone': timezone
        }
        return self.__make_request(api_url, params=params, method='GET')
    
    def get_activity_time_series_by_range(self, resource=ActivityResource.STEPS, start_date=Dates.TODAY, end_date=Dates.TODAY, timezone='UTC'):
        """
        Get Activity Time Series by Range
        Retrieves the user's activity time series data for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/{resource}/date/{start_date}/{end_date}.json'
        params = {
            'timezone': timezone
        }
        return self.__make_request(api_url, params=params, method='GET')
    
    # ------------------------------------------------------------
    # Body
    # https://dev.fitbit.com/build/reference/web-api/body/
    # ------------------------------------------------------------
    def get_body_goals(self, goal_type=BodyGoalType.WEIGHT):
        """
        Get Body Goals
        Retrieves a user's body fat and weight goals.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/body/log/{goal_type}/goal.json'
        return self.__make_request(api_url, method='GET')
    
    def get_body_fat_log(self, date=Dates.TODAY):
        """
        Get Body Fat Log
        Retrieves a user's body fat log for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/body/log/fat/date/{date}.json'
        return self.__make_request(api_url, method='GET')

    def get_body_weight_log(self, date=Dates.TODAY):
        """
        Get Body Weight Log
        Retrieves a user's body weight log for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/body/log/weight/date/{date}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_body_time_series_by_date(self, resource=BodyResource.WEIGHT, date=Dates.TODAY, period=BodyPeriod.DAY):
        """
        Get Body Time Series by Date
        Retrieves a list of a user's body data (e.g., bmi, fat, weight) for a given period.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/body/{resource}/date/{date}/{period}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_body_time_series_by_date_range(self, resource=BodyResource.WEIGHT, start_date=Dates.TODAY, end_date=Dates.TODAY):
        """
        Get Body Time Series by Date Range
        Retrieves a list of a user's body data (e.g., weight, fat) for a given date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/body/{resource}/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')
        #############################################
    
    def get_body_fat_time_series_by_date(self, date, period=BodyPeriod.DAY):
        """
        Get Body Fat Time Series by Date
        Retrieves a list of all user's body fat log entries for a given period.
        """
        if period not in (self.BodyPeriod.DAY, self.BodyPeriod.WEEK, self.BodyPeriod.MONTH):
            raise ValueError("Period must be one of the following: DAY, WEEK, MONTH")
        api_url = f'{self.api_url}/{self.api_version}/user/-/body/log/fat/date/{date}/{period}.json'
        return self.__make_request(api_url, method='GET')

    def get_body_fat_time_series_by_date_range(self, start_date, end_date):
        """
        Get Body Fat Time Series by Date Range
        Retrieves a list of all user's body fat log entries for a given date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/body/log/fat/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_body_weight_time_series_by_date(self, date, period=BodyPeriod.DAY):
        """
        Get Body Weight Time Series by Date
        Retrieves a list of all user's body weight log entries for a given period.
        """
        if period not in (self.BodyPeriod.DAY, self.BodyPeriod.WEEK, self.BodyPeriod.MONTH):
            raise ValueError("Period must be one of the following: DAY, WEEK, MONTH")
        api_url = f'{self.api_url}/{self.api_version}/user/-/body/log/weight/date/{date}/{period}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_body_weight_time_series_by_date_range(self, start_date=Dates.TODAY, end_date=Dates.TODAY):
        """
        Get Body Weight Time Series by Date Range
        Retrieves a list of all user's body weight log entries for a given date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/body/log/weight/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')
    
    # ------------------------------------------------------------
    # Breathing Rate
    # https://dev.fitbit.com/build/reference/web-api/breathing-rate/
    # ------------------------------------------------------------
    def get_breathing_rate_summary_by_date(self, date=Dates.TODAY):
        """
        Get Breathing Rate Summary by Date
        Retrieves the user's breathing rate summary for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/br/date/{date}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_breathing_rate_summary_by_date_range(self, start_date=Dates.TODAY, end_date=Dates.TODAY):
        """
        Get Breathing Rate Summary by Date Range
        Retrieves the user's breathing rate summary for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/br/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')
    
    # ------------------------------------------------------------
    # cardio-fitness-score (VO2 Max)
    # https://dev.fitbit.com/build/reference/web-api/cardio-fitness-score/
    # -----------------------------------------------------------
    def get_vo2_max_summary_by_date(self, date=Dates.TODAY):
        """
        Get VO2 Max Summary by Date
        Retrieves the user's VO2 Max summary for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/cardioscore/date/{date}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_vo2_max_summary_by_date_range(self, start_date=Dates.TODAY, end_date=Dates.TODAY):
        """
        Get VO2 Max Summary by Date Range
        Retrieves the user's VO2 Max summary for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/cardioscore/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')
    
    # ------------------------------------------------------------
    # Devices & Alarms
    # https://dev.fitbit.com/build/reference/web-api/devices/
    # ------------------------------------------------------------
    def get_devices(self):
        """
        Get Devices
        Retrieves the user's devices.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/devices.json'
        return self.__make_request(api_url, method='GET')
    
    def get_alarms(self, tracker_id=None):
        """
        Get Alarms
        Retrieves the user's alarms for a specific device.
        If no tracker_id is provided, the first device in the list is used.
        If error 400, return empty list
        """
        if tracker_id == None:
            try:
                tracker_id = self.get_devices()[0]['id']
            except Exception as e:
                print(f"Error getting device ID: {e}")
                return None
        api_url = f'{self.api_url}/{self.api_version}/user/-/devices/tracker/{tracker_id}/alarms.json'
        try:
            response = self.__make_request(api_url, method='GET')
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                return []
            else:
                raise
        return response
    
    # ------------------------------------------------------------
    # ECG
    # https://dev.fitbit.com/build/reference/web-api/electrocardiogram/
    # ------------------------------------------------------------
    def get_ecg_log_list(self, after_date=Dates.YESTERDAY, before_date=Dates.TODAY, sort='asc', limit=10, offset=0):
        """
        Get ECG Log List
        Retrieves a list of a user's ECG log entries.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/ecg/list.json'
        params = {
            'sort': sort,
            'limit': limit,
            'offset': offset
        }
        
        if after_date:
            params['afterDate'] = after_date
        elif before_date:
            params['beforeDate'] = before_date

        return self.__make_request(api_url, params=params, method='GET')['ecgReadings']

    # ------------------------------------------------------------
    # Friends
    # https://dev.fitbit.com/build/reference/web-api/friends
    # ------------------------------------------------------------
    def get_friends(self, api_version=1.1):
        """
        Get Friends
        Retrieves the user's friends.
        API version is 1.1 by default, for some reason its not 1 like the other endpoints.
        """
        api_url = f'{self.api_url}/{api_version}/user/-/friends.json'
        return self.__make_request(api_url, method='GET')

    def get_friends_leaderboard(self, api_version=1.1):
        """
        Get Friends Leaderboard
        Retrieves the user's friends leaderboard.
        API version is 1.1 by default, for some reason its not 1 like the other endpoints.
        """
        api_url = f'{self.api_url}/{api_version}/user/-/leaderboard/friends.json'
        return self.__make_request(api_url, method='GET')

    # ------------------------------------------------------------
    # Heart Rate
    # https://dev.fitbit.com/build/reference/web-api/heartrate-timeseries/
    # ------------------------------------------------------------
    def get_heart_rate_time_series_by_date(self, date=Dates.TODAY, period=ActivityPeriod.DAY):
        """
        Get Heart Rate Time Series by Date
        Retrieves a list of a user's heart rate time series data for a specific date and period.
        """
        if period not in (self.ActivityPeriod.DAY, self.ActivityPeriod.WEEK, self.ActivityPeriod.MONTH):
            raise ValueError("Period must be one of the following: DAY, WEEK, MONTH")
        
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/heart/date/{date}/{period}.json'
        return self.__make_request(api_url, method='GET')['activities-heart']
    
    def get_heart_rate_time_series_by_date_range(self, start_date=Dates.TODAY, end_date=Dates.TODAY):
        """
        Get Heart Rate Time Series by Date Range
        Retrieves a list of a user's heart rate time series data for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/heart/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')['activities-heart']
    
    def get_hrv_summary_by_date(self, date=Dates.TODAY):
        """
        Get HRV Summary by Date
        Retrieves the user's HRV summary for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/hrv/date/{date}.json'
        return self.__make_request(api_url, method='GET')

    def get_hrv_summary_by_date_range(self, start_date=Dates.TODAY, end_date=Dates.TODAY):
        """
        Get HRV Summary by Date Range
        Retrieves the user's HRV summary for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/hrv/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')
    
    # ------------------------------------------------------------
    # Intraday/Detailed Endpoints
    # https://dev.fitbit.com/build/reference/web-api/intraday/
    # ------------------------------------------------------------
    def get_azm_intraday_by_date(self, date=Dates.TODAY, detail_level=IntradayDetailLevel.MINUTE_15):
        """
        Get AZM Intraday by Date
        Retrieves the active zone minute (AZM) intraday time series data for a specific date.
        """
        if detail_level not in (self.IntradayDetailLevel.MINUTE_1, self.IntradayDetailLevel.MINUTE_5, self.IntradayDetailLevel.MINUTE_15):
            raise ValueError("Detail level must be one of the following: MINUTE_1, MINUTE_5, MINUTE_15")
        
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/active-zone-minutes/date/{date}/1d/{detail_level}.json'
        return self.__make_request(api_url, method='GET') 
    
    def get_activity_intraday_by_date(self, resource=ActivityResource.STEPS, date=Dates.TODAY, detail_level=IntradayDetailLevel.MINUTE_1, start_time=None, end_time=None, timezone='UTC'):
        """
        Get Activity Intraday by Date
        Retrieves the activity intraday time series data for a given resource on a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/{resource}/date/{date}/1d/{detail_level}.json'
        
        if start_time and end_time:
            api_url = f'{self.api_url}/{self.api_version}/user/-/activities/{resource}/date/{date}/1d/{detail_level}/time/{start_time}/{end_time}.json'
        
        params = {
            'timezone': timezone
        }
        
        return self.__make_request(api_url, params=params, method='GET')
    
    def get_activity_intraday_by_date_range(self, resource=ActivityResource.STEPS, start_date=Dates.TODAY, end_date=Dates.TODAY, detail_level=IntradayDetailLevel.MINUTE_1, start_time=None, end_time=None, timezone='UTC'):
        """
        Get Activity Intraday by Date Range
        Retrieves the activity intraday time series data for a given resource on a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/{resource}/date/{start_date}/{end_date}/1d/{detail_level}.json'
        
        if start_time and end_time:
            api_url = f'{self.api_url}/{self.api_version}/user/-/activities/{resource}/date/{start_date}/{end_date}/1d/{detail_level}/time/{start_time}/{end_time}.json'
        
        params = {
            'timezone': timezone
        }   
        
        return self.__make_request(api_url, params=params, method='GET')
        
    def get_breathing_rate_intraday_by_date(self, date):
        """
        Get Breathing Rate Intraday by Date
        Retrieves intraday breathing rate data for a specified date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/br/date/{date}/all.json'
        
        try:
            return self.__make_request(api_url, method='GET')
        except Exception as e:
            print(f"Error getting breathing rate intraday data: {e}")
            return None
    
    def get_breathing_rate_intraday_by_date_range(self, start_date=Dates.TODAY, end_date=Dates.TODAY):
        """
        Get Breathing Rate Intraday by Date Range
        Retrieves intraday breathing rate data for a specified date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/br/date/{start_date}/{end_date}/all.json'
        return self.__make_request(api_url, method='GET')

    def get_heart_rate_intraday_by_date(self, date=Dates.TODAY, detail_level=IntradayDetailLevel.MINUTE_1, start_time=None, end_time=None, timezone='UTC'):
        """
        Get Heart Rate Intraday by Date
        Retrieves the heart rate intraday time series data for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/heart/date/{date}/1d/{detail_level}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_heart_rate_intraday_by_date_range(self, start_date=Dates.TODAY, end_date=Dates.TODAY, detail_level=IntradayDetailLevel.MINUTE_1, start_time=None, end_time=None, timezone='UTC'):
        """
        Get Heart Rate Intraday by Date Range
        Retrieves the heart rate intraday time series data for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/activities/heart/date/{start_date}/{end_date}/1d/{detail_level}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_hrv_intraday_by_date(self, date=Dates.TODAY):
        """
        Get HRV Intraday by Date
        Retrieves the HRV intraday time series data for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/hrv/date/{date}.json'
        return self.__make_request(api_url, method='GET')

    def get_hrv_intraday_by_date_range(self, start_date=Dates.PAST_WEEK, end_date=Dates.TODAY):
        """
        Get HRV Intraday by Date Range
        Retrieves the HRV intraday time series data for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/hrv/date/{start_date}/{end_date}/all.json'
        return self.__make_request(api_url, method='GET')
        
    def get_spo2_intraday_by_date(self, date=Dates.YESTERDAY):
        """
        Get SPO2 Intraday by Date
        Retrieves the SPO2 intraday time series data for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/spo2/date/{date}/all.json'
        return self.__make_request(api_url, method='GET')
    
    def get_spo2_intraday_by_date_range(self, start_date=Dates.PAST_WEEK, end_date=Dates.TODAY):
        """
        Get SPO2 Intraday by Date Range
        Retrieves the SPO2 intraday time series data for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/spo2/date/{start_date}/{end_date}/all.json'
        return self.__make_request(api_url, method='GET')
    
    # ------------------------------------------------------------
    # Irregular Rhythm Notifications
    # https://dev.fitbit.com/build/reference/web-api/irregular-rhythm-notifications/
    # ------------------------------------------------------------
    def get_irn_alerts_list(self, after_date=Dates.YESTERDAY, before_date=Dates.TODAY, sort='asc', limit=10, offset=0):
        """
        Get IRN Alerts List
        Retrieves a paginated list of Irregular Rhythm Notifications (IRN) alerts.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/irn/alerts/list.json'
        params = {
            'sort': sort,
            'limit': limit,
            'offset': offset
        }
        
        if after_date:
            params['afterDate'] = after_date
        elif before_date:
            params['beforeDate'] = before_date

        return self.__make_request(api_url, params=params, method='GET')

    def get_irn_profile(self):
        """
        Get IRN Profile
        Retrieves the user's Irregular Rhythm Notifications (IRN) profile.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/irn/profile.json'
        return self.__make_request(api_url, method='GET')
    
    # ------------------------------------------------------------
    # Nutrition
    # https://dev.fitbit.com/build/reference/web-api/nutrition/
    # ------------------------------------------------------------
    def get_favorite_foods(self):
        """
        Get Favorite Foods
        Retrieves the user's favorite foods.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/foods/log/favorite.json'
        return self.__make_request(api_url, method='GET')
    
    def get_food(self, food_id):
        """
        Get Food
        Retrieves detailed information about a specific food.
        """
        api_url = f'{self.api_url}/{self.api_version}/foods/{food_id}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_food_locale(self):
        """
        Get Food Locale
        Retrieves the user's food locale.
        """
        api_url = f'{self.api_url}/{self.api_version}/foods/locales.json'
        return self.__make_request(api_url, method='GET')
    
    def get_food_goals(self):
        """
        Get Food Goals
        Retrieves the user's food goals.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/foods/log/goal.json'
        return self.__make_request(api_url, method='GET')
    
    def get_food_log(self, date=Dates.TODAY):
        """
        Get Food Log
        Retrieves the user's food log for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/foods/log/date/{date}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_food_units(self):
        """
        Get Food Units
        Retrieves the user's food units.
        """
        api_url = f'{self.api_url}/{self.api_version}/foods/units.json'
        return self.__make_request(api_url, method='GET')
    
    def get_frequent_foods(self):
        """
        Get Frequent Foods
        Retrieves the user's frequent foods.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/foods/log/frequent.json'
        return self.__make_request(api_url, method='GET')
    
    def get_meal(self, meal_id):
        """
        Get Meal
        Retrieves detailed information about a specific meal.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/meals/{meal_id}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_meals(self):
        """
        Get Meals
        Retrieves the user's meals.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/meals.json'
        return self.__make_request(api_url, method='GET')
    
    def get_recent_foods(self):
        """
        Get Recent Foods
        Retrieves the user's recent foods.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/foods/log/recent.json'
        return self.__make_request(api_url, method='GET')

    def get_water_goal(self):
        """
        Get Water Goal
        Retrieves the user's water goal.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/foods/log/water/goal.json'
        return self.__make_request(api_url, method='GET')
    
    def get_water_log(self, date=Dates.TODAY):
        """
        Get Water Log
        Retrieves the user's water log for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/foods/log/water/date/{date}.json'
        return self.__make_request(api_url, method='GET')
    
    def search_foods(self, query):
        """
        Search Foods
        Searches for foods based on a query.
        """
        api_url = f'{self.api_url}/{self.api_version}/foods/search.json'
        return self.__make_request(api_url, method='GET', params={'query': query})['foods']
        
    def get_nutrition_time_series_by_date(self, resource=NutritionResource.CALORIES_IN, date=Dates.TODAY, period=ActivityPeriod.DAY):
        """
        Get Nutrition Time Series by Date
        Retrieves the nutrition time series data for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/foods/log/{resource}/date/{date}/{period}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_nutrition_time_series_by_date_range(self, resource=NutritionResource.CALORIES_IN, start_date=Dates.TODAY, end_date=Dates.TODAY):
        """
        Get Nutrition Time Series by Date Range
        Retrieves the nutrition time series data for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/foods/log/{resource}/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')
    
    # ------------------------------------------------------------
    # Sleep
    # https://dev.fitbit.com/build/reference/web-api/sleep/
    # ------------------------------------------------------------
    def get_sleep_goal(self, api_verison=1.2):
        """
        Get Sleep Goal
        Retrieves the user's sleep goal.
        """
        api_url = f'{self.api_url}/{api_verison}/user/-/sleep/goal.json'
        return self.__make_request(api_url, method='GET')

    def get_sleep_log_by_date(self, date=Dates.TODAY, api_verison=1.2):
        """
        Get Sleep Log by Date
        Retrieves the user's sleep log for a specific date.
        """
        api_url = f'{self.api_url}/{api_verison}/user/-/sleep/date/{date}.json'
        return self.__make_request(api_url, method='GET')['sleep']
    
    def get_sleep_log_by_date_range(self, start_date=Dates.TODAY, end_date=Dates.TODAY, api_verison=1.2):
        """ 
        Get Sleep Log by Date Range
        Retrieves the user's sleep log for a specific date range.
        """
        api_url = f'{self.api_url}/{api_verison}/user/-/sleep/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')['sleep']
    
    def get_sleep_log_list(self, after_date=Dates.PAST_WEEK, before_date=Dates.TODAY, sort='asc', limit=100, offset=0):
        """
        Get Sleep Log List
        Retrieves a list of a user's sleep log entries before or after a given date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/sleep/list.json'
        params = {
            'sort': sort,
            'limit': limit,
            'offset': offset
        }
        
        if after_date:
            params['afterDate'] = after_date
        elif before_date:
            params['beforeDate'] = before_date

        return self.__make_request(api_url, method='GET', params=params)

    
    # ------------------------------------------------------------
    # SpO2
    # https://dev.fitbit.com/build/reference/web-api/spo2/
    # ------------------------------------------------------------
    def get_spo2_by_date(self, date=Dates.TODAY):
        """
        Get SPO2 by Date
        Retrieves the user's SPO2 data for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/spo2/date/{date}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_spo2_by_date_range(self, start_date=Dates.TODAY, end_date=Dates.TODAY):
        """
        Get SPO2 by Date Range
        Retrieves the user's SPO2 data for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/spo2/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')
    

    # ------------------------------------------------------------
    # Subscription
    # https://dev.fitbit.com/build/reference/web-api/subscription/
    # ------------------------------------------------------------
    def create_fitbit_subscription(self, collection_type, subscription_id):
        if collection_type is not None:
            url = f"https://api.fitbit.com/1/user/-/{collection_type}/apiSubscriptions/{subscription_id}.json"
        else:
            url = f"https://api.fitbit.com/1/user/-/apiSubscriptions/{subscription_id}.json"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Fitbit-Subscriber-Id": "dev"  # Optional, for multi-subscriber setups
        }
        response = requests.post(url, headers=headers)
        
        if response.status_code == 201:
            print("Subscription created successfully.")
        elif response.status_code == 409:
            print("Subscription already exists.")
        elif response.status_code == 400:
            print("Invalid subscription ID.")
        else:
            print(f"Failed to create subscription: {response.status_code} - {response.text}")
        return response.json()

    def list_fitbit_subscriptions(self):
        url = f"https://api.fitbit.com/1/user/-/apiSubscriptions.json"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        response = requests.get(url, headers=headers)
        return response.json()
    
    # ------------------------------------------------------------
    # Temperature
    # https://dev.fitbit.com/build/reference/web-api/temperature/
    # ------------------------------------------------------------
    def get_temperature_core_by_date(self, date=Dates.TODAY):
        """
        Get Temperature by Date
        Retrieves the user's temperature data for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/temp/core/date/{date}.json'
        return self.__make_request(api_url, method='GET')

    def get_temperature_core_by_date_range(self, start_date=Dates.TODAY, end_date=Dates.TODAY):
        """
        Get Temperature by Date Range
        Retrieves the user's temperature data for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/temp/core/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_temperature_skin_by_date(self, date=Dates.TODAY):
        """
        Get Temperature Skin by Date
        Retrieves the user's skin temperature data for a specific date.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/temp/skin/date/{date}.json'
        return self.__make_request(api_url, method='GET')
    
    def get_temperature_skin_by_date_range(self, start_date=Dates.TODAY, end_date=Dates.TODAY):
        """
        Get Temperature Skin by Date Range
        Retrieves the user's skin temperature data for a specific date range.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/temp/skin/date/{start_date}/{end_date}.json'
        return self.__make_request(api_url, method='GET')

    # ------------------------------------------------------------
    # User
    # https://dev.fitbit.com/build/reference/web-api/user-api/
    # ------------------------------------------------------------
    def get_profile(self):
        """
        Get Profile
        Retrieves the user's profile information.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/profile.json'
        return self.__make_request(api_url)
        
    def get_badges(self):
        """
        Get Badges
        Retrieves the user's badges.
        """
        api_url = f'{self.api_url}/{self.api_version}/user/-/badges.json'
        return self.__make_request(api_url)['badges']


    
fitbit = FitbitClient()


# TODO: 
# - better error handling
# - logging
# - I just did "r" from crud. i still need cud.