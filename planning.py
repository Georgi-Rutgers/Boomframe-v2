# Main App for OOP ETL final project
from requests import get
from pandas import DataFrame
import matplotlib.pyplot as plt

# Define the URL for the API endpoint
url = "https://api.warframe.market/v2/"

# Make a GET request to the API endpoint to get all possible items
response = get(url + "items")
# Check if the request was successful
if response.status_code == 200:
	# Parse the JSON response to get the list of items
	items = response.json()["data"]
	# Create a DataFrame from the list of items
	df_items = DataFrame(items)
	# list all columns in the DataFrame
	print(df_items.columns)
	# we are concerned with the slug
	# get first slug and get data for that item
	first_slug = df_items["slug"][0]
	# Make a GET request to the API endpoint to get order data for the first item
	response_item = get(url + f"orders/item/{first_slug}")
	# Check if the request was successful
	if response_item.status_code == 200:
		# parse the list of orders for the first item
		orders = response_item.json()["data"]
		# create a DataFrame from the list of orders
		df_orders = DataFrame(orders)
		# list all columns in the DataFrame
		print(df_orders.columns)
		# we are concerned with the type, quantity, and platinum
		# we also only want to show visible orders
		df_orders_visible = df_orders[df_orders["visible"] == True]
		# show the type, quantity, and platinum for the visible orders
		#print(df_orders_visible[["type", "quantity", "platinum"]])
		# ultimately, we want to show a graph of prices and quantities at those prices for sell orders of an item
		df_sell_orders = df_orders_visible[df_orders_visible["type"] == "sell"]
		# show the quantity and platinum for the sell orders
		#print(df_sell_orders[["quantity", "platinum"]])
		# we should now create a graph of the quantity and platinum for the sell orders
		# the graph should show a distribution of prices and quantities at those prices for sell orders of an item, but also remove outliers
		# we can use a boxplot to show the distribution of prices and quantities for the sell orders
		# plt.figure(figsize=(10, 6))
		# plt.boxplot(df_sell_orders["platinum"], vert=False)
		# plt.title(f"Distribution of Prices for {first_slug}")
		# plt.xlabel("Platinum")
		# plt.show()
		# we want to get some useful statistics about the sell orders, such as the mean, median, and standard deviation of the prices
		# we also want to get these stats for specifically the lowest 25% of the prices, which would be the most relevant for buyers, seperately from the overall stats to show how the lower end of the market is doing
		# print item name
		print(f"Item name: {first_slug}")
		# get the mean, median, and standard deviation of the prices for the sell orders
		mean_price = df_sell_orders["platinum"].mean()
		median_price = df_sell_orders["platinum"].median()
		std_price = df_sell_orders["platinum"].std()
		print(f"Mean price: {mean_price}")
		print(f"Median price: {median_price}")
		print(f"Standard deviation of price: {std_price}")
		# get the lowest 25% of the prices for the sell orders
		lowest_25_percent = df_sell_orders["platinum"].quantile(0.25)
		# get the mean, median, and standard deviation of the lowest 25%
		mean_price_lowest_25 = df_sell_orders[df_sell_orders["platinum"] <= lowest_25_percent]["platinum"].mean()
		median_price_lowest_25 = df_sell_orders[df_sell_orders["platinum"]<= lowest_25_percent]["platinum"].median()
		std_price_lowest_25 = df_sell_orders[df_sell_orders["platinum"] <= lowest_25_percent]["platinum"].std()
		print(f"Mean price for lowest 25%: {mean_price_lowest_25}")
		print(f"Median price for lowest 25%: {median_price_lowest_25}")
		print(f"Standard deviation of price for lowest 25%: {std_price_lowest_25}")

		# make a boxplot of prices grouped by 5 platinum intervals to show the distribution of prices for the sell orders, excluding any outliers above 3 standard deviations
		# remove extreme outliers in price, bucket prices into 5-platinum intervals
		df_sell_orders_no_outliers = df_sell_orders[df_sell_orders["platinum"] <= mean_price + 3 * std_price].copy()
		df_sell_orders_no_outliers["price_interval"] = (df_sell_orders_no_outliers["platinum"] // 5) * 5
		# remove outliers in quantity using the IQR rule to avoid skewing the chart
		q1 = df_sell_orders_no_outliers["quantity"].quantile(0.25)
		q3 = df_sell_orders_no_outliers["quantity"].quantile(0.75)
		iqr = q3 - q1
		lower_q = max(0, q1 - 1.5 * iqr)
		upper_q = q3 + 1.5 * iqr
		df_filtered = df_sell_orders_no_outliers[(df_sell_orders_no_outliers["quantity"] >= lower_q) & (df_sell_orders_no_outliers["quantity"] <= upper_q)].copy()
		# group the quantities for each price interval (use filtered data; fall back if filtering removes everything)
		df_grouped = df_filtered.groupby("price_interval", as_index=False).agg({"quantity": "sum"})
		if df_grouped.empty:
			df_grouped = df_sell_orders_no_outliers.groupby("price_interval", as_index=False).agg({"quantity": "sum"})
		# sort by price interval for consistent x-axis
		df_grouped = df_grouped.sort_values("price_interval")
		# plot a clean bar chart
		plt.figure(figsize=(10, 6))
		x_labels = df_grouped["price_interval"].astype(int).astype(str)
		plt.bar(x_labels, df_grouped["quantity"], color="#2b8cbe")
		plt.title(f"Quantity by Price Interval for {first_slug} (Outliers Excluded)")
		plt.xlabel("Platinum (price interval)")
		plt.ylabel("Quantity")
		plt.tight_layout()
		plt.show()


else:
	print(f"Failed to retrieve items. Status code: {response.status_code}")
	