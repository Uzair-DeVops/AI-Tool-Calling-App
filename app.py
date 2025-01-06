import shutil
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import streamlit as st  # type: ignore
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
st.title("Tool Calling with Gemini")
st.sidebar.title("Available Tools 10")
tools = [
    "get_time_in_timezone",
    "get_disk_usage",
    "get_weather",
    "search_image",
    "get_ip_address",
    "get_stock_price",
    "get_distance",
    "get_latest_news",
    "get_movie_details",
    "get_recipe"
]

tool_descriptions = {
    "get_time_in_timezone": "Returns the current time for a given timezone. Example: 'Asia/Karachi'.",
    "get_disk_usage": "Shows the current disk usage on your system.",
    "get_weather": "Fetches the current weather for a given location. Example: 'Karachi'.",
    "search_image": "Searches for images based on the query keyword. Example: 'Mountain'.",
    "get_ip_address": "Fetches the public IP address of the user.",
    "get_stock_price": "Shows the current stock price for a given stock symbol. Example: 'AAPL'.",
    "get_distance": "Calculates the distance between two locations. Example: 'Karachi' and 'Lahore'.",
    "get_latest_news": "Shows the latest news headlines.",
    "get_movie_details": "Fetches details of a movie based on its title. Example: 'Inception'.",
    "get_recipe": "Fetches a recipe for a given dish. Example: 'Chicken Biryani'."
}


# Display available tools and description in the sidebar
for tool_name in tools:
    st.sidebar.markdown(f"# {tool_name}")
    st.sidebar.markdown(tool_descriptions[tool_name])
    st.sidebar.markdown("---")


messages = []

# Prompt for user input
prompt = st.text_input("Enter your prompt")

# Variable to store the last country queried
last_country = None

# Define major cities for countries
country_cities = {
    "Pakistan": ["Karachi", "Lahore", "Islamabad", "Quetta", "Peshawar"],
    "USA": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"],
    "India": ["Mumbai", "Delhi", "Bangalore", "Kolkata", "Chennai"],
    # Add more countries and their major cities here
}


@tool(parse_docstring=True)
def get_disk_usage():
    """Retrieves disk usage.

    This function provides the disk usage statistics such as total, used, and free disk space.

    Args:
        None

    Returns:
        dict: A dictionary containing disk usage statistics with the following keys:
            - total (str): Total disk space in GB
            - used (str): Used disk space in GB
            - free (str): Free disk space in GB
    """
    path = "/"
    total, used, free = shutil.disk_usage(path)
    gb = 1024 * 1024 * 1024

    return {
        "total": f"{total / gb:.2f} GB",
        "used": f"{used / gb:.2f} GB",
        "free": f"{free / gb:.2f} GB"
    }


@tool(parse_docstring=True)
def get_time_in_timezone(timezone_name: str) -> str:
    """Returns the current time for a given timezone.

    This function fetches the current time for a specific timezone based on the provided IANA timezone name.

    Args:
        timezone_name (str): The IANA timezone name (e.g., 'America/New_York')

    Returns:
        str: Current time in the specified timezone (get_time_in_timezone tool is used )
    """
    try:
        current_time = datetime.now(ZoneInfo(timezone_name))
        return current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        return f"Error: Invalid timezone: {str(e)}"


@tool(parse_docstring=True)
def get_weather(location_name: str, is_city: bool = False) -> str:
    """Fetches the current weather for a given location (country or city). If a country is queried, includes weather for major cities.

    Args:
        location_name (str): The name of the location (country or city) for which to fetch the weather.
        is_city (bool, optional): Boolean indicating if the location is a city. Default is False.

    Returns:
        str: A description of the current weather, temperature, and other details.
    """
    try:
        global last_country
        api_key = "049048adef5f0ac4aa3012b93db79b78"  # Replace with your OpenWeatherMap API key

        # Fetch country weather
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location_name}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            weather = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            result = (
                f"The current weather in {location_name} is {weather} with a temperature "
                f"of {temp}°C and feels like {feels_like}°C.\n get_weather tool is used "
            )

            # Fetch major cities' weather if the location is a country
            if not is_city and location_name in country_cities:
                last_country = location_name
                result += "\nMajor cities' weather:\n"
                for city in country_cities[location_name]:
                    city_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
                    city_response = requests.get(city_url)
                    city_data = city_response.json()

                    if city_response.status_code == 200:
                        city_weather = city_data["weather"][0]["description"].capitalize()
                        city_temp = city_data["main"]["temp"]
                        city_feels_like = city_data["main"]["feels_like"]
                        result += (
                            f"- {city}: {city_weather}, {city_temp}°C (feels like {city_feels_like}°C)\n"
                        )
                    else:
                        result += f"- {city}: Weather data unavailable.\n"

            # Append tool usage info
            result += "\nTool used: get_weather"
            return result
        else:
            return f"Error: Could not retrieve weather data. Reason: {data.get('message', 'Unknown error')}."
    except Exception as e:
        return f"Error: Unable to fetch weather. Details: {str(e)}"


@tool(parse_docstring=True)
def search_image(query: str):
    """Searches for images based on the query keyword.

    Args:
        query (str): The search query to find images.

    Returns:
        str: Displays images related to the search query.
    """
    api_key = "YcKCA72Ez-w6bn0jC03opmr4UtdeXlRccoHpOs4WygU"
    url = f"https://api.unsplash.com/search/photos?query={query}&client_id={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if data['results']:
        # Extract the image URLs from the response
        image_urls = [image['urls']['small'] for image in data['results'][:5]]
        
        # Display images in the Streamlit app
        for img_url in image_urls:
            st.image(img_url, caption=f"Image related to {query}", use_container_width=True)
        
        return f"Tool used: search_image\n search_image tool is used to  Displayed images related to {query}."
    else:
        return f"Error: Could not find images for {query}.\nTool used: search_image"



@tool(parse_docstring=True)
def get_ip_address() -> str:
    """Fetches the user's public IP address.

    Args:
        None

    Returns:
        str: A message containing the user's public IP address.
    """
    try:
        ip = requests.get('https://api.ipify.org').text
        return f"get_ip_address tool is used to find Your public IP address is {ip}."
    except Exception as e:
        return f"Error: Unable to fetch IP address. Details: {str(e)}"




@tool(parse_docstring=True)
def get_stock_price(symbol: str) -> str:
    """Fetches the current stock price of a company based on its stock symbol using the Polygon API.

    Args:
        symbol (str): The stock symbol of the company (e.g., 'AAPL' for Apple, 'GOOGL' for Google).

    Returns:
        str: A message containing the current stock price of the company.

    Raises:
        HTTPError: If the HTTP request to the stock API fails (e.g., 404 or 500 status).
        RequestException: If there is an issue with the request itself (e.g., connection error).
        Exception: For any other unexpected errors during the execution of the function.

    """
    api_key =  "2bx0DyQuypHfwohF46294_29KpFtMKzt"  # Replace this with your actual secret API key from Polygon
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"  # Polygon endpoint for previous close price

    try:
        # Send a GET request with the API key
        response = requests.get(url, params={'apiKey': api_key})
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)

        # Assuming the data contains 'close' in the response for the last closing price
        data = response.json()
        price = data.get('results', [{}])[0].get('c')  # 'c' is the closing price

        if price:
            return f"Tool used: get_stock_price\n get_stock_price tool is used to find The current price of {symbol} is ${price}"
        else:
            return f"Error: Could not retrieve stock data for {symbol}.\nTool used: get_stock_price"

    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}\nTool used: get_stock_price"
    except requests.exceptions.RequestException as req_err:
        return f"Request error occurred: {req_err}\nTool used: get_stock_price"
    except Exception as err:
        return f"An unexpected error occurred: {err}\nTool used: get_stock_price"
import requests

@tool(parse_docstring=True)
def get_distance(location1: str, location2: str) -> str:
    """
    Calculates the distance between two locations using the OpenCage Geocoder API.

    This function uses the OpenCage Geocoder API to get the geographic coordinates (latitude and longitude) 
    of the provided locations, then computes the distance between the two points using the Haversine formula.

    Args:
        location1 (str): The first location (e.g., "New York").
        location2 (str): The second location (e.g., "Los Angeles").

    Returns:
        str: A message containing the calculated distance in kilometers between the two locations.

    Raises:
        Exception: If either location is invalid or the API requests fail.
    """
    
    api_key = "52420d959f5749cfbd67a5258d590195"  # Replace with your OpenCage API key
    
    # Geocode the origin location
    url1 = f"https://api.opencagedata.com/geocode/v1/json?q={location1}&key={api_key}"
    response1 = requests.get(url1)
    
    # Geocode the destination location
    url2 = f"https://api.opencagedata.com/geocode/v1/json?q={location2}&key={api_key}"
    response2 = requests.get(url2)
    
    # Check if both responses are successful
    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()

        # Extract latitude and longitude for both locations
        lat1, lon1 = data1['results'][0]['geometry']['lat'], data1['results'][0]['geometry']['lng']
        lat2, lon2 = data2['results'][0]['geometry']['lat'], data2['results'][0]['geometry']['lng']

        # Calculate the distance using the Haversine formula
        from math import radians, sin, cos, sqrt, atan2
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        # Radius of the Earth in kilometers
        radius = 6371.0
        
        # Calculate the distance
        distance = radius * c
        
        return f"Tool used: get_distance\n get_distance tool is used to find The distance between {location1} and {location2} is {distance:.2f} km."
    
    else:
        return f"Error: Could not calculate the distance. Check if both locations are valid.\nTool used: get_distance"

@tool(parse_docstring=True)
def get_latest_news(topic: str) -> str:
    """
    Fetches the latest news for a given topic.

    Args:
        topic (str): The topic to search for news articles.

    Returns:
        str: A formatted string containing the tool name, the latest news titles, and their respective links.

    Example:
        get_latest_news("Technology")
    """
    api_key = "e9c6d47717ab4738b733f4a8e15f9375"  # Replace with your actual API key
    url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={api_key}"

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data.get('articles'):
            articles = data['articles']
            result = f"Tool used: get_latest_news\n get_latest_news tool is used \nHere are the latest news articles related to {topic}:\n"

            for article in articles[:10]:  # Limiting to 5 articles
                title = article['title']
                url = article['url']
                result += f"- {title}: {url}\n"

            return result
        else:
            return f"Error: Could not fetch news for {topic}. Reason: {data.get('message', 'Unknown error')}"
    except Exception as e:
        return f"Error: Unable to fetch news. Details: {str(e)}"

@tool(parse_docstring=True)
def get_movie_details(movie_name: str) -> str:
    """
    Fetches detailed information about a movie using its name.

    Args:
        movie_name (str): The name of the movie.

    Returns:
        str: A detailed summary of the movie, including title, year, genre, director, plot, and rating.

    Raises:
        Exception: If the movie is not found or the API request fails.
    """
    import requests

    api_key = "31f29fd0"  # Replace with your OMDB API key
    url = f"http://www.omdbapi.com/?t={movie_name}&apikey={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("Response") == "True":
            title = data.get("Title", "N/A")
            year = data.get("Year", "N/A")
            genre = data.get("Genre", "N/A")
            director = data.get("Director", "N/A")
            plot = data.get("Plot", "N/A")
            imdb_rating = data.get("imdbRating", "N/A")

            return (
                f"Tool used: get_movie_details\n"
                f"Movie Details:\n"
                f"- Title: {title}\n"
                f"- Year: {year}\n"
                f"- Genre: {genre}\n"
                f"- Director: {director}\n"
                f"- Plot: {plot}\n"
                f"- IMDb Rating: {imdb_rating}/10"
            )
        else:
            return f"Tool used: get_movie_details\nMovie not found: {movie_name}"
    except Exception as e:
        return f"Tool used: get_movie_details\nError fetching movie details: {str(e)}"

import requests

@tool(parse_docstring=True)
def get_recipe(dish_name: str) -> str:
    """Fetches a recipe for a given dish name using the Spoonacular API.

    Args:
        dish_name (str): The name of the dish for which the recipe is to be fetched.

    Returns:
        str: The recipe with ingredients and instructions.
    """
    try:
        api_key = '716e3a77f3e841669be0a6974ff05b9b'  # Replace with your Spoonacular API key
        url = f"https://api.spoonacular.com/recipes/complexSearch?query={dish_name}&apiKey={api_key}&number=1"
        response = requests.get(url)
        data = response.json()

        if data.get('results'):
            recipe_id = data['results'][0]['id']
            recipe_title = data['results'][0]['title']
            
            # Fetch detailed recipe information
            details_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={api_key}"
            details_response = requests.get(details_url)
            details_data = details_response.json()
            
            ingredients = details_data.get('extendedIngredients', [])
            instructions = details_data.get('instructions', 'No instructions available.')

            # Create the recipe text
            recipe_text = f"Recipe for {recipe_title}:\n\nIngredients:\n"
            for ingredient in ingredients:
                recipe_text += f"- {ingredient['original']}\n"
            
            recipe_text += f"\nInstructions:\n{instructions}"
            
            return f"Tool used: get_recipe\n{recipe_text}"
        else:
            return f"Error: Could not find a recipe for {dish_name}. Try another dish name."
    except Exception as e:
        return f"Error: Unable to fetch recipe. Details: {str(e)}"


tools_list = {
    "get_time_in_timezone": get_time_in_timezone,
    "get_disk_usage": get_disk_usage,
    "get_weather": get_weather,
    "search_image": search_image,
    "get_ip_address": get_ip_address,
    "get_stock_price": get_stock_price,
    "get_distance": get_distance,
    "get_latest_news": get_latest_news,
    "get_movie_details": get_movie_details,
    "get_recipe": get_recipe
}

if prompt:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp", temperature=0.3, api_key="AIzaSyDlGuiJOqQePVsQEu5gWiftb74RDGvcq-c"
    )
    llm_with_tools = llm.bind_tools(list(tools_list.values()))

    messages.append(HumanMessage(prompt))
    ai_response = llm_with_tools.invoke(messages)
    messages.append(ai_response)

    if not ai_response.tool_calls:
        with st.container(height=500, border=True):
            st.write(ai_response.content)
            # Check if the response contains the stop condition
            if "stop" in ai_response.content.lower():  # Example stop condition
                st.write("Execution stopped as requested.")
                sys.exit()  # Exit the program if stop condition is met

    for tool_call in ai_response.tool_calls:
        selected_tool = tools_list.get(tool_call["name"].lower())
        tool_response = selected_tool.invoke(tool_call["args"])

        messages.append(ToolMessage(tool_response, tool_call_id=tool_call["id"]))

        # Check for stop condition in tool responses
        if "stop" in tool_response.lower():  # Example stop condition in tool response
            st.write("Execution stopped as requested.")
            sys.exit()  # Exit the program if stop condition is met

    final_response = llm_with_tools.stream(messages)
    with st.container(height=500, border=True):
        st.write_stream(final_response)
