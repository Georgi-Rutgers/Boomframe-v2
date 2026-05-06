# Main App for OOP ETL final project
# Author: Georgi Petrov
# This app fetches item data from the Warframe Market API, allows the user to select an item, and then displays a graph of quantity by price interval for sell orders of that item, along with statistics about the prices.

# Project Requirements:
"""
Purpose: Conduct a Data ETL project and document the process on Word. On Canvas, submit a Python file called "final.py" that contains a  completed Data ETL (Extract, Transform, Load) project. Your project should successfully extract data (from either a file containing data or the web using an API or) you think is interesting. Your project should look into this data to uncover some meaningful findings in it and (up)load these findings into a text, CSV, website, or image format.

Code Checklist: The following checklist should be used to ensure all necessary components of the assignment are in place for a 20/20 on the code:

The code runs and there are no errors or exceptions
The code has several comments that document the ETL process
The code has a comment that links the API or dataset used for the analysis
The code explores at least one dataset or API
The code utilizes at least one module or package
The code contains at least one conditional statement
The code contains at least one loop
The code contains at least one data structure (tuple, list, set, dictionary, Pandas dataframe)
Report Checklist: The following checklist should be used to ensure all necessary components of the paper are in place for a 10/10 on the report:

The report describes each step of the ETL process in a 1-2 page Word document
The report discusses the data that is analyzed in the project 
The report discusses what the student looked into for their project
The report discusses how the student extracted meaningful insight from their original data
The report discusses any struggles encountered when working with web data or files
Sources: Consider the following resources when selecting a dataset for your project. If you would like to use an alternate resource, please feel free."""

# Define the URL for the API endpoint
url = "https://api.warframe.market/v2/"

# For Professor: If you want to see documentation for API which I used, and get data yourself, the API is at this link:
# https://42bytes.notion.site/WFM-Api-v2-Documentation-5d987e4aa2f74b55a80db1a09932459d

from requests import get
from pandas import DataFrame
import matplotlib.pyplot as plt


def fetch_item_slugs():
	"""
	Fetches a list of all items which the Market API stores order info for

	Returns:
		list: all items sold on the Warframe Market, as a list of slugs (string identifiers) 
	"""
	resp = get(url + "items")
	resp.raise_for_status()
	items = resp.json()["data"]
	df_items = DataFrame(items)
	return df_items["slug"].tolist()

def fetch_orders_for_slug(slug):
	"""
	Fetches a list of all visible sell orders for a given item slug

	Args:
		slug (string): The slug of the item for which to fetch sell orders

	Returns:
		DataFrame: A DataFrame containing the visible sell orders for the specified item
	"""
	resp = get(url + f"orders/item/{slug}")
	resp.raise_for_status()
	orders = resp.json()["data"]
	df_orders = DataFrame(orders)
	# only visible orders
	df_orders_visible = df_orders[df_orders["visible"] == True]
	# only sell orders
	df_sell = df_orders_visible[df_orders_visible["type"] == "sell"].copy()
	return df_sell

def compute_stats_and_group(df_sell):
	"""
	Uses data given to calculate statistics like mean, median, and standard deviation
	Also groups orders into intervals of 5 platinum while combining quanitites of orders, and removes outliers in both cost and quantity

	Args:
		df_sell (Dataframe): Pandas Dataframe of visible sell orders from API

	Returns:
		stats (dict): A dictionary containing the calculated statistics
		df_grouped (DataFrame): A DataFrame containing the quantity of items for each price interval, with outliers removed
	"""
	if df_sell.empty:
		return None, None
	# price stats
	mean_price = df_sell["platinum"].mean()
	median_price = df_sell["platinum"].median()
	std_price = df_sell["platinum"].std()
	lowest_25_percent = df_sell["platinum"].quantile(0.25)
	mean_price_lowest_25 = df_sell[df_sell["platinum"] <= lowest_25_percent]["platinum"].mean()
	median_price_lowest_25 = df_sell[df_sell["platinum"] <= lowest_25_percent]["platinum"].median()
	std_price_lowest_25 = df_sell[df_sell["platinum"] <= lowest_25_percent]["platinum"].std()

	stats = {
		"mean_price": mean_price,
		"median_price": median_price,
		"std_price": std_price,
		"mean_price_lowest_25": mean_price_lowest_25,
		"median_price_lowest_25": median_price_lowest_25,
		"std_price_lowest_25": std_price_lowest_25,
	}

	# remove extreme price outliers
	df_price_filtered = df_sell[df_sell["platinum"] <= mean_price + 3 * std_price].copy()
	df_price_filtered["price_interval"] = (df_price_filtered["platinum"] // 5) * 5

	# remove only upper quantity outliers using IQR (keep low quantities)
	q1 = df_price_filtered["quantity"].quantile(0.25)
	q3 = df_price_filtered["quantity"].quantile(0.75)
	iqr = q3 - q1
	upper_q = q3 + 1.5 * iqr
	df_filtered = df_price_filtered[df_price_filtered["quantity"] <= upper_q].copy()

	df_grouped = df_filtered.groupby("price_interval", as_index=False).agg({"quantity": "sum"})
	if df_grouped.empty:
		df_grouped = df_price_filtered.groupby("price_interval", as_index=False).agg({"quantity": "sum"})

	df_grouped = df_grouped.sort_values("price_interval")
	return stats, df_grouped


# fetch all item slugs from the API
slugs = fetch_item_slugs()
# ask user to select an item by slug
print("Available items:")
for i, slug in enumerate(slugs):
	print(f"{i + 1}. {slug}")
selection = int(input("Select an item by number: "))
selected_slug = slugs[selection - 1]
print(f"You selected: {selected_slug}")

# fetch sell orders for the selected item
df_sell = fetch_orders_for_slug(selected_slug)

# compute statistics and group data for graphing
stats, df_grouped = compute_stats_and_group(df_sell)

if stats is not None:
	print(f"Statistics for {selected_slug}:")
	for key, value in stats.items():
		print(f"{key}: {value}")
else:
	print(f"No sell orders found for {selected_slug}.")

if df_grouped is not None:
	print(f"Grouped data for {selected_slug}:")
	print(df_grouped)
else:
	print(f"No data available to group for {selected_slug}.")

# If grouped data exists, plot a simple bar chart using matplotlib
if df_grouped is not None and not df_grouped.empty:
	# convert interval to string labels for plotting
	x = df_grouped["price_interval"].astype(int).astype(str)
	y = df_grouped["quantity"]
	plt.figure(figsize=(10, 6))
	plt.bar(x, y, color="#2b8cbe")
	plt.xlabel("Platinum (price interval)")
	plt.ylabel("Quantity")
	plt.title(f"Quantity by price interval for {selected_slug}")
	plt.tight_layout()
	plt.show()
