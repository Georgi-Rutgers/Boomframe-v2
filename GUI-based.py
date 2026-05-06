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


"""
Note For Grader:
I used online help / teaching sites to help me make the GUI. Specifically, I used W3 schools information on TKinter for the GUI, and a combination of Stack overflow posts I have since lost (there was like 4 of them which i used bits and pieces of, but re-creating those searches on my process to document things has been unsucessful) on how to embed a matplotlib graph into a TKinter window.
I spoke with professor during office hours and was suggested to include this disclaimer for the grader.
"""


# Import necessary libraries
import tkinter as tk
from tkinter import ttk, messagebox
from requests import get
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Define the URL for the API endpoint
url = "https://api.warframe.market/v2/"

# For Professor: If you want to see documentation for API which I used, and get data yourself, the API is at this link:
# https://42bytes.notion.site/WFM-Api-v2-Documentation-5d987e4aa2f74b55a80db1a09932459d

"""
Simple GUI front-end: dropdown of item slugs and a button to plot
quantity-by-price-interval bar chart with statistics displayed.
"""

# Create Methods to fetch/extract data, compute stats, and plot in a window

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
	Uses data given to calculate statistics like mean, median, and standard deviation to transform data into more usable format.
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


def plot_stats_in_window(slug, stats, df_grouped):
	"""
	Using TKinter, creates a window to display/load the selected items stats and graph into a user friendly display format.

	Args:
		slug (String): The slug of the item which stats are for
		stats (dict): Dictionary containing all the calculated statistics
		df_grouped (Dataframe): Dataframe containing the quantity of items for each price interval, with outliers removed
	"""
	win = tk.Toplevel()
	win.title(f"{slug} — Quantity by Price Interval")
	# figure
	fig = plt.Figure(figsize=(8, 5))
	ax = fig.add_subplot(111)
	if df_grouped is None or df_grouped.empty:
		# Error catching for if there are no sell orders to display, or if all orders were filtered out as outliers
		ax.text(0.5, 0.5, "No sell orders to display", ha="center", va="center")
	else:
		# plot a bar chart of quantity vs price interval, using the grouped data
		x = df_grouped["price_interval"].astype(int).astype(str)
		y = df_grouped["quantity"]
		ax.bar(x, y, color="#2b8cbe") # I like this color blue :P
		ax.set_xlabel("Platinum (price interval)")
		ax.set_ylabel("Quantity")
		ax.set_title(f"Quantity by price interval for {slug}")

	# embed
	canvas = FigureCanvasTkAgg(fig, master=win)
	canvas.draw()
	canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

	# stats box on the right
	stats_frame = tk.Frame(win)
	stats_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=8, pady=8)
	stats_text = tk.Text(stats_frame, width=40, height=15)
	stats_text.pack(fill=tk.BOTH, expand=1)
	stats_text.insert(tk.END, f"Item: {slug}\n\n")
	if stats is None:
		stats_text.insert(tk.END, "No statistics available.\n")
	else:
		stats_text.insert(tk.END, f"Mean price: {stats['mean_price']:.2f}\n")
		stats_text.insert(tk.END, f"Median price: {stats['median_price']:.2f}\n")
		stats_text.insert(tk.END, f"Std dev (price): {stats['std_price']:.2f}\n\n")
		stats_text.insert(tk.END, "Lowest 25% stats:\n")
		stats_text.insert(tk.END, f"Mean: {stats['mean_price_lowest_25']:.2f}\n")
		stats_text.insert(tk.END, f"Median: {stats['median_price_lowest_25']:.2f}\n")
		stats_text.insert(tk.END, f"Std dev: {stats['std_price_lowest_25']:.2f}\n")

	stats_text.config(state=tk.DISABLED)


def build_gui():
	"""
	Create the input GUI to select which item to display stats for
	"""
	try:
		slugs = fetch_item_slugs()
	except Exception as e:
		messagebox.showerror("Error", f"Failed to fetch items: {e}")
		return

	root = tk.Tk()
	root.title("Warframe Market — Item Price Viewer")

	frame = tk.Frame(root, padx=12, pady=12)
	frame.pack(fill=tk.BOTH, expand=1)

	tk.Label(frame, text="Select item:").grid(row=0, column=0, sticky=tk.W)
	# build human-readable labels from slugs using a for-loop (replace underscores and title-case)
	display_labels = []
	slug_map = {}
	for s in slugs:
		label = s.replace("_", " ").title()
		display_labels.append(label)
		slug_map[label] = s

	combo = ttk.Combobox(frame, values=display_labels, width=60)
	combo.grid(row=0, column=1, padx=8, pady=4)
	if display_labels:
		combo.set(display_labels[0])

	# helper function for button to fetch data and plot when clicked
	def on_show():
		# map the human-readable label back to the slug (support pasting a slug directly)
		sel = combo.get().strip()
		slug = slug_map.get(sel, sel)
		if not slug:
			messagebox.showwarning("No selection", "Please select an item.")
			return
		btn.config(state=tk.DISABLED)
		try:
			# fetch orders, compute stats, and plot in a new window for the selected item
			df_sell = fetch_orders_for_slug(slug)
			stats, df_grouped = compute_stats_and_group(df_sell)
			plot_stats_in_window(slug, stats, df_grouped)
		except Exception as e:
			messagebox.showerror("Error", f"Failed to fetch/plot data: {e}")
		finally:
			# when stats window is closed, re-enable the button to allow another selection
			btn.config(state=tk.NORMAL)

	btn = tk.Button(frame, text="Show Graph", command=on_show)
	btn.grid(row=1, column=0, columnspan=2, pady=8)

	# run the GUI loop
	root.mainloop()


if __name__ == "__main__":
	# if this file is run directly, build the GUI to allow user interaction. Otherwise, if imported, the functions can be used programmatically without launching the GUI.
	build_gui()
