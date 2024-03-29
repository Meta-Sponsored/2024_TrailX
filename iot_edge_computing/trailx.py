"""This module is the main program of Trailx, allowing Jetson Nano to 
detect and track objects."""

# References:
# - https://github.com/dusty-nv/jetson-inference/blob/master/docs/detectnet-example-2.md
# - https://github.com/dusty-nv/jetson-inference/blob/master/docs/detectnet-tracking.md

import os
import sys
from dotenv import load_dotenv
import threading
from threading import Timer
import time
from datetime import datetime
import random
import requests
import pytz
from jetson_inference import detectNet
from jetson_utils import videoSource
from object_class import object_class
from data_analysis import update_user_counter
from speed_tracker import SpeedTracker
from led_screen_controller import (
    change_frame_rate,
    get_current_mode,
    change_led_screen_mode,
    run_led_screen,
    ANIMATIONS_PATH,
)
from animations.gif_frame_rates import gif_frame_rates

OPEN_WEATHER_API_PATH = "/home/trailx/Desktop/keys/open_weather_api.env"
WARNING_SPEED = 10  # Unit: Miles Per Hour
SPEED_LIMIT_SPEED = 15  # Unit: Miles Per Hour
FULLY_FUNCTIONAL_CLOUD_COVERAGE = 100  # Range: 0-100%
LIMITED_FUNCTIONAL_CLOUD_COVERAGE = 100  # Range: 0-100%
COOLDOWN_TIME_BETWEEN_ANIMATIONS = 45  # Unit: Seconds
ANIMATION_PLAY_TIME = 15  # Unit: Seconds


# Function to get weather data including cloud coverage, sunrise, and sunset times, and city name
def get_weather_data(api_key, city_name, time_zone):
    """Function to get weather data including cloud coverage, sunrise,
    and sunset times, and city name."""

    base_url = (
        f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}"
    )

    try:
        response = requests.get(base_url, timeout=100)
        data = response.json()

        if "clouds" in data:
            cloud_coverage = data["clouds"]["all"]
        else:
            cloud_coverage = None

        if "sys" in data:
            sunrise_time_utc = data["sys"]["sunrise"]
            sunset_time_utc = data["sys"]["sunset"]
        else:
            sunrise_time_utc = None
            sunset_time_utc = None

        current_time_utc = data["dt"]

        # Get the city name
        if "name" in data:
            city_name = data["name"]
        else:
            city_name = None

        # Convert Unix timestamps to human-readable strings in the local time zone
        sunrise_time = datetime.fromtimestamp(
            sunrise_time_utc, tz=pytz.timezone(time_zone)
        )
        sunset_time = datetime.fromtimestamp(
            sunset_time_utc, tz=pytz.timezone(time_zone)
        )
        current_time = datetime.fromtimestamp(
            current_time_utc, tz=pytz.timezone(time_zone)
        )

        print("City Name:", city_name)
        print("Cloud Coverage:", cloud_coverage)
        print("Sunrise Time:", sunrise_time.strftime("%Y-%m-%d %H:%M:%S %Z"))
        print("Sunset Time:", sunset_time.strftime("%Y-%m-%d %H:%M:%S %Z"))
        print("Current Time:", current_time.strftime("%Y-%m-%d %H:%M:%S %Z"))

        return cloud_coverage, sunrise_time_utc, sunset_time_utc, current_time_utc
    except requests.RequestException as e:
        print("HTTP request error:", e)
    except ValueError as e:
        print("JSON decoding error:", e)
    except Exception as e:
        print("An unexpected error occurred:", e)

    return None, None, None, None


# Function to check if the device should enter idle state
def check_idle_state(api_key, city_name, state_change_event, time_zone):
    """Function to check if the device should enter idle state."""

    while True:
        cloud_coverage, sunrise_time, sunset_time, current_time = get_weather_data(
            api_key, city_name, time_zone
        )

        if (
            cloud_coverage is not None
            and sunrise_time is not None
            and sunset_time is not None
            and current_time is not None
        ):
            if (
                current_time >= sunrise_time
                and current_time <= sunset_time
                and cloud_coverage <= LIMITED_FUNCTIONAL_CLOUD_COVERAGE
            ):
                _, playback_mode = get_current_mode()
                if cloud_coverage <= FULLY_FUNCTIONAL_CLOUD_COVERAGE:
                    change_led_screen_mode(
                        led_screen_enabled=True, playback_mode=playback_mode
                    )
                else:
                    change_led_screen_mode(
                        led_screen_enabled=False, playback_mode=playback_mode
                    )
                state_change_event.clear()  # Clear the event flag to continue running
                time.sleep(900)
            else:
                state_change_event.set()  # Set the event flag to signal the main program
                print("State changed to idle.")

                # Disable the LED screen and set playback back to Default = 0,
                # which will play 0.gif the next time the LED screen is enabled.
                led_screen_enabled, playback_mode = get_current_mode()
                if led_screen_enabled or playback_mode != 0:
                    change_frame_rate(gif_frame_rates[0])
                    change_led_screen_mode(led_screen_enabled=False, playback_mode=0)
                time.sleep(1800)
        else:
            time.sleep(60)  # Retry after 1 minute if weather data is unavailable


# Function to randomly select animations to play when a user is detected.
def play_random_animation():
    """Function to randomly select animations to play when a user is detected."""

    led_screen_enabled, current_playback_mode = get_current_mode()
    if current_playback_mode == 0:
        num_of_gif_files = len(
            [
                name
                for name in os.listdir(ANIMATIONS_PATH)
                if os.path.isfile(os.path.join(ANIMATIONS_PATH, name))
                and name.endswith(".gif")
            ]
        )
        # If a pre-made animation exists. Check the files in the ANIMATIONS_PATH.
        if num_of_gif_files >= 3:
            gif_to_show = random.randrange(3, num_of_gif_files)
            change_frame_rate(gif_frame_rates[gif_to_show])
            change_led_screen_mode(led_screen_enabled, gif_to_show)

            # Return to the default gif image.
            timer = Timer(
                ANIMATION_PLAY_TIME, change_led_screen_mode, [led_screen_enabled, 0]
            )
            timer.start()


# Function to run the main program
def run_object_detection(
    state_change_event, total_user_counted, total_bike_counted, total_dog_counted
):
    """Function to run the main program."""

    net = detectNet("ssd-mobilenet-v2", threshold=0.6)
    net.SetTrackingEnabled(True)
    net.SetTrackingParams(minFrames=20, dropFrames=100, overlapThreshold=0.1)

    camera = videoSource("/dev/video0", argv=["--input-flip=rotate-180"])
    last_animation_time = 0

    while True:
        img = camera.Capture()
        if img is None:
            continue

        tracking_types = set(["bicycle", "dog", "person"])
        detections = net.Detect(img)
        for detection in detections:
            (
                total_user_counted,
                total_bike_counted,
                total_dog_counted,
            ) = update_user_counter(
                detection, total_user_counted, total_bike_counted, total_dog_counted
            )

            # When a user is detected, we start randomly playing a pre-made animation.
            # The cooldown is to avoid playing the next animation
            # without going back to the preset static background.
            if (
                detection.TrackID >= 0
                and detection.TrackStatus >= 0
                and object_class[detection.ClassID] in tracking_types
            ):
                current_time = time.time()
                if (
                    current_time - last_animation_time
                    >= COOLDOWN_TIME_BETWEEN_ANIMATIONS
                ):
                    play_random_animation()
                    last_animation_time = current_time

        # print(f"Detecting Object | Network: {net.GetNetworkFPS():.0f} FPS")

        if (
            state_change_event.is_set()
        ):  # Check if the event flag is set (indicating a state change)
            print("Exiting main program...")
            break

    return total_user_counted, total_bike_counted, total_dog_counted


# Main function to control installation states
def main(api_key, city_name, time_zone):
    """Main function to control device states."""

    state_change_event = threading.Event()  # Event flag to signal state change
    weather_checking_thread = threading.Thread(
        target=check_idle_state,
        args=(api_key, city_name, state_change_event, time_zone),
    )
    weather_checking_thread.start()
    time.sleep(20)
    tracker = SpeedTracker(WARNING_SPEED, SPEED_LIMIT_SPEED)
    lidar_speed_update_thread = threading.Thread(
        target=tracker.update_object_speed,
    )
    lidar_speed_update_thread.start()
    time.sleep(5)

    total_user_counted, total_bike_counted, total_dog_counted = 0, 0, 0

    while True:
        if (
            state_change_event.is_set()
        ):  # Check if the event flag is set (indicating a state change)
            print("Device is in standby mode.")
            # We don't need to check that fast because
            # the weather and time of day don't change quickly.
            time.sleep(1800)
        else:
            print("Entering operating state ...")
            (
                total_user_counted,
                total_bike_counted,
                total_dog_counted,
            ) = run_object_detection(
                state_change_event,
                total_user_counted,
                total_bike_counted,
                total_dog_counted,
            )
            # Add a 60-second wait to prevent crashes caused by
            # multiple rapid entries and exits into run_object_detection.
            time.sleep(60)


if __name__ == "__main__":
    dotenv_path = OPEN_WEATHER_API_PATH
    load_dotenv(dotenv_path=dotenv_path)
    OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")
    CITY_NAME = "kikrland"
    TIME_ZONE = "America/Los_Angeles"

    main_function_thread = threading.Thread(
        target=main, args=(OPEN_WEATHER_API_KEY, CITY_NAME, TIME_ZONE)
    )
    main_function_thread.start()
    time.sleep(70)
    run_led_screen()
    sys.exit()

    # Los Angeles, California, USA (Pacific Time Zone):
    # IANA Identifier: 'America/Los_Angeles'

    # New York, USA (Eastern Time Zone):
    # IANA Identifier: 'America/New_York'

    # London, United Kingdom (Greenwich Mean Time):
    # IANA Identifier: 'Europe/London'

    # Tokyo, Japan (Japan Standard Time):
    # IANA Identifier: 'Asia/Tokyo'

    # Taipei, Taiwan (Taipei Standard Time):
    # IANA Identifier: 'Asia/Taipei'
